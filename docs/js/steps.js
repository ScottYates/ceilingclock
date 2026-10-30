// Assembly steps. Each step drives the 3D view (visible parts, highlighted parts,
// explode amount, projector tilt, camera) and the instructions on assembly.html.
// Cameras are in three.js coordinates: (model x, model z, -model y).
const ELEC = ['ref_perfboard', 'ref_esp32', 'ref_amp', 'ref_rtc', 'ref_mosfet'];
const BARREL = ['barrel', 'ref_mirror', 'lcd_holder', 'ref_lcd', 'lens_mount', 'pins_barrel', 'sleeve', 'ref_lens', 'lens_cap'];
const CAP = ['led_cap', 'ref_led', 'ref_diffuser'];
const PRINTED = ['base', 'lid', 'barrel', 'lcd_holder', 'led_cap', 'lens_mount', 'sleeve', 'lens_cap', 'ring_holder', 'dome', 'pins_asm', 'pins_barrel'];

const s1 = ['base', 'ref_speaker'];
const s2 = [...s1, 'ref_tm1637', 'ref_window', 'ref_usbc', 'ref_buttonB'];
const s3 = [...s2, ...ELEC];
const s6 = [...s3, ...BARREL, ...CAP];
const s7 = [...s6, 'lid', 'ref_button', 'ref_ldr', 'pins_asm'];
const s8 = [...s7, 'ring_holder', 'ref_ring', 'dome', 'ref_wires'];

