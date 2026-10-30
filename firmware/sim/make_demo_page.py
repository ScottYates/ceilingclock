"""Builds docs/demo/index.html from the firmware's own web page (src/web_ui.h).

The page is used unchanged; the only addition is sim.js, which runs the firmware
(docs/demo/ceilingclock.wasm) in the browser and answers the page's requests.
"""
import os, re
here = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(here, '..', 'src', 'web_ui.h'), encoding='utf-8').read()
html = re.search(r'R"rawliteral\((.*)\)rawliteral"', src, re.S).group(1)
html = html.replace('<title>Ceiling Clock</title>', '<title>Ceiling Clock (live demo)</title>', 1)
assert '<script>' in html
html = html.replace('<script>', '<script src="sim.js?v=2"></script>\n<script>', 1)
out = os.path.join(here, '..', '..', 'docs', 'demo', 'index.html')
open(out, 'w', encoding='utf-8').write(html)
print('wrote', os.path.relpath(out, here), len(html), 'bytes')
