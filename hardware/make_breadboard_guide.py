# Usage: python3 hardware/make_breadboard_guide.py
# Writes docs/breadboard.html: an illustrated, step-by-step breadboard test for beginners.
# Every picture is drawn here from firmware/src/pins.h and the ESP32-S3-DevKitC-1 header order,
# so the wires in the pictures go to the right physical pins.
#
# Bench layout: the ESP32 sits BESIDE the breadboard (it is too wide to leave free holes on a standard
# breadboard) and connects with female jumper leads. The breadboard carries the power rails, the
# buttons, the light sensor and the resistors. Top rails: 3V3 + GND from the ESP32. Bottom rails:
# external 5 V + GND. The two GND rails are joined.
import os, re, html

HERE = os.path.dirname(os.path.abspath(__file__))
PINS = dict(re.findall(r'#define (PIN_\w+)\s+(\d+)', open(os.path.join(HERE, '..', 'firmware', 'src', 'pins.h')).read()))
G = lambda k: int(PINS[k])

# ESP32-S3-DevKitC-1 headers (Espressif user guide). Pin 1 is at the antenna end.
J1 = ['3V3', '3V3', 'RST', '4', '5', '6', '7', '15', '16', '17', '18', '8', '3', '46', '9', '10', '11', '12', '13', '14', '5V', 'G']
J3 = ['G', 'TX', 'RX', '1', '2', '42', '41', '40', '39', '38', '37', '36', '35', '0', '45', '48', '47', '21', '20', '19', 'G', 'G']

def esp_pin(name, which=None):
    """(header, index) of a pin name like '15' or '3V3'."""
    for hdr, lst in (('J1', J1), ('J3', J3)):
        if which and hdr != which: continue
        if name in lst: return hdr, lst.index(name)
    raise KeyError(name)

# ---------------------------------------------------------------- geometry
W, H = 1000, 690
P = 15                                   # breadboard pitch in the drawing
BX0 = 300                                # x of row 1
ROWS = 30
COLY = {c: y for c, y in zip('abcde', [436, 451, 466, 481, 496])}
COLY.update({c: y for c, y in zip('fghij', [526, 541, 556, 571, 586])})
RAILY = {'t+': 398, 't-': 412, 'b+': 610, 'b-': 624}
EX0, EY0, EX1, EY1 = 330, 70, 690, 180   # ESP32 board
EPITCH = 15.5

def rx(r): return BX0 + (r - 1) * P
def hole(r, c): return (rx(r), COLY[c])
def rail(k, r): return (rx(r), RAILY[k])
def epin(name, which=None):
    hdr, i = esp_pin(name, which)
    x = EX0 + 15 + i * EPITCH
    return (x, EY1 + 8) if hdr == 'J1' else (x, EY0 - 8)

# endpoints: (point, direction the wire leaves in)
def E_esp(name, which=None):
    hdr, _ = esp_pin(name, which)
    return (epin(name, which), (0, 1) if hdr == 'J1' else (0, -1))
def E_hole(r, c): return (hole(r, c), 'auto')
def E_rail(k, r): return (rail(k, r), 'auto')

# ---------------------------------------------------------------- modules (off the breadboard)
# name -> (x0, y0, x1, y1, pin side, [pins], colour, title, subtitle)
MODS = {
  'ds3231': (30, 30, 200, 125, 'right', ['VCC (+)', 'SDA (D)', 'SCL (C)', 'NC', 'GND (−)'], '#1f4e8c', 'DS3231 clock', 'pins: check your board'),
  'tm1637': (30, 150, 200, 225, 'right', ['CLK', 'DIO', 'VCC', 'GND'], '#c0392b', 'TM1637 display', ''),
  'amp':    (30, 250, 200, 370, 'right', ['LRC', 'BCLK', 'DIN', 'GAIN', 'SD', 'GND', 'VIN'], '#7b3fa0', 'MAX98357A amp', ''),
  'usbc':   (30, 560, 170, 625, 'right', ['VBUS', 'GND'], '#2a6f9e', 'USB-C breakout', '5 V 3 A supply'),
  'lcd':    (800, 30, 980, 175, 'left', ['RST', 'CE', 'DC', 'DIN', 'CLK', 'VCC', 'BL', 'GND'], '#b03030', 'Nokia 5110 LCD', ''),
  'ring':   (800, 200, 980, 320, 'left', ['DI', '5V', 'GND'], '#1d1d1d', 'WS2812B ring', ''),
  'mosfet': (800, 345, 980, 455, 'left', ['TRIG', 'GND', 'VIN+', 'VIN−', 'OUT+', 'OUT−'], '#2a6f9e', 'MOSFET module', ''),
  'led':    (840, 490, 980, 570, 'left', ['LED +', 'LED −'], '#d39a00', '3 W LED star', 'on metal'),
}
def mpin(mod, label):
    x0, y0, x1, y1, side, pins, *_ = MODS[mod]
    i = pins.index(label)
    y = y0 + 34 + i * 13
    return ((x1 + 2, y), (1, 0)) if side == 'right' else ((x0 - 2, y), (-1, 0))

