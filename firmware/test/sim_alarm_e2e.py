#!/usr/bin/env python3
"""End-to-end alarm tests against the PC simulator (the real firmware, simulated hardware).

    cd firmware/sim && make all && cd .. && python3 test/sim_alarm_e2e.py [scenario ...]

Every scenario tries a way an alarm could fail to go off and checks that it rings anyway. The simulator is
started fresh for each one (its own storage folder); a crash or restart is simulated by the process exiting,
after which the harness starts it again "warm" (SIM_RESET=warm), as the ESP32 does after a reset.
"""
import json, os, shutil, subprocess, sys, tempfile, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
SIM = os.environ.get('CC_SIM') or os.path.join(HERE, '..', 'sim', 'build', 'ceilingclock-sim')   # CC_SIM: test another build
PORT = 8130


class Clock:
    def __init__(self, env=None, fs=None):
        self.fs = fs or tempfile.mkdtemp(prefix='cc-e2e-')
        self.env = dict(env or {})
        self.proc = None
        self.log = open(os.path.join(self.fs, '..', os.path.basename(self.fs) + '.log'), 'a')

    def pass_time_while_off(self, sec):
        """Time passes while the clock is off (the simulated world's time is kept in .worldtime)."""
        p = os.path.join(self.fs, '.worldtime')
        off = int(open(p).read().strip() or 0) if os.path.exists(p) else 0
        open(p, 'w').write(f'{off + int(sec)}\n')

    def start(self, warm=False, wait_s=10, **extra):
        env = dict(os.environ, SIM_FS_DIR=self.fs, SIM_PORT=str(PORT), **self.env, **extra)
        if warm:
            env['SIM_RESET'] = 'warm'
        else:
            env.pop('SIM_RESET', None)
        self.proc = subprocess.Popen([SIM], env=env, stdout=self.log, stderr=subprocess.STDOUT)
        for _ in range(int(wait_s * 10)):
            try:
                self.get('/sim/clock'); return self
            except Exception:
                if self.proc.poll() is not None: raise RuntimeError('simulator exited at start')
                time.sleep(0.1)
        raise RuntimeError('simulator did not answer')

    def stop(self):
        if self.proc and self.proc.poll() is None:
            self.proc.kill(); self.proc.wait()

    def power_cut(self):
        """Power off: the reset-surviving memory is lost too."""
        self.stop()
        p = os.path.join(self.fs, '.rtcmem')
        if os.path.exists(p): os.remove(p)

    def crashed(self):
        return self.proc.poll() is not None

    def get(self, path):
        return json.loads(urllib.request.urlopen(f'http://localhost:{PORT}{path}', timeout=5).read() or b'null')

    def post(self, path, body=None):
        data = json.dumps(body).encode() if body is not None else b''
        req = urllib.request.Request(f'http://localhost:{PORT}{path}', data=data, method='POST',
                                     headers={'Content-Type': 'application/json'})
        r = urllib.request.urlopen(req, timeout=5).read()
        try: return json.loads(r)
        except Exception: return r

    def state(self): return self.get('/api/state')
    def hw(self): return self.get('/sim/hw')
    def clock(self): return self.get('/sim/clock')

    def config(self): return self.get('/api/config')

    def set_alarms(self, alarms, **extra):
        c = self.config()
        c['tz'] = 'UTC0'
        c['alarms'] = alarms
        c.update(extra)
        return self.post('/api/config', c)

    def advance(self, sec):
        """Move the real world's time forward (the clock's own time follows, like a running clock)."""
        self.post(f'/sim/time?add={int(sec)}')

    def wait(self, cond, timeout, what):
        end = time.time() + timeout
        last = None
        while time.time() < end:
            try:
                last = cond()
                if last: return last
            except Exception as e:
                last = e
            time.sleep(0.2)
        raise AssertionError(f'timed out waiting for: {what} (last: {last})')


