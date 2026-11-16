// Assembly steps. Each step drives the 3D view (visible parts, highlighted parts,
// explode amount, projector tilt, camera) and the instructions on assembly.html.
// Cameras are in three.js coordinates: (model x, model z, -model y).
const ELEC = ['ref_perfboard', 'ref_esp32', 'ref_amp', 'ref_rtc'];
const BARREL = ['barrel', 'ref_mirror', 'disp_holder', 'ref_projdisp', 'lens_mount', 'pins_barrel', 'sleeve', 'ref_lens', 'lens_cap'];
const CAP = ['end_cap'];
const PRINTED = ['base', 'lid', 'barrel', 'disp_holder', 'end_cap', 'lens_mount', 'sleeve', 'lens_cap', 'pins_asm', 'pins_barrel'];

const s1 = ['base', 'ref_speaker'];
const s2 = [...s1, 'ref_tm1637', 'ref_window', 'ref_usbc', 'ref_buttonB'];
const s3 = [...s2, ...ELEC];
const s6 = [...s3, ...BARREL, ...CAP];
const s7 = [...s6, 'lid', 'ref_button', 'ref_alarmbtns', 'ref_ldr', 'pins_asm'];
const s8 = [...s7, 'ref_wires'];

export const STEPS = [
  {
    title: 'Print the parts',
    view: { visible: PRINTED, highlight: [], explode: 0.75, camera: [420, 380, 560], target: [0, 100, 0] },
    html: `<p>Print the nine files in <code>hardware/stl/</code>. They are already in printing orientation. The case needs <b>no screws</b>: printed quarter-turn lock pins hold the lid, end cap and lens mount, and the circuit board snaps under printed hooks.</p>
<table><thead><tr><th>Part</th><th>Material</th><th>Notes</th></tr></thead><tbody>
<tr><td>base.stl</td><td>PLA/PETG, black or dark grey</td><td>170 × 135 × 44 mm (56 mm at the bearing). 0.2 mm layers, 3 walls, 15% infill. No supports. For a 0.56" display, print <code>base_056.stl</code> instead.</td></tr>
<tr><td>lid.stl</td><td>Same as base</td><td>Prints flat, <b>top face down</b> (as exported): the pins' ramps are on its underside. The top gets the smooth bed finish.</td></tr>
<tr><td>barrel.stl</td><td><b>Black</b> PLA/PETG</td><td>Opaque, so room light doesn't wash out the picture. Stands on its open end; the mirror ramp inside is a 45° slope, so no supports.</td></tr>
<tr><td>disp_holder.stl</td><td>Black</td><td>Prints flat.</td></tr>
<tr><td>end_cap.stl</td><td>Black</td><td>Stands on its collar.</td></tr>
<tr><td>lens_mount.stl</td><td>Black</td><td>The threaded collar. Prints upside down, no supports; 0.16 mm layers.</td></tr>
<tr><td>sleeve.stl</td><td>Black</td><td>The threaded focus ring. Prints grip-down, no supports. Use 0.16 mm layers so the thread comes out smooth.</td></tr>
<tr><td>lens_cap.stl</td><td>Any</td><td>3 mm ring that traps the lens.</td></tr>
<tr><td>pins.stl</td><td><b>PETG</b> (or PLA)</td><td>Quarter-turn lock pins, heads down: 4 short (3 needed, for the lid corners) and 5 long (4 needed). Use <b>100% infill</b>, in PETG if you have it (it's tougher for the click). The small lug near each head is a 1.4 mm overhang, which prints fine.</td></tr>
</tbody></table>
<p>Total print time is about 11–13 hours. The base needs a bed of at least 180 × 145 mm; everything else is smaller.</p>`,
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
    html: `<p>Use a 70 × 50 mm perfboard cut down to <b>70 × 40</b>: score across it with a knife along a row of holes, four rows in from one long edge, and snap it. The alarm buttons hang down just in front of it. Follow the <a href="wiring.html">wiring page</a> for every connection.</p>
<ol>
<li>Solder two rows of female headers so the ESP32-S3 board plugs in rather than being soldered. That way you can replace or reflash it easily.</li>
<li>Add the 5 V and GND rails, the 100 µF capacitor by the amplifier, the 10 kΩ resistor for the light sensor, and the two 220 Ω resistors for the alarm buttons' lights. Keep the right-hand two thirds of the board's front edge (the edge toward the front of the clock) free of anything taller than 2.5 mm: the alarm buttons' bodies end just above it.</li>
<li>The MAX98357A and DS3231 sit on the floor in front of the board, on short leads.</li>
<li>Bring every off-board connection to a pin header along the board's left edge: both displays, speaker, buttons, LDR, power. The two alarm buttons' lights each need a 220 Ω resistor on the board, between the ESP32 pin (10 or 13) and the header. Then each wire plugs in during final assembly.</li>
<li><b>Test before mounting:</b> ideally build it all on a breadboard first (see <a href="breadboard.html">Breadboard test</a>). At least flash the firmware (see <a href="firmware.html">Firmware</a>), check the web page loads and "Ring now" beeps.</li>
<li>Press the board down onto the four corner pads (right half of the base), header side toward the back, until the four hooks on its short edges click over it. To remove it, ease the hooks outward with a fingernail.</li></ol>`,
  },
  {
    title: 'Projector display and its holder',
    view: { visible: [...s3, 'disp_holder', 'ref_projdisp'], highlight: ['disp_holder', 'ref_projdisp'], explode: 0.5, camera: [-250, 230, 220], target: [-35, 85, -30] },
    html: `<p>The projector is a second TM1637 display, the same as the front one. The lens images its glowing digits onto the ceiling, so nothing needs cutting or lighting.</p>
<ol>
<li>Plug a 40 cm 4-wire lead onto its header (CLK, DIO, VCC, GND), and label the CLK and DIO ends.</li>
<li>Drop the module into the slot in the display holder from the top, <b>digits facing away from the round recess</b> and the header at the top. The digits run up and down; that's right, the mirror turns them.</li>
<li>Check that the display body sits in the window and the board is flat against the slot.</li></ol>`,
  },
  {
    title: 'Barrel: mirror, display and lens',
    view: { visible: [...s3, ...BARREL], highlight: BARREL, explode: 0.35, camera: [250, 300, 320], target: [20, 90, -30] },
    html: `<p>The barrel carries the display, the mirror and the lens, so they stay lined up when you tilt it.</p>
<ol>
<li>Peel the protective film off the mirror only now, holding it by the edges. The coating is on the front, so any fingerprint shows up on the ceiling.</li>
<li>Put two short strips of thin double-sided tape on the 45° ramp inside the barrel's closed (right) end. Slide the mirror in from the open end, <b>shiny side up</b>, and press it onto the tape with its lower edge against the stop.</li>
<li>Push the display holder into the open end, key at the bottom, until it's flush. Let its lead hang out of the open end.</li>
<li>Set the lens mount (the threaded collar) on top of the barrel, slotted tongue toward the back, and lock it with a long pin through each of its two tabs: push in with the head along the slot, turn a quarter turn until it clicks.</li>
<li>Drop the 50 mm lens into the seat in the top of the focus ring, and glue the lens cap on with three small dots (keep glue off the glass).</li>
<li>Screw the focus ring into the collar, clockwise, about three turns, until its grip is roughly 5 mm above the collar. That's close to focused for an 8 ft ceiling. The thread is coarse (3 mm per turn) so it starts easily; if it's stiff, run it in and out a few times.</li></ol>`,
  },
  {
    title: 'End cap and fitting the barrel',
    view: { visible: s6, highlight: [...CAP, 'barrel'], explode: 0.4, camera: [-330, 250, 160], target: [-40, 50, -30] },
    html: `<ol>
<li>Thread the display's lead through the end cap, in at the collar and out through the slot low in its back.</li>
<li>Lower the barrel into the base, then slide it right so its axle goes into the hole in the bearing block in the back-right corner.</li>
<li>Slide the end cap's collar into the barrel's open left end and let the cap settle onto its saddle. The barrel is now held at both ends and can't slide out.</li>
<li>Pull the lead through until a short loop is left inside the cap, so the barrel can tilt, then run it along the floor to the board.</li></ol>`,
  },
  {
    title: 'Lid and buttons',
    view: { visible: s7, highlight: ['lid', 'ref_button', 'ref_alarmbtns', 'ref_ldr', 'pins_asm'], explode: 0.3, camera: [300, 330, 400], target: [0, 60, 0] },
    html: `<ol>
<li>Push the 16 mm snooze button through the hole at the front left of the lid, and the two lit alarm buttons through the pair of holes at the front right, well away from snooze so a sleepy hand doesn't switch an alarm off: <b>alarm 1 on the left</b>, alarm 2 on the right. Tighten the nuts.</li>
<li>Plug their leads onto the board's header: each alarm button has two switch wires and two light wires (the light's + goes to the 220 Ω resistor).</li>
<li>Glue the LDR into the small hole at the front-left corner, with its face flush with the top. (It's away from the alarm buttons, so their lights don't fool it.)</li>
<li>Lay the lid on so the barrel and end cap sit in its cut-out. Lock it with a short pin in each of the three corners and a long pin through each of the end cap's two tabs: push the pin in with its wing head <b>along</b> the slot beside the hole, then turn the head a quarter turn either way until it lies <b>crosswise</b> and clicks.</li></ol>`,
  },
  {
    title: 'Focus, aim and finish',
    view: { visible: s8, highlight: [], explode: 0, tilt: 20, beam: true, camera: [2500, 450, 2900], target: [0, 1000, 250] },
    html: `<ol>
<li>Plug in the 5 V supply. Both displays show <code>-- --</code> until the clock knows the time; connect it to Wi-Fi first (see <a href="firmware.html">Firmware</a>).</li>
<li><b>Aim:</b> hold the lens mount and roll the barrel toward the front. It clicks every 5°, from 5° back to 30° forward; the grooves on the barrel's right end show the steps. The picture turns with the barrel, so the time stays straight.</li>
<li><b>Focus:</b> darken the room (the projected digits are meant for the dark), set the projector's brightness to 7, and turn the knurled focus ring on top of the lens. Clockwise (seen from above) lowers the lens and focuses further away; anticlockwise raises it and focuses closer. The arrows on the ring show the way. One turn moves the lens 3 mm, and about ±1½ turns from the middle covers any normal ceiling. The thread holds wherever you leave it, and a springy tongue in the collar stops it creeping. Tilting further sends the light further, so give it a small turn after a big change. On the <a href="index.html">3D model</a> page, "Show focusing" plays this.</li>
<li>If the time reads upside down from where you lie, press <b>Flip projection</b> on the clock's web page (or tick <b>Upside down</b> in the projector settings). If it reads back to front, tick or untick <b>Mirror left/right</b>; if it's upside down only top to bottom, use <b>Mirror top/bottom</b>. The "Flip upside down" button on the <a href="index.html">3D model</a> page shows what it does.</li>
<li>Set the projector's night brightness on the web page: as low as still reads, so it doesn't light the room.</li></ol>
<table><thead><tr><th>Tilt</th><th>0°</th><th>10°</th><th>15°</th><th>20°</th><th>25°</th><th>30°</th></tr></thead><tbody>
<tr><td>Image moves forward (8 ft ceiling, 1.8 m above the clock)</td><td>0</td><td>32 cm</td><td>48 cm</td><td>66 cm</td><td>84 cm</td><td>104 cm</td></tr></tbody></table>
<p>The time is about 50 cm wide straight up (digits about 15 cm tall) and grows a little with tilt; at 30° its far edge is about 15% wider than its near edge. The clock stands about 11 cm tall at the focus ring.</p>`,
  },
];