# ---------------------------------------------------------------- drawing helpers
def esc(s): return html.escape(str(s), quote=True)
class Svg:
    def __init__(self): self.o = []
    def add(self, s): self.o.append(s)
    def text(self, x, y, s, size=11, fill='#222', anchor='start', weight=400, extra=''):
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" font-weight="{weight}" {extra}>{esc(s)}</text>')
    def rect(self, x, y, w, h, fill, stroke='none', rx=4, sw=1, extra=''):
        self.add(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>')
    def circle(self, x, y, r, fill, stroke='none', sw=1, extra=''):
        self.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>')
    def line(self, x1, y1, x2, y2, col, w=1.5, extra=''):
        self.add(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{col}" stroke-width="{w}" stroke-linecap="round" {extra}/>')

def autodir(a, b):
    # breadboard ends: leave toward the other end, mostly upward (wires lie on top of the board)
    dx, dy = b[0] - a[0], b[1] - a[1]
    if abs(dx) > 1.6 * abs(dy) and abs(dx) > 40: return (1 if dx > 0 else -1, -0.35)
    return (0, -1) if dy < 0 or abs(dy) < 30 else (0, 1)

def bez(p, q):
    (a, da), (b, db) = p, q
    if da == 'auto': da = autodir(a, b)
    if db == 'auto': db = autodir(b, a)
    d = max(35, min(170, 0.42 * ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5))
    c1 = (a[0] + da[0] * d, a[1] + da[1] * d)
    c2 = (b[0] + db[0] * d, b[1] + db[1] * d)
    path = f'M{a[0]:.1f},{a[1]:.1f} C{c1[0]:.1f},{c1[1]:.1f} {c2[0]:.1f},{c2[1]:.1f} {b[0]:.1f},{b[1]:.1f}'
    # midpoint of the cubic, for the number badge
    m = [(a[i] + 3 * c1[i] + 3 * c2[i] + b[i]) / 8 for i in (0, 1)]
    return path, m

COL = {'3v3': '#f39c12', 'gnd': '#222222', '5v': '#d32f2f', 'yellow': '#e6b800', 'green': '#2e9e44', 'blue': '#2c6fd6',
       'purple': '#8e44ad', 'white': '#9aa0a6', 'brown': '#8d5a2b', 'cyan': '#14a3b8', 'pink': '#e05297', 'grey': '#6b7280'}
COLNAME = {'3v3': 'orange', 'gnd': 'black', '5v': 'red', 'yellow': 'yellow', 'green': 'green', 'blue': 'blue', 'purple': 'purple',
           'white': 'white', 'brown': 'brown', 'cyan': 'cyan', 'pink': 'pink', 'grey': 'grey'}

# ---------------------------------------------------------------- the steps
# Each wire: (colour key, endpoint A, endpoint B, text A, text B, jumper type)
# Each part placed on the breadboard: ('kind', args...)
def W_(col, a, b, ta, tb, kind):
    return dict(col=col, a=a, b=b, ta=ta, tb=tb, kind=kind)

STEPS = []
def step(**k): STEPS.append(k)

step(id='flash', title='Flash the firmware', time='10 min', mods=[], parts=[], wires=[],
     need=['ESP32-S3 board', 'USB-C data cable', 'Computer'],
     intro='No wiring yet. Get the ESP32 running first, on its own, so you know the board and the firmware are good before anything else is connected.',
     todo=['Plug the USB-C cable into the port marked <b>USB</b> on the ESP32 (the board has two; this one carries the log).',
           'Flash the firmware from the <a href="firmware.html">Firmware</a> page: the web flasher needs nothing installed.',
           'Open a serial monitor at <b>115200</b> baud (the web flasher has one, or PlatformIO\'s monitor).',
           'On your phone, join the Wi-Fi network <b>CeilingClock-Setup</b> and pick your home network.'],
     test='Open <b>http://ceilingclock.local/</b> on your phone or computer. You should see the clock\'s page with the time and a green <b>synced just now</b>.',
     fix=[('ceilingclock.local doesn\'t open', 'Some Android phones don\'t support .local names. Use the IP address printed in the serial monitor instead.'),
          ('Nothing in the serial monitor', 'Use the port marked USB, not UART, at 115200 baud. Some USB-C cables only carry power: try another.'),
          ('No CeilingClock-Setup network', 'Press the RST button on the ESP32 and wait 20 seconds.')])

step(id='power', title='Power rails', time='5 min', mods=[], parts=[],
     need=['Breadboard', '3 jumper wires: 2 female–male, 1 male–male'],
     intro='The two rails along the top of the breadboard become 3.3 V (from the ESP32) and ground. Every small module will plug into them. A wire over the right-hand end joins the top ground rail to the bottom one.',
     wires=[W_('3v3', E_esp('3V3'), E_rail('t+', 1), 'ESP32 pin 3V3 (the first pin, by the antenna)', 'top + rail', 'female–male'),
            W_('gnd', E_esp('G', 'J1'), E_rail('t-', 26), 'ESP32 pin G (last pin on the same side, by the USB ports)', 'top − rail', 'female–male'),
            W_('gnd', ((rx(30), RAILY['t-']), (1, -0.3)), ((rx(30), RAILY['b-']), (1, 0.3)), 'top − rail, right end', 'bottom − rail, right end', 'male–male')],
     test='Nothing to see yet. If you have a multimeter, the top + and − rails should read about 3.3 V with the USB cable plugged in.',
     fix=[('The ESP32 goes dark or resets when you plug in the wire', 'The 3V3 wire is in the − rail or touching G. Unplug USB and check: orange to +, black to −.')])

step(id='buttons', title='Buttons', time='10 min', mods=[],
     need=['2 small 6 × 6 mm push buttons (from your tactile switch kit)', '4 jumper wires: 2 female–male, 2 male–male'],
     intro='For testing, use two small 4-legged push buttons; the 16 mm panel buttons go in later. Each one sits <b>across the gap</b> in the middle of the breadboard. Wire to <b>diagonally opposite legs</b>: that way it works whichever way round the button sits.',
     parts=[('button', 3, 'A'), ('button', 8, 'B')],
     wires=[W_('green', E_esp(str(G('PIN_BTN_A'))), E_hole(3, 'a'), f'ESP32 pin {G("PIN_BTN_A")}', 'hole a3 (button A, top-left leg)', 'female–male'),
            W_('gnd', E_hole(5, 'j'), E_rail('b-', 5), 'hole j5 (button A, bottom-right leg)', 'bottom − rail', 'male–male'),
            W_('blue', E_esp(str(G('PIN_BTN_B'))), E_hole(8, 'a'), f'ESP32 pin {G("PIN_BTN_B")}', 'hole a8 (button B, top-left leg)', 'female–male'),
            W_('gnd', E_hole(10, 'j'), E_rail('b-', 10), 'hole j10 (button B, bottom-right leg)', 'bottom − rail', 'male–male')],
     test='On the clock\'s page, press button <b>B</b>: the <b>Front display</b> button on the page flips between on and off. Hold B for 3 seconds: <b>Projector</b> flips. (Button A snoozes an alarm; you\'ll try it later.)',
     fix=[('Nothing happens', 'Check the wires go to diagonally opposite legs (a3 and j5, a8 and j10) and that the button straddles the gap.'),
          ('It acts as if always pressed', 'The button is turned so both wires land on legs that are always connected. Turn it 90°.')])

step(id='tm1637', title='Front display (TM1637)', time='5 min', mods=['tm1637'], parts=[],
     need=['TM1637 display', '4 jumper wires: 2 female–female, 2 female–male'],
     intro='The four-digit display that shows the time on the front of the clock. Its two data pins go straight to the ESP32; power comes from the top rails.',
     wires=[W_('yellow', E_esp(str(G('PIN_TM_CLK'))), mpin('tm1637', 'CLK'), f'ESP32 pin {G("PIN_TM_CLK")}', 'display CLK', 'female–female'),
            W_('white', E_esp(str(G('PIN_TM_DIO'))), mpin('tm1637', 'DIO'), f'ESP32 pin {G("PIN_TM_DIO")}', 'display DIO', 'female–female'),
            W_('3v3', mpin('tm1637', 'VCC'), E_rail('t+', 4), 'display VCC', 'top + rail', 'female–male'),
            W_('gnd', mpin('tm1637', 'GND'), E_rail('t-', 5), 'display GND', 'top − rail', 'female–male')],
     test='The display shows the time within a second. On the settings page, change the front display\'s brightness: it follows.',
     fix=[('Display stays blank', 'CLK and DIO swapped? VCC must go to the + rail (3.3 V).'),
          ('Shows 88:88 or garbage', 'A loose jumper: push each one firmly onto its pin.')])

step(id='lcd', title='Projector LCD (Nokia 5110)', time='10 min', mods=['lcd'], parts=[],
     need=['Nokia 5110 LCD (no need to cut it yet)', '8 jumper wires: 5 female–female, 3 female–male'],
     intro='The LCD makes the image on the ceiling. Test it as it comes, before cutting its window: lighting its own backlight lets you read it on the bench.',
     wires=[W_('brown', E_esp(str(G('PIN_LCD_RST'))), mpin('lcd', 'RST'), f'ESP32 pin {G("PIN_LCD_RST")}', 'LCD RST', 'female–female'),
            W_('purple', E_esp(str(G('PIN_LCD_CE'))), mpin('lcd', 'CE'), f'ESP32 pin {G("PIN_LCD_CE")}', 'LCD CE', 'female–female'),
            W_('cyan', E_esp(str(G('PIN_LCD_DC'))), mpin('lcd', 'DC'), f'ESP32 pin {G("PIN_LCD_DC")}', 'LCD DC', 'female–female'),
            W_('green', E_esp(str(G('PIN_LCD_DIN'))), mpin('lcd', 'DIN'), f'ESP32 pin {G("PIN_LCD_DIN")}', 'LCD DIN', 'female–female'),
            W_('yellow', E_esp(str(G('PIN_LCD_CLK'))), mpin('lcd', 'CLK'), f'ESP32 pin {G("PIN_LCD_CLK")}', 'LCD CLK', 'female–female'),
            W_('3v3', mpin('lcd', 'VCC'), E_rail('t+', 28), 'LCD VCC', 'top + rail', 'female–male'),
            W_('gnd', mpin('lcd', 'BL'), E_rail('t-', 27), 'LCD BL (bench only: lights it)', 'top − rail', 'female–male'),
            W_('gnd', mpin('lcd', 'GND'), E_rail('t-', 29), 'LCD GND', 'top − rail', 'female–male')],
     test='The LCD shows the time, <b>back to front</b>: the clock mirrors it for the projector. Untick <b>Mirror left/right</b> in the projector settings to read it, and tick it again before testing the optics.',
     fix=[('Blank or solid black', 'Adjust <b>LCD contrast</b> on the settings page. Check RST and CE.'),
          ('No backlight', 'On some boards BL lights when connected to + instead of −. Move that one wire to the top + rail.')])

step(id='ldr', title='Light sensor', time='5 min', mods=[],
     need=['GL5528 light sensor', '10 kΩ resistor (brown-black-orange)', '2 jumper wires: 1 female–male, 1 male–male'],
     intro='A light-dependent resistor and a fixed 10 kΩ resistor make a divider: the voltage between them rises as the room gets brighter. Neither part has a polarity.',
     parts=[('ldr', 13, 16), ('res_rail', 16, 't-', '10 kΩ')],
     wires=[W_('3v3', E_rail('t+', 13), E_hole(13, 'a'), 'top + rail', 'hole a13 (one leg of the sensor)', 'male–male'),
            W_('pink', E_esp(str(G('PIN_LDR'))), E_hole(16, 'd'), f'ESP32 pin {G("PIN_LDR")}', 'hole d16 (where sensor and resistor meet)', 'female–male')],
     test='In the night settings, watch <b>sensor now</b> next to "Dark below". It goes up with a torch on the sensor and down when you cover it with a finger.',
     fix=[('Always about 0', 'The sensor leg isn\'t in row 13 or the orange wire isn\'t on the + rail.'),
          ('Always about 4095', 'The 10 kΩ resistor isn\'t reaching the − rail.')])

step(id='ds3231', title='Clock module (DS3231)', time='5 min', mods=['ds3231'], parts=[],
     need=['DS3231 module (with its coin cell)', '4 jumper wires: 2 female–female, 2 female–male'],
     intro='The battery-backed clock that keeps time when Wi-Fi or power drops. Its two data pins are on the <b>other</b> side of the ESP32 (pins 1 and 2), so route those wires round the end of the board.',
     wires=[W_('blue', E_esp(str(G('PIN_SDA')), 'J3'), mpin('ds3231', 'SDA (D)'), f'ESP32 pin {G("PIN_SDA")} (far side)', 'module SDA (marked D on mini boards)', 'female–female'),
            W_('yellow', E_esp(str(G('PIN_SCL')), 'J3'), mpin('ds3231', 'SCL (C)'), f'ESP32 pin {G("PIN_SCL")} (far side)', 'module SCL (marked C)', 'female–female'),
            W_('3v3', mpin('ds3231', 'VCC (+)'), E_rail('t+', 2), 'module VCC (+)', 'top + rail', 'female–male'),
            W_('gnd', mpin('ds3231', 'GND (−)'), E_rail('t-', 3), 'module GND (−)', 'top − rail', 'female–male')],
     test='The page shows <b>RTC backup ok</b>. Turn your router\'s Wi-Fi off and press RST on the ESP32: the time is still right.',
     fix=[('Still says "no RTC"', 'SDA and SCL swapped, or VCC on 5 V instead of 3.3 V.'),
          ('ZS-042 (larger) board', 'It charges its battery. With a non-rechargeable CR2032, remove the 200 Ω resistor or diode beside the holder first.')])

step(id='supply', title='5 V supply', time='10 min', mods=['usbc'], parts=[],
     need=['USB-C breakout + 5 V 3 A adapter', '2 wires soldered to VBUS and GND (or header pins)'],
     intro='From here on, parts need more current than the ESP32 can give. The 5 V supply feeds the <b>bottom</b> rails only. The ESP32 stays on your computer\'s USB, and the grounds are already joined.',
     wires=[W_('5v', mpin('usbc', 'VBUS'), E_rail('b+', 1), 'breakout VBUS', 'bottom + rail', 'soldered lead'),
            W_('gnd', mpin('usbc', 'GND'), E_rail('b-', 2), 'breakout GND', 'bottom − rail', 'soldered lead')],
     test='Plug the adapter in. Everything carries on as before. With a multimeter, the bottom rails read about 5 V.',
     fix=[('Reads 0 V', 'Some breakouts only switch on with a USB-C to USB-C charger and 5.1 kΩ CC resistors (yours has them). Try another cable.')],
     warn='Never connect this 5 V to the ESP32\'s <b>5V</b> pin while the computer is plugged in: two supplies would fight through the board. In the finished clock the computer stays unplugged.')

step(id='amp', title='Amplifier and speaker', time='10 min', mods=['amp'],
     need=['MAX98357A amplifier', '40 mm speaker', '100 µF capacitor', '5 jumper wires: 3 female–female, 2 female–male'],
     intro='Plays the alarm sounds. The capacitor steadies its supply; the long leg is +, and the stripe marks −.',
     parts=[('cap', 19, '100 µF')],
     wires=[W_('purple', E_esp(str(G('PIN_I2S_BCLK'))), mpin('amp', 'BCLK'), f'ESP32 pin {G("PIN_I2S_BCLK")}', 'amp BCLK', 'female–female'),
            W_('cyan', E_esp(str(G('PIN_I2S_LRC'))), mpin('amp', 'LRC'), f'ESP32 pin {G("PIN_I2S_LRC")}', 'amp LRC', 'female–female'),
            W_('white', E_esp(str(G('PIN_I2S_DOUT'))), mpin('amp', 'DIN'), f'ESP32 pin {G("PIN_I2S_DOUT")}', 'amp DIN', 'female–female'),
            W_('5v', mpin('amp', 'VIN'), E_rail('b+', 6), 'amp VIN', 'bottom + rail (5 V)', 'female–male'),
            W_('gnd', mpin('amp', 'GND'), E_rail('b-', 7), 'amp GND', 'bottom − rail', 'female–male')],
     test='Screw the speaker leads into the amp\'s + and − terminals. Under <b>Sounds</b>, press <b>Play</b> on beep.wav: four beeps. Then give an alarm a radio or podcast URL and press <b>Preview stream</b>.',
     fix=[('Silent', 'Is the 5 V adapter plugged in? Check BCLK, LRC and DIN aren\'t swapped. Leave GAIN and SD unconnected.'),
          ('Crackles', 'Push the capacitor\'s legs fully into the rails (long leg to +).')])

step(id='ring', title='Sunrise ring', time='10 min', mods=['ring'],
     need=['WS2812B 16-LED ring (with leads soldered on)', '330 Ω resistor (orange-orange-brown)', '1000 µF capacitor', '4 jumper wires'],
     intro='The sunrise light. The 330 Ω resistor protects the ring\'s data input; the big capacitor smooths the current the LEDs draw. Mind the capacitor\'s stripe: it goes to −.',
     parts=[('res', 21, 25, 'c', '330 Ω'), ('cap', 23, '1000 µF')],
     wires=[W_('green', E_esp(str(G('PIN_RING'))), E_hole(21, 'a'), f'ESP32 pin {G("PIN_RING")}', 'hole a21 (one end of the 330 Ω)', 'female–male'),
            W_('green', E_hole(25, 'a'), mpin('ring', 'DI'), 'hole a25 (other end of the 330 Ω)', 'ring DI (data in)', 'male–female'),
            W_('5v', mpin('ring', '5V'), E_rail('b+', 27), 'ring 5V', 'bottom + rail', 'female–male'),
            W_('gnd', mpin('ring', 'GND'), E_rail('b-', 28), 'ring GND', 'bottom − rail', 'female–male')],
     test='Give an alarm a sunrise time (for example 15 minutes) and press <b>Ring now</b>: the ring glows warm white until you press <b>Dismiss</b> (or hold button A for 2 seconds).',
     fix=[('Nothing lights', 'Make sure the wire goes to DI (in), not DO (out). Check the 5 V adapter is on.'),
          ('Flickers or wrong colours', 'Keep the data wire short. If it persists, a 74AHCT125 level shifter on the data line fixes it.')])

step(id='led', title='Projector LED', time='15 min', mods=['mosfet', 'led'],
     need=['MOSFET module', '3 W LED on its star (leads soldered on)', '4.7 Ω 2 W resistor', 'Something metal to sit the LED on', '6 jumper wires'],
     intro='The bright LED that lights the LCD. The MOSFET module switches and dims it for the ESP32. The 4.7 Ω resistor limits the current to about 400 mA, and it gets warm, so keep it off the plastic.',
     parts=[('res', 26, 30, 'g', '4.7 Ω 2 W')],
     wires=[W_('grey', E_esp(str(G('PIN_PROJ_LED'))), mpin('mosfet', 'TRIG'), f'ESP32 pin {G("PIN_PROJ_LED")}', 'module TRIG / PWM', 'female–female'),
            W_('gnd', mpin('mosfet', 'GND'), E_rail('b-', 26), 'module trigger GND', 'bottom − rail', 'female–male'),
            W_('5v', mpin('mosfet', 'VIN+'), E_rail('b+', 29), 'module VIN+', 'bottom + rail (5 V)', 'screw terminal–male'),
            W_('gnd', mpin('mosfet', 'VIN−'), E_rail('b-', 25), 'module VIN−', 'bottom − rail', 'screw terminal–male'),
            W_('5v', mpin('mosfet', 'OUT+'), E_hole(26, 'j'), 'module OUT+', 'hole j26 (one end of the 4.7 Ω)', 'screw terminal–male'),
            W_('5v', E_hole(30, 'j'), mpin('led', 'LED +'), 'hole j30 (other end of the 4.7 Ω)', 'LED +', 'male–soldered lead'),
            W_('gnd', mpin('led', 'LED −'), mpin('mosfet', 'OUT−'), 'LED −', 'module OUT−', 'soldered lead–screw terminal')],
     test='On the clock\'s page, switch the <b>Projector</b> off and on: the LED goes off and on. Change the projector\'s day brightness: it dims.',
     fix=[('LED never lights', 'LED + and − swapped? Check OUT+ goes through the resistor to LED +.'),
          ('Always on full', 'TRIG is on the wrong pin, or the module\'s trigger GND isn\'t connected.')],
     warn='Don\'t look straight into the lit LED. Without its heatsink it heats up in seconds: sit the star on metal and don\'t leave it at full brightness for more than a few seconds.')

# ---------------------------------------------------------------- drawing one step
def draw_step(k):
    s = Svg()
    s.add(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" class="bbsvg" font-family="system-ui,-apple-system,Segoe UI,sans-serif">')
    s.rect(0, 0, W, H, '#fbfaf6', rx=0)
    mods_now = [m for st in STEPS[:k + 1] for m in st['mods']]
    new_mods = STEPS[k]['mods']
    # breadboard
    s.rect(BX0 - 22, 380, (ROWS - 1) * P + 44, 258, '#f3f1ea', '#cfcabc', 10, 1.2)
    for key, col, lab in (('t+', '#d33a2c', '+3V3'), ('t-', '#2b5fd9', '−GND'), ('b+', '#d33a2c', '+5 V'), ('b-', '#2b5fd9', '−GND')):
        y = RAILY[key]
        s.line(BX0 - 10, y - 7 if key.endswith('+') else y + 7, rx(ROWS) + 10, y - 7 if key.endswith('+') else y + 7, col, 1)
        s.text(BX0 - 18, y + 3.5, lab.split('V')[0][:1], 11, col, 'end', 700)
        for r in range(1, ROWS + 1): s.rect(rx(r) - 2.2, y - 2.2, 4.4, 4.4, '#8a8577', rx=0.8)
    s.text(rx(ROWS) + 14, RAILY['t+'] + 4, '3.3 V', 10, '#d33a2c', 'start', 700)
    s.text(rx(ROWS) + 14, RAILY['b+'] + 4, '5 V', 10, '#d33a2c', 'start', 700)
    for c, y in COLY.items():
        s.text(BX0 - 14, y + 3.5, c, 9.5, '#8a8577', 'middle')
        for r in range(1, ROWS + 1): s.rect(rx(r) - 2.2, y - 2.2, 4.4, 4.4, '#8a8577', rx=0.8)
    s.rect(BX0 - 6, 503, (ROWS - 1) * P + 12, 16, '#e6e2d6', rx=2)
    for r in (1, 5, 10, 15, 20, 25, 30): s.text(rx(r), 425, r, 8.5, '#8a8577', 'middle')
    # ESP32
    s.rect(EX0, EY0, EX1 - EX0, EY1 - EY0, '#1e2126', '#000', 6)
    s.rect(EX0 + 6, EY0 + 22, 92, EY1 - EY0 - 44, '#c8ccd2', rx=3)
    for i in range(5): s.line(EX0 + 12, EY0 + 30 + i * 12, EX0 + 30, EY0 + 30 + i * 12, '#9aa0a8', 2)
    s.text(EX0 + 52, EY0 + 58, 'ESP32-S3', 10, '#5b6068', 'middle', 700)
    s.rect(EX1 - 2, EY0 + 26, 16, 20, '#9aa0a8', rx=2); s.rect(EX1 - 2, EY0 + 64, 16, 20, '#9aa0a8', rx=2)
    s.text(EX1 + 18, EY0 + 40, 'UART', 8.5, '#6b7280'); s.text(EX1 + 18, EY0 + 78, 'USB → computer', 8.5, '#2b5fd9', 'start', 700)
    s.text((EX0 + EX1) / 2 + 40, (EY0 + EY1) / 2 + 4, 'DevKitC-1', 11, '#cfd3da', 'middle', 700)
    used = set()
    for st in STEPS[:k + 1]:
        for w in st['wires']:
            for e in (w['a'], w['b']):
                for nm, hdr in [(n, 'J1') for n in J1] + [(n, 'J3') for n in J3]:
                    pass
    for hdr, lst in (('J1', J1), ('J3', J3)):
        for i, nm in enumerate(lst):
            x = EX0 + 15 + i * EPITCH
            y = EY1 - 6 if hdr == 'J1' else EY0 + 6
            s.circle(x, y, 2.6, '#d8ad45')
            s.text(x, (EY1 - 15) if hdr == 'J1' else (EY0 + 19), nm, 7.5, '#e7e9ec', 'middle')
    # modules present
    for m in mods_now:
        x0, y0, x1, y1, side, pins, col, title, sub = MODS[m]
        op = '1' if m in new_mods or k == len(STEPS) else '0.45'
        s.add(f'<g opacity="{op}">')
        s.rect(x0, y0, x1 - x0, y1 - y0, '#fffdf8', col, 8, 2)
        s.rect(x0, y0, x1 - x0, 20, col, rx=8); s.rect(x0, y0 + 12, x1 - x0, 8, col, rx=0)
        s.text(x0 + 8, y0 + 14.5, title, 11, '#fff', 'start', 700)
        if sub: s.text(x0 + (x1 - x0) / 2, y1 - 6, sub, 8.5, '#8a8577', 'middle')
        for i, pn in enumerate(pins):
            (px, py), _ = mpin(m, pn)
            s.circle(px, py, 3, '#d8ad45', '#6b5a2b', 0.8)
            s.text(px - 7 if side == 'right' else px + 7, py + 3.5, pn, 9, '#333', 'end' if side == 'right' else 'start')
        if m == 'amp':   # speaker on its terminal
            s.circle(x0 + 55, y1 + 32, 22, '#3b3b3b'); s.circle(x0 + 55, y1 + 32, 9, '#777')
            s.line(x0 + 50, y1, x0 + 48, y1 + 12, '#d32f2f', 2); s.line(x0 + 62, y1, x0 + 64, y1 + 12, '#222', 2)
            s.text(x0 + 85, y1 + 36, 'speaker', 9, '#6b7280')
        if m == 'ring':
            s.add(f'<circle cx="{x0 + 120}" cy="{y0 + 66}" r="30" fill="none" stroke="#1d1d1d" stroke-width="9"/>')
            for a in range(16):
                import math
                s.circle(x0 + 120 + 30 * math.cos(a * math.pi / 8), y0 + 66 + 30 * math.sin(a * math.pi / 8), 3, '#ffe9a8')
        if m == 'led':
            s.rect(x0 + 50, y0 + 26, 80, 40, '#9aa0a8', rx=3)
            for i in range(6): s.line(x0 + 56 + i * 13, y0 + 66, x0 + 56 + i * 13, y0 + 74, '#7b8088', 3)
            s.circle(x0 + 90, y0 + 36, 13, '#e9edf2', '#b8bec6'); s.circle(x0 + 90, y0 + 36, 4, '#ffe07a')
        if m == 'usbc':
            s.rect(x0 - 26, y0 + 22, 22, 26, '#e8eaed', '#9aa0a8', 3); s.text(x0 - 15, y0 + 60, '5 V', 8.5, '#6b7280', 'middle')
            s.line(x0 - 4, y0 + 35, x0 + 6, y0 + 35, '#555', 4)
        s.add('</g>')
    # parts on the breadboard
    for idx, st in enumerate(STEPS[:k + 1]):
        op = '1' if idx == k else '0.45'
        s.add(f'<g opacity="{op}">')
        for p in st['parts']:
            if p[0] == 'button':
                r = p[1]
                x0, x1 = rx(r) - 4, rx(r + 2) + 4
                s.rect(x0, COLY['e'] - 6, x1 - x0, COLY['f'] - COLY['e'] + 12, '#30343b', rx=3)
                s.circle((x0 + x1) / 2, (COLY['e'] + COLY['f']) / 2, 8, '#111', '#5b6068')
                for c in 'ef':
                    for rr in (r, r + 2): s.circle(rx(rr), COLY[c], 2.6, '#c8ccd2')
                s.text((x0 + x1) / 2, COLY['f'] + 22, p[2], 11, '#30343b', 'middle', 700)
            elif p[0] == 'ldr':
                a, b = hole(p[1], 'c'), hole(p[2], 'c')
                s.line(*a, (a[0] + b[0]) / 2 - 8, a[1] - 14, '#888', 1.6); s.line(*b, (a[0] + b[0]) / 2 + 8, a[1] - 14, '#888', 1.6)
                s.circle((a[0] + b[0]) / 2, a[1] - 18, 9, '#f4e2c0', '#b98a3a', 1.5)
                s.add(f'<path d="M{(a[0]+b[0])/2-6},{a[1]-18} q3,-5 6,0 q3,5 6,0" fill="none" stroke="#b03030" stroke-width="1.6"/>')
                s.text((a[0] + b[0]) / 2, a[1] - 31, 'light sensor', 9, '#6b5a2b', 'middle', 700)
            elif p[0] == 'res_rail':
                a, b = hole(p[1], 'a'), rail(p[2], p[1] + 1)
                s.line(*a, *b, '#888', 1.6)
                mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
                s.rect(mx - 4, my - 9, 8, 18, '#d9c49a', '#9a8455', 2)
                s.text(mx + 10, my + 3, p[3], 9, '#6b5a2b', 'start', 700)
            elif p[0] == 'res':
                a, b = hole(p[1], p[3]), hole(p[2], p[3])
                s.line(*a, *b, '#888', 1.6)
                mx = (a[0] + b[0]) / 2
                big = '2 W' in p[4]
                s.rect(mx - (16 if big else 11), a[1] - (5 if big else 4), 32 if big else 22, 10 if big else 8, '#7ab3d6' if big else '#d9c49a', '#55606e' if big else '#9a8455', 3)
                s.text(mx, a[1] - 9, p[4], 9, '#55606e', 'middle', 700)
            elif p[0] == 'cap':
                r = p[1]
                a, b = rail('b+', r), rail('b-', r + 1)
                cx, cy = (a[0] + b[0]) / 2, RAILY['b-'] + 26
                s.line(*a, cx - 3, cy - 8, '#888', 1.4); s.line(*b, cx + 3, cy - 8, '#888', 1.4)
                big = '1000' in p[2]
                rw = 9 if big else 6
                s.rect(cx - rw, cy - 8, 2 * rw, 20 if big else 14, '#2140a0', rx=3)
                s.rect(cx + rw - 4, cy - 8, 3, 20 if big else 14, '#c8ccd2', rx=1)
                s.text(cx, cy + (25 if big else 19), p[2], 8.5, '#2140a0', 'middle', 700)
        s.add('</g>')
    # wires: earlier steps faded, this step bright with number badges
    n = 0
    for idx, st in enumerate(STEPS[:k + 1]):
        cur = idx == k
        for w in st['wires']:
            path, m = bez(w['a'], w['b'])
            col = COL[w['col']]
            if cur:
                n += 1
                s.add(f'<g class="wire" data-w="{STEPS[k]["id"]}-{n}"><path d="{path}" fill="none" stroke="#fff" stroke-width="6.5" stroke-linecap="round"/>'
                      f'<path d="{path}" fill="none" stroke="{col}" stroke-width="3.6" stroke-linecap="round"/>')
                for e in (w['a'], w['b']): s.circle(*e[0], 3.6, col, '#fff', 1.2)
                s.circle(m[0], m[1], 9, '#fff', col, 2); s.text(m[0], m[1] + 3.8, n, 10.5, '#111', 'middle', 700)
                s.add('</g>')
            else:
                s.add(f'<path d="{path}" fill="none" stroke="{col}" stroke-width="2.4" stroke-linecap="round" opacity="0.28"/>')
    s.add('</svg>')
    return '\n'.join(s.o)

# ---------------------------------------------------------------- small explainer pictures
def svg_basics():
    s = Svg()
    s.add('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 560 330" class="bbsvg" font-family="system-ui,-apple-system,Segoe UI,sans-serif">')
    s.rect(0, 0, 560, 330, '#fbfaf6', rx=0)
    x0, p, n = 46, 13, 12
    cols = {'a': 98, 'b': 110, 'c': 122, 'd': 134, 'e': 146, 'f': 170, 'g': 182, 'h': 194, 'i': 206, 'j': 218}
    ys = {'t+': 58, 't-': 72, 'b+': 244, 'b-': 258}
    s.rect(x0 - 18, 42, n * p + 26, 232, '#f3f1ea', '#cfcabc', 10)
    s.rect(x0 - 6, 152, n * p - 2, 12, '#e6e2d6', rx=2)
    s.rect(x0 - 8, ys['t+'] - 6, n * p - 2, 12, '#ffd6d1', rx=6)
    s.rect(x0 + 5 * p - 6, cols['a'] - 6, 12, cols['e'] - cols['a'] + 12, '#c9f0cf', rx=6)
    s.rect(x0 + 5 * p - 6, cols['f'] - 6, 12, cols['j'] - cols['f'] + 12, '#cfe0ff', rx=6)
    for y in list(ys.values()) + list(cols.values()):
        for r in range(n): s.rect(x0 + r * p - 2.3, y - 2.3, 4.6, 4.6, '#8a8577', rx=1)
    for c, y in cols.items(): s.text(x0 - 10, y + 3.5, c, 9.5, '#8a8577', 'end')
    s.text(x0 - 10, ys['t+'] + 4, '+', 11, '#d33a2c', 'end', 700); s.text(x0 - 10, ys['t-'] + 4, '−', 11, '#2b5fd9', 'end', 700)
    tx = x0 + n * p + 22
    def note(y, head, body, col):
        s.text(tx, y, head, 12.5, col, 'start', 700)
        for i, ln in enumerate(body): s.text(tx, y + 17 + i * 15, ln, 11.5, '#333')
    note(52, 'Rails (red and blue lines)', ['Each line of holes along the edge is one long', 'connection. Use them for + power and − ground.'], '#c0392b')
    note(112, 'Columns of five', ['Holes a–e in one column are joined, so', 'anything in the same five is connected.'], '#2e8b3d')
    note(172, 'The gap in the middle', ['Splits each column: a–e and f–j are separate.', 'Push buttons sit across it.'], '#555')
    note(232, 'f–j: another group of five', ['Joined to each other, not to a–e.'], '#2b5fd9')
    s.add('</svg>')
    return '\n'.join(s.o)

def svg_jumpers():
    s = Svg()
    s.add('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 130" class="bbsvg" font-family="system-ui,-apple-system,Segoe UI,sans-serif">')
    s.rect(0, 0, 640, 130, '#fbfaf6', rx=0)
    def end(x, y, male, flip):
        d = -1 if flip else 1
        if male:
            s.rect(x - 7 if d > 0 else x - 1, y - 5, 8, 10, '#222', rx=1)
            s.line(x + d * 1, y, x + d * 12, y, '#c9a227', 2.4)
        else:
            s.rect(x - 9 if d > 0 else x - 3, y - 6, 12, 12, '#222', rx=1.5)
            s.circle(x + d * 2, y, 2, '#555')
    for i, (a, b, lab, use) in enumerate([(True, True, 'male–male', 'breadboard hole to breadboard hole'),
                                          (False, True, 'female–male', 'ESP32 or module pin to a breadboard hole'),
                                          (False, False, 'female–female', 'ESP32 pin straight to a module pin')]):
        x = 30 + i * 205
        s.add(f'<path d="M{x+14},64 C{x+60},30 {x+110},98 {x+150},64" fill="none" stroke="{["#2e9e44","#e6b800","#2c6fd6"][i]}" stroke-width="4" stroke-linecap="round"/>')
        end(x + 8, 64, a, True); end(x + 156, 64, b, False)
        s.text(x + 82, 22, lab, 13, '#222', 'middle', 700)
        s.text(x + 82, 112, use, 10.5, '#555', 'middle')
    s.add('</svg>')
    return '\n'.join(s.o)

def svg_optics():
    s = Svg()
    s.add('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 330" class="bbsvg" font-family="system-ui,-apple-system,Segoe UI,sans-serif">')
    s.rect(0, 0, 640, 330, '#1d2026', rx=0)
    s.add('<polygon points="250,300 330,300 470,16 110,16" fill="#ffe6b0" opacity="0.10"/>')
    s.rect(60, 8, 520, 10, '#3a3f47', rx=2); s.text(320, 34, 'ceiling: the time, sharp when the lens is right', 11.5, '#ffd696', 'middle', 700)
    def part(y, w, h, col, lab, sub):
        s.rect(290 - w / 2, y, w, h, col, rx=2)
        s.line(290 + w / 2 + 6, y + h / 2, 362, y + h / 2, '#5b6068', 1)
        s.text(370, y + h / 2 + 4, lab, 12, '#e8e8e8', 'start', 700)
        s.text(370 + 7.2 * len(lab) + 8, y + h / 2 + 4, sub, 10.5, '#aab0b8')
    s.add('<ellipse cx="290" cy="110" rx="34" ry="5" fill="#9fd3ff" opacity="0.8"/>')
    s.text(370, 106, 'lens (50 mm, f = 100)', 12, '#e8e8e8', 'start', 700); s.text(370, 122, 'move it up and down to focus', 10.5, '#aab0b8')
    part(232, 46, 4, '#c8ccd2', 'LCD, glass up', '30 mm above the LED')
    part(266, 50, 2, '#ffffff', 'baking paper', '10 mm above the LED')
    s.rect(272, 296, 36, 8, '#9aa0a8', rx=2); s.circle(290, 294, 5, '#ffe07a')
    s.line(314, 298, 362, 298, '#5b6068', 1); s.text(370, 302, 'LED, pointing up', 12, '#e8e8e8', 'start', 700)
    s.line(230, 112, 230, 232, '#ffd696', 1.2); s.line(224, 112, 236, 112, '#ffd696', 1.2); s.line(224, 232, 236, 232, '#ffd696', 1.2)
    s.text(222, 176, 'about 106 mm', 11, '#ffd696', 'end', 700)
    s.add('</svg>')
    return '\n'.join(s.o)

# ---------------------------------------------------------------- the page
def page():
    total = sum(len(st['wires']) for st in STEPS)
    nav = ''.join(f'<a href="#s-{st["id"]}"><span>{i + 1}</span>{esc(st["title"])}</a>' for i, st in enumerate(STEPS))
    out = []
    for i, st in enumerate(STEPS):
        wl = []
        for j, w in enumerate(st['wires']):
            wid = f'{st["id"]}-{j + 1}'
            wl.append(f'<li data-w="{wid}"><label><input type="checkbox" data-k="{wid}"><span class="badge" style="border-color:{COL[w["col"]]}">{j + 1}</span>'
                      f'<span class="sw" style="background:{COL[w["col"]]}"></span><span class="wt"><b>{esc(COLNAME[w["col"]].capitalize())} wire</b> ({esc(w["kind"])}):<br>'
                      f'{w["ta"]} <span class="arr">→</span> {w["tb"]}</span></label></li>')
        todo = ''.join(f'<li>{t}</li>' for t in st.get('todo', []))
        fixes = ''.join(f'<dt>{esc(a)}</dt><dd>{b}</dd>' for a, b in st['fix'])
        need = ''.join(f'<span class="chip">{esc(n)}</span>' for n in st['need'])
        warn = f'<div class="warn">⚠️ {st["warn"]}</div>' if st.get('warn') else ''
        out.append(f'''
<section class="bbstep" id="s-{st['id']}">
  <div class="bbhead"><span class="num">{i + 1}</span><h2>{esc(st['title'])}</h2><span class="time">⏱ {st['time']}</span></div>
  <p>{st['intro']}</p>
  <div class="need"><b>You need:</b> {need}</div>
  {warn}
  <div class="pic">{draw_step(i)}</div>
  {'<p class="mut" style="margin:4px 0 10px">New wires are bright and numbered; earlier ones are faded. Hover a wire in the list to find it in the picture.</p>' if st['wires'] else ''}
  {f'<ol class="todo">{todo}</ol>' if todo else ''}
  {f'<h3>Connect</h3><ul class="wires">{"".join(wl)}</ul>' if wl else ''}
  <div class="test"><b>✅ Test it:</b> {st['test']}</div>
  <details><summary>Not working?</summary><dl>{fixes}</dl></details>
</section>''')
    return f'''<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Breadboard test · Ceiling Clock</title>
<link rel="stylesheet" href="style.css?v=20261030w">
<style>
.bbsvg{{width:100%;height:auto;display:block;border:1px solid var(--line);border-radius:12px;background:#fbfaf6}}
.toc{{display:flex;flex-wrap:wrap;gap:6px;margin:14px 0 6px}}
.toc a{{display:flex;align-items:center;gap:6px;border:1px solid var(--line);border-radius:999px;padding:4px 10px 4px 4px;text-decoration:none;color:inherit;font-size:.88rem;background:var(--paper)}}
.toc a span{{display:inline-grid;place-items:center;width:22px;height:22px;border-radius:50%;background:#e8743b;color:#fff;font-weight:700;font-size:.8rem}}
.toc a.done span{{background:#2e9e44}}
.progress{{position:sticky;top:0;z-index:5;background:var(--bg,#fff);padding:8px 0;border-bottom:1px solid var(--line)}}
.progress .bar{{height:8px;border-radius:99px;background:#e9e6dd;overflow:hidden}}.progress .bar i{{display:block;height:100%;width:0;background:#2e9e44;transition:width .3s}}
.progress small{{color:var(--mut)}}
.bbstep{{border:1px solid var(--line);border-radius:16px;padding:18px 18px 10px;margin:22px 0;background:var(--paper)}}
.bbhead{{display:flex;align-items:center;gap:12px}}.bbhead h2{{margin:0;flex:1}}
.bbhead .num{{display:grid;place-items:center;width:38px;height:38px;border-radius:50%;background:#e8743b;color:#fff;font-weight:800;font-size:1.1rem}}
.bbstep.done .bbhead .num{{background:#2e9e44}}
.time{{color:var(--mut);font-size:.9rem}}
.chip{{display:inline-block;background:#eef2f7;border:1px solid #d8e0ea;border-radius:999px;padding:2px 9px;margin:2px 3px;font-size:.85rem}}
.need{{margin:8px 0 10px}}
.pic{{margin:8px 0}}
.wires{{list-style:none;padding:0;margin:6px 0 10px;display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));gap:6px}}
.wires li label{{display:flex;align-items:flex-start;gap:8px;border:1px solid var(--line);border-radius:10px;padding:8px;cursor:pointer;background:#fff}}
.wires li.hl label{{border-color:#e8743b;box-shadow:0 0 0 2px #f6c3a9}}
.wires input{{margin-top:3px;width:18px;height:18px;accent-color:#2e9e44}}
.wires li input:checked ~ .wt{{color:#6b7280;text-decoration:line-through}}
.badge{{display:inline-grid;place-items:center;min-width:22px;height:22px;border-radius:50%;border:2.5px solid;font-weight:800;font-size:.8rem}}
.sw{{width:10px;height:22px;border-radius:3px;flex:none}}
.arr{{color:#e8743b;font-weight:800}}
.todo li{{margin:4px 0}}
.test{{background:#eaf7ec;border:1px solid #bfe5c6;border-radius:10px;padding:10px 12px;margin:10px 0}}
.warn{{background:#fff3e0;border:1px solid #ffd59a;border-radius:10px;padding:10px 12px;margin:10px 0}}
details{{margin:6px 0 8px}}summary{{cursor:pointer;font-weight:700;color:#b5541f}}dl{{margin:8px 0}}dt{{font-weight:700;margin-top:6px}}dd{{margin:2px 0 0 0;color:#444}}
.wire{{cursor:pointer}}.bbsvg .wire.hl path:last-of-type{{stroke-width:6}}
.legend{{display:flex;flex-wrap:wrap;gap:14px;margin:8px 0}}.legend span{{display:flex;align-items:center;gap:6px}}.legend i{{width:22px;height:6px;border-radius:3px;display:inline-block}}
.two{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}@media(max-width:800px){{.two{{grid-template-columns:1fr}}}}
</style>
</head><body>
<header class="site"><div class="in">
<a class="brand" href="index.html"><span class="dot"></span>Ceiling Clock</a>
<nav><a href="index.html">3D model</a><a href="assembly.html">Assembly</a><a href="wiring.html">Wiring</a><a href="breadboard.html" class="on">Breadboard test</a><a href="parts.html">Parts</a><a href="demo/">Live demo</a><a href="firmware.html">Firmware &amp; use</a><a href="https://github.com/ScottYates/ceilingclock">GitHub</a></nav>
</div></header>
<main>
<h1>Breadboard test</h1>
<p class="lead">Wire the clock's electronics up on a breadboard and check every part works, before you solder anything or print the case. You add one part at a time and test it, so if something doesn't work you know exactly where to look. No soldering is needed except for the parts that only come with solder pads (the USB-C breakout, the LED and the ring). Allow an evening.</p>

<div class="progress"><div class="bar"><i id="pbar"></i></div><small id="ptext">0 of {total} wires connected</small></div>
<div class="toc" id="toc">{nav}</div>

<h2>Before you start</h2>
<div class="two">
<div><h3>How a breadboard works</h3>{svg_basics()}</div>
<div><h3>Three kinds of jumper wire</h3>{svg_jumpers()}
<p>The ESP32 board is too wide to leave free holes beside its pins on a standard breadboard, so it sits <b>next to</b> the breadboard and you connect to its pins with the <b>female</b> end of a jumper. Most modules have pins too, so a female–female jumper goes straight from the ESP32 to the module.</p></div>
</div>
<h3>Wire colours used here</h3>
<div class="legend"><span><i style="background:{COL['3v3']}"></i>3.3 V</span><span><i style="background:{COL['5v']}"></i>5 V</span><span><i style="background:{COL['gnd']}"></i>ground (GND)</span><span><i style="background:linear-gradient(90deg,{COL['yellow']},{COL['green']},{COL['blue']},{COL['purple']})"></i>signals</span></div>
<p>Your jumpers can be any colour, but sticking to red for 5 V, orange (or another one colour) for 3.3 V and black for ground makes mistakes easy to spot.</p>
<div class="warn">⚠️ <b>Golden rules.</b> Unplug the USB cable (and later the 5 V adapter) every time you change wires. Keep the ESP32 on your computer's USB the whole time and <b>never</b> connect the 5 V adapter to its <b>5V</b> pin. Make sure the two ground rails stay joined.</div>
<p>You'll also want the two small 6 × 6 mm push buttons from your tactile switch kit; the 16 mm panel buttons need soldering, so they go in during final assembly.</p>
{''.join(out)}

<section class="bbstep" id="s-optics">
  <div class="bbhead"><span class="num">★</span><h2>Bonus: see it on the ceiling</h2><span class="time">⏱ 15 min</span></div>
  <p>Once the LCD has its window cut (<a href="assembly.html#step-5">assembly step 5</a>), you can try the projector by hand in a dark room before printing anything.</p>
  <div class="two"><div>{svg_optics()}</div><div><ol class="todo">
  <li>Point the LED up, sitting on its metal.</li>
  <li>Hold a piece of baking paper about 10 mm above it, and the LCD, glass up, about 30 mm above it.</li>
  <li>Hold the lens about 106 mm above the LCD, look at the ceiling, and move the lens up and down until the digits are sharp. That's what the focus ring does in the finished clock.</li>
  <li>Use <b>Mirror left/right</b> and <b>Flip projection</b> on the clock's page until it reads right from where you lie. In the clock the mirror adds one more flip, so expect to change Mirror left/right once it's built.</li></ol></div></div>
</section>

<h2>Done?</h2>
<p>When every step passes, move the same connections onto the perfboard (<a href="assembly.html#step-4">assembly step 4</a>). Two things change in the finished clock: the 16 mm buttons replace the small ones, and the 5 V supply also feeds the ESP32's 5V pin, so from then on leave the computer unplugged and update the firmware over Wi-Fi. The full pin list is on the <a href="wiring.html">wiring page</a>.</p>
</main>
<footer>Ceiling Clock · pictures drawn from <a href="https://github.com/ScottYates/ceilingclock/blob/main/firmware/src/pins.h">pins.h</a> by <code>hardware/make_breadboard_guide.py</code></footer>
<script>
(() => {{
  const KEY = 'ceilingclock-breadboard';
  let saved = {{}};
  try {{ saved = JSON.parse(localStorage.getItem(KEY) || '{{}}'); }} catch (e) {{}}
  const boxes = [...document.querySelectorAll('.wires input')];
  function update() {{
    const done = boxes.filter(b => b.checked).length;
    document.getElementById('pbar').style.width = (100 * done / boxes.length) + '%';
    document.getElementById('ptext').textContent = done + ' of ' + boxes.length + ' wires connected';
    document.querySelectorAll('.bbstep').forEach((s, i) => {{
      const bs = [...s.querySelectorAll('.wires input')];
      const ok = bs.length > 0 && bs.every(b => b.checked);
      s.classList.toggle('done', ok);
      const t = document.querySelectorAll('#toc a')[i]; if (t) t.classList.toggle('done', ok);
    }});
  }}
  boxes.forEach(b => {{
    b.checked = !!saved[b.dataset.k];
    b.onchange = () => {{ saved[b.dataset.k] = b.checked; try {{ localStorage.setItem(KEY, JSON.stringify(saved)); }} catch (e) {{}} update(); }};
  }});
  // hover a wire in the list or the picture to highlight both
  const hl = (id, on) => document.querySelectorAll('[data-w="' + id + '"]').forEach(e => e.classList.toggle('hl', on));
  document.querySelectorAll('[data-w]').forEach(e => {{
    e.addEventListener('mouseenter', () => hl(e.dataset.w, true));
    e.addEventListener('mouseleave', () => hl(e.dataset.w, false));
  }});
  update();
}})();
</script>
</body></html>'''

if __name__ == '__main__':
    out = os.path.join(HERE, '..', 'docs', 'breadboard.html')
    open(out, 'w').write(page())
    print('wrote', os.path.relpath(out), '-', len(STEPS), 'steps,', sum(len(s['wires']) for s in STEPS), 'wires')