def alarm(at_epoch, **kw):
    t = time.gmtime(at_epoch)
    a = dict(enabled=True, hour=t.tm_hour, minute=t.tm_min, days=127, skipNext=False, label='Test',
             sound='/sounds/beep.wav', stream='', volume=12, rampSec=0, snoozeMin=1, maxRingMin=30)
    a.update(kw)
    return a


def next_minute(c, ahead=60):
    """An alarm time at least `ahead` seconds after the clock's own time, on a minute boundary."""
    now = c.state()['now']
    return (now + ahead) // 60 * 60 + 60


def ringing(c):
    s = c.state()
    return s['ring'] == 'ringing' and s


def ring_and_check(c, at, what, timeout=10):
    c.advance(at - c.state()['now'] + 2)
    c.wait(lambda: ringing(c), timeout, what)
    c.wait(lambda: c.hw()['audio']['playing'], 5, what + ': sound playing')


# ------------------------------------------------------------------------------------------------ scenarios
def s_basic(c):
    """An alarm rings at its time and plays its sound."""
    c.start()
    at = next_minute(c)
    c.set_alarms([alarm(at)])
    ring_and_check(c, at, 'alarm rings')
    assert c.hw()['audio']['file'] == '/sounds/beep.wav'


def s_moved_same_day(c):
    """Rang at its time, stopped, then moved later the same day: rings again (old 23-hour guard)."""
    c.start()
    at = next_minute(c)
    c.set_alarms([alarm(at)])
    ring_and_check(c, at, 'first ring')
    c.post('/api/action?do=dismiss')
    c.wait(lambda: c.state()['ring'] == 'idle', 5, 'stopped')
    at2 = next_minute(c, 120)
    c.set_alarms([alarm(at2)])
    ring_and_check(c, at2, 'rings again after being moved later the same day')


def s_clock_jump(c):
    """The clock runs 20 minutes slow (backup clock drift); the time sync jumps it forward over the alarm."""
    c.start()
    c.set_alarms([])                    # time zone first: changing it makes the clock resync
    c.post('/sim/clockerror?sec=-1200')
    at = next_minute(c, 120)            # 2 minutes ahead of the slow clock = in the real past after the sync
    c.set_alarms([alarm(at)])
    time.sleep(1.5)
    assert c.state()['ring'] == 'idle'
    c.post('/sim/ntp')                  # the sync corrects the clock by +20 minutes
    c.wait(lambda: ringing(c), 10, 'rings after the clock jumped forward over it')


def s_save_while_ringing(c):
    """Saving settings (even deleting the ringing alarm) doesn't silence it; nor does it cancel a snooze."""
    c.start()
    at = next_minute(c)
    c.set_alarms([alarm(at, snoozeMin=1)])
    ring_and_check(c, at, 'rings')
    c.set_alarms([])                    # delete every alarm while it rings
    time.sleep(1.5)
    assert ringing(c), 'still ringing after saving settings'
    c.post('/api/action?do=snooze')
    c.wait(lambda: c.state()['ring'] == 'snoozed', 5, 'snoozed')
    c.set_alarms([alarm(at + 7200)])    # save again while snoozed
    time.sleep(1)
    assert c.state()['ring'] == 'snoozed', 'snooze kept after saving'
    c.advance(65)
    c.wait(lambda: ringing(c), 10, 'rings again after the snooze')


def s_crash_while_ringing(c):
    """The clock crashes or is reset while ringing: it comes back ringing."""
    c.start()
    at = next_minute(c)
    c.set_alarms([alarm(at)])
    ring_and_check(c, at, 'rings')
    try: c.post('/sim/crash')
    except Exception: pass
    c.wait(c.crashed, 5, 'simulated crash')
    c.start(warm=True)
    c.wait(lambda: ringing(c), 10, 'rings again after the reset')


def s_crash_while_snoozed(c):
    """Reset while snoozed: the snooze carries on and it rings at the end."""
    c.start()
    at = next_minute(c)
    c.set_alarms([alarm(at, snoozeMin=2)])
    ring_and_check(c, at, 'rings')
    c.post('/api/action?do=snooze')
    c.wait(lambda: c.state()['ring'] == 'snoozed', 5, 'snoozed')
    try: c.post('/sim/crash')
    except Exception: pass
    c.wait(c.crashed, 5, 'simulated crash')
    c.start(warm=True)
    assert c.state()['ring'] == 'snoozed', 'still snoozed after the reset'
    c.advance(125)
    c.wait(lambda: ringing(c), 10, 'rings when the snooze ends')


