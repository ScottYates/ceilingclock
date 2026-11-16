"""Fail if the browser build needs a function the demo page (docs/demo/sim.js) doesn't provide.
The browser only reports a missing one when the demo loads, so this catches it at build time."""
import re, sys
wasm, js = sys.argv[1], open(sys.argv[2]).read()
b = open(wasm, 'rb').read()
def leb(i):
    r = s = 0
    while True:
        x = b[i]; i += 1; r |= (x & 0x7f) << s; s += 7
        if x < 0x80: return r, i
i, needed = 8, []
while i < len(b):
    sid = b[i]; n, i = leb(i + 1); end = i + n
    if sid == 2:   # import section
        c, i = leb(i)
        for _ in range(c):
            l, i = leb(i); i += l
            l, i = leb(i); needed.append(b[i:i + l].decode()); i += l
            kind = b[i]; i += 1
            if kind == 0: _, i = leb(i)
            else: sys.exit(f'unexpected import kind {kind}')
    i = end
provided = set(re.findall(r'^\s+([A-Za-z_]\w*)\s*:', js, re.M))
missing = [f for f in needed if f not in provided]
if missing:
    sys.exit(f'{wasm} needs {", ".join(missing)}, which {sys.argv[2]} does not provide')
print(f'browser build: all {len(needed)} imports provided by the page')