export const STEPS = [
  {
    title: 'Print the parts',
    view: { visible: PRINTED, highlight: [], explode: 0.75, camera: [420, 380, 560], target: [0, 100, 0] },
    html: `<p>Print the eleven files in <code>hardware/stl/</code>. They are already in printing orientation. The case needs <b>no screws</b>: printed snap pins hold the lid, LED cap, lens mount and ring holder, and the circuit board snaps under printed hooks.</p>
<table><thead><tr><th>Part</th><th>Material</th><th>Notes</th></tr></thead><tbody>
<tr><td>base.stl</td><td>PLA/PETG, black or dark grey</td><td>170 × 135 × 44 mm (56 mm at the bearing). 0.2 mm layers, 3 walls, 15% infill. No supports. For a 0.56" display, print <code>base_056.stl</code> instead.</td></tr>
<tr><td>lid.stl</td><td>Same as base</td><td>Prints flat, no supports.</td></tr>
<tr><td>barrel.stl</td><td><b>Black</b> PLA/PETG</td><td>Must be opaque. Stands on its open end; the mirror ramp inside is a 45° slope, so no supports.</td></tr>
<tr><td>lcd_holder.stl</td><td>Black</td><td>Prints flat.</td></tr>
<tr><td>led_cap.stl</td><td>Black PETG preferred</td><td>Holds the LED, so PETG copes with the warmth better. Stands on its collar.</td></tr>
<tr><td>lens_mount.stl</td><td>Black</td><td>The threaded collar. Prints upside down, no supports; 0.16 mm layers.</td></tr>
<tr><td>sleeve.stl</td><td>Black</td><td>The threaded focus ring. Prints grip-down, no supports. Use 0.16 mm layers so the thread comes out smooth.</td></tr>
<tr><td>lens_cap.stl</td><td>Any</td><td>3 mm ring that traps the lens.</td></tr>
<tr><td>ring_holder.stl</td><td>Any</td><td>—</td></tr>
<tr><td>dome.stl</td><td>White or natural PLA</td><td>Vase mode or 2 walls, 0% infill, so it glows evenly.</td></tr>
<tr><td>pins.stl</td><td><b>PETG</b> (or PLA)</td><td>12 snap pins (10 needed, 2 spares), lying on their flats. Use <b>100% infill</b> and 0.12–0.16 mm layers. PETG flexes without snapping.</td></tr>
</tbody></table>
<p>Total print time is about 12–15 hours. The base needs a bed of at least 180 × 145 mm; everything else is smaller.</p>`,
  },
  {
    title: 'Fit the speaker',
    view: { visible: s1, highlight: ['ref_speaker'], explode: 0, camera: [-170, 250, 220], target: [-48, 5, 30] },
    html: `<ol>
<li>Solder 15 cm leads to the speaker.</li>
<li>Press it cone-down into the round retaining ring on the base floor (front left), over the grille holes.</li>
<li>Run a thin bead of hot glue around the rim. This seals it so the sound goes out through the grille, not into the box.</li></ol>`,
  },
  {
    title: 'Front display and side panel',
    view: { visible: s2, highlight: ['ref_tm1637', 'ref_window', 'ref_usbc', 'ref_buttonB'], explode: 0.35, camera: [-330, 190, 260], target: [-30, 25, 25] },
    html: `<ol>
<li>Cut a 31 × 15 mm piece of 2 mm red or smoked acrylic and glue it into the front window, flush with the outside. It makes the digits darker and nicer at night. Tinted film stuck on the outside works too.</li>
<li>Solder a 4-pin lead to the TM1637 module, then slide its PCB down into the two slotted rails behind the window, digits facing out. The left rail has a notch for the module's header. The rails fit the 42 × 24 mm board of a 0.36" module. If you're using a 0.56" module, print <code>base_056.stl</code> instead of <code>base.stl</code>.</li>
<li>Glue the USB-C breakout onto its cradle on the <b>left side wall</b> so the socket lines up with the slot. Solder red/black leads to VBUS/GND.</li>
<li>Fit the second 16 mm button (button B) into the round hole lower down on the left side wall.</li></ol>`,
  },
  {
    title: 'Build the electronics board',
    view: { visible: s3, highlight: ELEC, explode: 0.6, camera: [240, 320, 300], target: [25, 30, 25] },
    html: `<p>Use a 70 × 50 mm perfboard. Follow the <a href="wiring.html">wiring page</a> for every connection.</p>
<ol>
<li>Solder two rows of female headers so the ESP32-S3 board plugs in rather than being soldered. That way you can replace or reflash it easily.</li>
<li>Add the 5 V and GND rails, the 1000 µF capacitor (for the LED ring) and the 100 µF capacitor (by the amplifier). Solder the 4.7 Ω 2 W LED resistor here too, standing a few millimetres off the board so air can reach it.</li>
<li>The MAX98357A and DS3231 sit on the floor in front of the board, and the MOSFET module at the back left beside the LED cap, all on short leads.</li>
<li>Bring every off-board connection to a pin header along the board's left edge: LCD, LED, ring, display, speaker, buttons, LDR, power. Then each wire plugs in during final assembly.</li>
<li><b>Test before mounting:</b> flash the firmware (see <a href="firmware.html">Firmware</a>), check the web page loads and "Ring now" beeps.</li>
<li>Press the board down onto the four corner pads (front right of the base) until the four hooks on its short edges click over it. To remove it, ease the hooks outward with a fingernail.</li></ol>`,
  },
  {
    title: 'LCD and its holder',
    view: { visible: [...s3, 'lcd_holder', 'ref_lcd'], highlight: ['lcd_holder', 'ref_lcd'], explode: 0.5, camera: [-250, 230, 220], target: [-35, 85, -30] },
    html: `<p>The Nokia 5110's own circuit board sits behind the glass and blocks light, so it needs a window:</p>
<ol>
<li>Bend up the four metal tabs and lift off the frame, glass and white light guide. Keep the rubber zebra strips clean and in place.</li>
<li>Discard the light guide. Mark the active pixel area (about 30 × 22 mm) on the board, centred under where the glass sits.</li>
<li>Check both sides of the board in that area. If a trace crosses it, bridge it later with thin wire. Then cut the window with a rotary tool and file it smooth.</li>
<li>Refit the glass and frame, and bend the tabs back. Plug it into the ESP32 and check the display still works before going further.</li>
<li>Mask the glass border with black electrical tape so only the pixel area lets light through.</li>
<li>Plug a 30 cm 8-wire lead onto the header. Drop the board into the slot in the LCD holder, <b>glass facing away from the round recess</b>, header to the side, so the display's long side runs up and down.</li></ol>`,
  },
  {
    title: 'Barrel: mirror, LCD and lens',
    view: { visible: [...s3, ...BARREL], highlight: BARREL, explode: 0.35, camera: [250, 300, 320], target: [20, 90, -30] },
    html: `<p>The barrel carries the LCD, the mirror and the lens, so they stay lined up when you tilt it.</p>
<ol>
<li>Peel the protective film off the mirror only now, holding it by the edges. The coating is on the front, so any fingerprint shows up on the ceiling.</li>
<li>Put two short strips of thin double-sided tape on the 45° ramp inside the barrel's closed (right) end. Slide the mirror in from the open end, <b>shiny side up</b>, and press it onto the tape with its lower edge against the stop.</li>
<li>Push the LCD holder into the open end, key at the bottom, until it's flush. Feed the LCD lead out through the slot low on the barrel's front side.</li>
<li>Set the lens mount (the threaded collar) on top of the barrel, slotted tongue toward the back, and push a snap pin through each of its two tabs.</li>
<li>Drop the 50 mm lens into the seat in the top of the focus ring, and glue the lens cap on with three small dots (keep glue off the glass).</li>
<li>Screw the focus ring into the collar, clockwise, about three turns, until its grip is roughly 5 mm above the collar. That's close to focused for an 8 ft ceiling. The thread is coarse (3 mm per turn) so it starts easily; if it's stiff, run it in and out a few times.</li></ol>`,
  },
  {
    title: 'LED cap and fitting the barrel',
    view: { visible: s6, highlight: [...CAP, 'barrel'], explode: 0.4, camera: [-330, 250, 160], target: [-40, 50, -30] },
    html: `<ol>
<li>Solder two 20 cm leads to the LED star, then stick it into the round pocket inside the cap's back with thermal tape or a dab of thermal glue, LED facing the open end. Lead the wires out through the small hole below it.</li>
<li>Cut a 48 mm disc of frosted plastic (or two layers of baking paper) and drop it into the slot in the top of the cap.</li>
<li>Lower the barrel into the base, then slide it right so its axle goes into the hole in the bearing block in the back-right corner.</li>
<li>Slide the LED cap's collar into the barrel's open left end and let the cap settle onto its saddle. The barrel is now held at both ends and can't slide out.</li>
<li>Connect the LED to the MOSFET module, and the LCD lead to the board. Leave a loose loop in the LCD lead so the barrel can turn.</li></ol>`,
  },
  {
    title: 'Lid and snooze button',
    view: { visible: s7, highlight: ['lid', 'ref_button', 'ref_ldr', 'pins_asm'], explode: 0.3, camera: [300, 330, 400], target: [0, 60, 0] },
    html: `<ol>
<li>Push the 16 mm snooze button through the hole near the front of the lid and tighten its nut.</li>
<li>Glue the LDR into the small hole at the front-right corner, with its face flush with the top.</li>
<li>Thread the ring leads up through the lid's centre hole on the left before closing it.</li>
<li>Lay the lid on so the barrel and LED cap sit in its cut-out. Push a snap pin into each of the three corner holes, and two more through the LED cap's tabs, until they click.</li></ol>`,
  },
  {
    title: 'Sunrise light',
    view: { visible: s8, highlight: ['ring_holder', 'ref_ring', 'dome'], explode: 0.4, camera: [-280, 260, 320], target: [-50, 60, 35] },
    html: `<ol>
<li>Solder three leads (5V, GND, DIN) to the ring's input pads and feed them down through the centre hole of the holder and the lid.</li>
<li>Press the ring LEDs-up into the holder pocket.</li>
<li>Fix the holder to the lid with three snap pins through the holes inside the ring.</li>
<li>Press the dome into the groove around the holder. A dab of glue holds it if it's loose.</li></ol>`,
  },
  {
    title: 'Focus, aim and finish',
    view: { visible: s8, highlight: [], explode: 0, tilt: 20, beam: true, camera: [2500, 450, 2900], target: [0, 1000, 250] },
    html: `<ol>
<li>Plug in the 5 V supply. The projector shows <code>WIFI SETUP</code> until you connect it (see <a href="firmware.html">Firmware</a>).</li>
<li><b>Aim:</b> hold the lens mount and roll the barrel toward the front. It clicks every 5°, from 5° back to 30° forward; the grooves on the barrel's right end show the steps. The picture turns with the barrel, so the time stays straight.</li>
<li><b>Focus:</b> darken the room and turn the knurled focus ring on top of the lens. Clockwise (seen from above) lowers the lens and focuses further away; anticlockwise raises it and focuses closer. The arrows on the ring show the way. One turn moves the lens 3 mm, and about ±1½ turns from the middle covers any normal ceiling. The thread holds wherever you leave it, and a springy tongue in the collar stops it creeping. Tilting further sends the light further, so give it a small turn after a big change. On the <a href="index.html">3D model</a> page, "Show focusing" plays this.</li>
<li>If the time reads upside down from where you lie, press <b>Flip projection</b> on the clock's web page (or tick <b>Upside down</b> in the projector settings). If it reads back to front, tick <b>Mirror left/right</b>. The "Flip upside down" button on the <a href="index.html">3D model</a> page shows what it does.</li>
<li>Adjust <b>LCD contrast</b> until the background is as dark as it gets without the digits fading.</li></ol>
<table><thead><tr><th>Tilt</th><th>0°</th><th>10°</th><th>15°</th><th>20°</th><th>25°</th><th>30°</th></tr></thead><tbody>
<tr><td>Image moves forward (8 ft ceiling, 1.8 m above the clock)</td><td>0</td><td>32 cm</td><td>48 cm</td><td>66 cm</td><td>84 cm</td><td>104 cm</td></tr></tbody></table>
<p>The image is about 50 cm wide straight up and grows a little with tilt; at 30° its far edge is about 15% wider than its near edge. The clock stands about 11 cm tall at the focus ring.</p>`,
  },
];