def s_reset_no_rtc_no_internet(c):
    """No backup clock and the internet is down: a reset keeps the time (RTC memory), so the alarm rings."""
    c.start()
    at = next_minute(c, 120)
    c.set_alarms([alarm(at)])
    c.post('/sim/net?ok=0')
    try: c.post('/sim/crash')
    except Exception: pass
    c.wait(c.crashed, 5, 'simulated crash')
    c.start(warm=True, SIM_NET='0')
    assert c.state()['timeValid'], 'time carried over the reset'
    ring_and_check(c, at, 'rings with no internet and no backup clock after a reset')


def s_power_back_late_rtc(c):
    """Power cut over the alarm time; with the backup clock it rings when power returns (within 15 min)."""
    c.env['SIM_RTC'] = '1'
    c.start()
    at = next_minute(c, 120)
    c.set_alarms([alarm(at)])
    now = c.state()['now']
    c.power_cut()
    c.pass_time_while_off(at - now + 600)    # power comes back 10 minutes after the alarm time
    c.start(SIM_NET='0')                      # no internet: the time comes from the backup clock
    c.wait(lambda: ringing(c), 10, 'rings when power returns 10 minutes late')


def s_router_late(c):
    """After a power cut the router starts after the clock: the setup portal closes and the clock rejoins."""
    c.start()
    at = next_minute(c, 180)
    c.set_alarms([alarm(at)])
    c.power_cut()
    # the router is down when the clock starts and comes up 8 s later; the clock's web page (and so these
    # test controls) only answers once it has joined, so starting at all proves it rejoined by itself
    c.start(SIM_WIFI='0', SIM_WIFI_UP_AFTER='8', SIM_FAST_PORTAL='1', wait_s=60)
    log = open(c.log.name).read()
    assert 'setup portal' in log, 'the setup portal opened while the router was down'
    c.wait(lambda: c.state()['timeValid'], 10, 'time synced')
    ring_and_check(c, at, 'rings after the router came up late')


def s_damaged_sound(c):
    """The alarm's sound file won't play: the built-in beep rings instead."""
    c.start()
    at = next_minute(c)
    shutil.copy(os.path.join(c.fs, 'sounds', 'beep.wav'), os.path.join(c.fs, 'sounds', 'song.mp3'))
    c.post('/sim/audiofail?path=/sounds/song.mp3&mode=fail')
    c.set_alarms([alarm(at, sound='/sounds/song.mp3')])
    c.advance(at - c.state()['now'] + 2)
    c.wait(lambda: ringing(c), 10, 'rings')
    c.wait(lambda: c.hw()['audio']['file'] == '/sounds/beep.wav' and c.hw()['audio']['playing'], 20, 'beep takes over')


def s_stalled_sound(c):
    """The sound opens but nothing comes out (stalled decoder): the beep takes over."""
    c.start()
    shutil.copy(os.path.join(c.fs, 'sounds', 'beep.wav'), os.path.join(c.fs, 'sounds', 'quiet.wav'))
    c.post('/sim/audiofail?path=/sounds/quiet.wav&mode=stall')
    at = next_minute(c)
    c.set_alarms([alarm(at, sound='/sounds/quiet.wav')])
    c.advance(at - c.state()['now'] + 2)
    c.wait(lambda: ringing(c), 10, 'rings')
    c.wait(lambda: c.hw()['audio']['file'] == '/sounds/beep.wav' and c.hw()['audio']['playing'], 20,
           'beep takes over from a stalled sound')


