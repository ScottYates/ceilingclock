# PlatformIO extra script: patches the ESP32-audioI2S library so a web stream or web file waits until a
# set amount of audio is buffered before it starts playing (the library on its own starts after about 2 s,
# which runs dry on a weak Wi-Fi link). Adds Audio::setStartBuffer(ms, maxWaitMs). The patch is applied
# to the downloaded library before each build and does nothing if it is already there.
Import("env")
import os

MARK = "ceilingclock start buffer"
libdir = os.path.join(env.subst("$PROJECT_LIBDEPS_DIR"), env.subst("$PIOENV"), "ESP32-audioI2S", "src")
hpath, cpath = os.path.join(libdir, "Audio.h"), os.path.join(libdir, "Audio.cpp")


def swap(text, old, new, path):
    if text.count(old) != 1:
        raise SystemExit("patch_audio.py: expected text not found once in %s:\n%s" % (path, old))
    return text.replace(old, new)


if os.path.exists(hpath) and os.path.exists(cpath):
    h = open(hpath, encoding="utf-8").read()
    if MARK not in h:
        h = swap(h, "    bool             isRunning() { return m_f_running; }\n",
                 "    bool             isRunning() { return m_f_running; }\n"
                 "    // " + MARK + ": hold playback until this much audio is buffered, or maxWaitMs has passed\n"
                 "    void             setStartBuffer(uint32_t ms, uint32_t maxWaitMs) { m_startBufMs = ms; m_startMaxWaitMs = maxWaitMs; }\n"
                 "  private:\n"
                 "    uint32_t         m_startBufMs = 0, m_startMaxWaitMs = 0, m_startWaitBegin = 0;\n"
                 "    bool             startBufferReady();\n"
                 "  public:\n", hpath)
        open(hpath, "w", encoding="utf-8").write(h)

    c = open(cpath, encoding="utf-8").read()
    if MARK not in c:
        # the check itself, placed just before processWebFile()
        c = swap(c, "void Audio::processWebFile() {\n",
                 "// " + MARK + ": true once m_startBufMs of audio (at the stream's bitrate, or 128 kbps when not yet\n"
                 "// known) is in the input buffer, the buffer is three-quarters full, or m_startMaxWaitMs has passed.\n"
                 "bool Audio::startBufferReady() {\n"
                 "    if (!m_startBufMs) return true;\n"
                 "    if (!m_startWaitBegin) m_startWaitBegin = millis();\n"
                 "    uint32_t br = m_nominal_bitrate ? m_nominal_bitrate : 128000;\n"
                 "    uint64_t want = (uint64_t)br / 8 * m_startBufMs / 1000;\n"
                 "    uint64_t cap = (uint64_t)InBuff.getBufsize() * 3 / 4;\n"
                 "    if (want > cap) want = cap;\n"
                 "    size_t   have = InBuff.bufferFilled();\n"
                 "    uint32_t waited = millis() - m_startWaitBegin;\n"
                 "    if (have < want && waited < m_startMaxWaitMs) return false;\n"
                 "    info(*this, evt_info, \"start buffer {} bytes after {} ms\", (uint32_t)have, waited);\n"
                 "    return true;\n"
                 "}\n"
                 "void Audio::processWebFile() {\n", cpath)
        # web files (podcast episodes, MP3 links)
        c = swap(c, "        m_pwf.timeout = 8000; // ms\n",
                 "        m_pwf.timeout = 8000; // ms\n        m_startWaitBegin = 0; // " + MARK + "\n", cpath)
        c = swap(c, "                if (InBuff.bufferFilled() > 2 * InBuff.getMaxBlockSize()) {\n",
                 "                if (InBuff.bufferFilled() > 2 * InBuff.getMaxBlockSize() &&\n"
                 "                    (startBufferReady() || (m_audioFileSize && m_audioFilePosition >= m_audioFileSize))) { // " + MARK + "\n", cpath)
        # internet radio streams
        c = swap(c, "        m_pwst.chunkSize = 0;\n        m_metacount = m_metaint;\n",
                 "        m_pwst.chunkSize = 0;\n        m_metacount = m_metaint;\n        m_startWaitBegin = 0; // " + MARK + "\n", cpath)
        c = swap(c, "    if (((InBuff.bufferFilled() > m_pwst.maxFrameSize) || (m_f_allDataReceived)) && !m_f_stream) { // waiting for buffer filled\n",
                 "    if (((InBuff.bufferFilled() > m_pwst.maxFrameSize && startBufferReady()) || (m_f_allDataReceived)) && !m_f_stream) { // " + MARK + "\n", cpath)
        open(cpath, "w", encoding="utf-8").write(c)
