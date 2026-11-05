# PlatformIO extra script: stamps the build time (US Central) into the firmware, so the clock's page shows
# which build it is running. Shown as "Firmware <FW_VERSION> · built <FW_BUILD>".
Import("env")
from datetime import datetime
try:
    from zoneinfo import ZoneInfo
    now = datetime.now(ZoneInfo("America/Chicago"))
except Exception:
    now = datetime.now()
stamp = now.strftime("%b %-d %Y %-I:%M %p")
env.Append(CPPDEFINES=[("FW_BUILD", '\\"%s\\"' % stamp)])