def s_stream_fails_then_backup_fails(c):
    """A stream that stalls falls back to its backup sound; a broken backup falls back to the beep."""
    c.start()
    at = next_minute(c)
    shutil.copy(os.path.join(c.fs, 'sounds', 'beep.wav'), os.path.join(c.fs, 'sounds', 'backup.wav'))
    c.post('/sim/audiofail?path=stream&mode=stall')
    c.post('/sim/audiofail?path=/sounds/backup.wav&mode=fail')
    c.set_alarms([alarm(at, stream='http://radio.example/live.mp3', sound='/sounds/backup.wav')])
    c.advance(at - c.state()['now'] + 2)
    c.wait(lambda: ringing(c), 10, 'rings')
    c.wait(lambda: c.hw()['audio']['url'], 5, 'stream started')
    c.wait(lambda: c.hw()['audio']['file'] == '/sounds/beep.wav' and c.hw()['audio']['playing'], 45,
           'stream -> backup -> beep')


def s_audio_hang(c):
    """The audio task freezes: the clock restarts itself and carries on ringing with the beep."""
    c.start()
    at = next_minute(c)
    shutil.copy(os.path.join(c.fs, 'sounds', 'beep.wav'), os.path.join(c.fs, 'sounds', 'hang.wav'))
    c.post('/sim/audiofail?path=/sounds/hang.wav&mode=hang')
    c.set_alarms([alarm(at, sound='/sounds/hang.wav')])
    c.advance(at - c.state()['now'] + 2)
    c.wait(c.crashed, 45, 'the clock restarts itself (audio stuck)')
    c.start(warm=True)
    c.wait(lambda: ringing(c), 10, 'rings after the restart')
    c.wait(lambda: c.hw()['audio']['file'] == '/sounds/beep.wav' and c.hw()['audio']['playing'], 10, 'with the beep')


def s_volume_floor(c):
    """An alarm set to volume 0 still rings audibly; a long fade-in finishes within a short ring time."""
    c.start()
    at = next_minute(c)
    c.set_alarms([alarm(at, volume=0)])
    ring_and_check(c, at, 'rings')
    c.wait(lambda: c.hw()['audio']['vol'] >= 6, 5, 'volume at least 6 of 21')
    c.post('/api/action?do=dismiss')
    at2 = next_minute(c, 120)
    c.set_alarms([alarm(at2, volume=21, rampSec=600, maxRingMin=5)])
    ring_and_check(c, at2, 'rings')
    c.advance(101)                      # fade-in is capped at a third of the 5-minute ring time
    c.wait(lambda: c.hw()['audio']['vol'] == 21, 5, 'full volume within 100 s')


def s_settings_damaged(c):
    """The settings file is damaged (power cut mid-save): the alarms come back from the backup copy."""
    c.start()
    at = next_minute(c, 180)
    c.set_alarms([alarm(at)])
    c.set_alarms([alarm(at)])           # a second save leaves a backup copy
    c.power_cut()
    with open(os.path.join(c.fs, 'config.json'), 'w') as f: f.write('{"alarms":[{"enab')
    c.start()
    assert len(c.config()['alarms']) == 1, 'alarms recovered'
    ring_and_check(c, at, 'rings with recovered settings')
    # only the half-renamed new file left
    c.power_cut()
    os.replace(os.path.join(c.fs, 'config.json'), os.path.join(c.fs, 'config.tmp'))
    for n in ('config.bak',):
        p = os.path.join(c.fs, n)
        if os.path.exists(p): os.remove(p)
    c.start()
    assert len(c.config()['alarms']) == 1, 'alarms recovered from config.tmp'


def s_two_alarms_same_time(c):
    """Two alarms at the same minute: at least one rings (they share the speaker)."""
    c.start()
    at = next_minute(c)
    c.set_alarms([alarm(at, label='A'), alarm(at, label='B')])
    ring_and_check(c, at, 'rings')



# ---- daylight saving, with the ESP32's own date library (newlib) linked into the simulator
CST = 'CST6CDT,M3.2.0,M11.1.0'


def utc(y, mo, d, h, mi, s=0):
    import calendar
    return calendar.timegm((y, mo, d, h, mi, s))


def set_world_time(c, t):
    c.post(f'/sim/time?set={int(t)}')
    c.wait(lambda: abs(c.state()['now'] - t) < 5, 5, 'clock follows the new time')


def rings_at(c, t, wait=5):
    """Move to 2 s after t; True if the alarm rings (then stops it)."""
    c.advance(t + 2 - c.state()['now'])
    try:
        c.wait(lambda: ringing(c), wait, 'ring')
    except AssertionError:
        return False
    c.post('/api/action?do=dismiss')
    c.wait(lambda: c.state()['ring'] == 'idle', 5, 'stopped')
    return True


def s_dst_skipped_hour(c):
    """An alarm at 2:30 on the night 2:00-3:00 is skipped (clocks go forward) rings once, at 3:30, then normally."""
    c.start()
    c.set_alarms([alarm(0, hour=2, minute=30)], tz=CST)
    set_world_time(c, utc(2027, 3, 14, 7, 50))           # 1:50 CST, ten minutes before the change
    assert not rings_at(c, utc(2027, 3, 14, 8, 0), 2), 'no ring at 3:00 CDT'
    assert not rings_at(c, utc(2027, 3, 14, 8, 29), 2), 'no ring before 3:30 CDT'
    assert rings_at(c, utc(2027, 3, 14, 8, 30)), 'rings at 3:30 CDT (2:30 does not exist that night)'
    assert not rings_at(c, utc(2027, 3, 14, 9, 30), 2), 'only once that night'
    assert rings_at(c, utc(2027, 3, 15, 7, 30)), 'next night at 2:30 CDT as usual'


def s_dst_repeated_hour(c):
    """An alarm at 1:30 on the night 1:00-2:00 happens twice (clocks go back) rings exactly once, then normally."""
    c.start()
    c.set_alarms([alarm(0, hour=1, minute=30)], tz=CST)
    set_world_time(c, utc(2027, 11, 7, 5, 50))           # 0:50 CDT
    first = rings_at(c, utc(2027, 11, 7, 6, 30))          # 1:30 CDT
    second = rings_at(c, utc(2027, 11, 7, 7, 30))         # 1:30 CST, an hour later
    assert first + second == 1, f'rang {first + second} times in the repeated hour'
    assert not rings_at(c, utc(2027, 11, 7, 8, 30), 2), 'not again after it'
    assert rings_at(c, utc(2027, 11, 8, 7, 30)), 'next night at 1:30 CST as usual'
    c.which = 'the second 1:30 (standard time)' if second else 'the first 1:30 (daylight time)'


def s_loop_hang(c):
    """The main loop freezes while ringing: the task watchdog resets the clock, and it carries on ringing."""
    c.start()
    at = next_minute(c)
    c.set_alarms([alarm(at)])
    ring_and_check(c, at, 'alarm rings')
    try: c.post('/sim/hang')
    except Exception: pass
    t0 = time.time()
    c.wait(c.crashed, 45, 'the task watchdog resets the clock')
    assert time.time() - t0 > 25, 'not before the 30-second watchdog time'
    c.start(warm=True)
    assert c.state()['lastStart'] == 'reset', 'started after a reset, not a power-on'
    c.wait(lambda: ringing(c), 10, 'rings after the reset')


SCENARIOS = {n[2:]: f for n, f in globals().items() if n.startswith('s_')}

if __name__ == '__main__':
    names = sys.argv[1:] or list(SCENARIOS)
    failed = []
    for n in names:
        c = Clock()
        t0 = time.time()
        try:
            SCENARIOS[n](c)
            print(f'PASS {n:34} {time.time() - t0:5.1f}s  {SCENARIOS[n].__doc__.strip().splitlines()[0]}'
                  + (f' [{c.which}]' if getattr(c, 'which', None) else ''))
        except Exception as e:
            failed.append(n)
            print(f'FAIL {n:34} {time.time() - t0:5.1f}s  {e}')
        finally:
            c.stop()
    print(f'\n{len(names) - len(failed)} of {len(names)} passed' + (f'; failed: {", ".join(failed)}' if failed else ''))
    sys.exit(1 if failed else 0)
