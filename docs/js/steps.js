// Assembly steps. Each step drives the 3D view (visible parts, highlighted parts,
// explode amount, camera) and the instructions on assembly.html.
// Cameras are in three.js coordinates: (model x, model z, -model y).
const ELEC = ['ref_perfboard', 'ref_esp32', 'ref_amp', 'ref_rtc', 'ref_mosfet'];
const ENGINE = ['carriage', 'ref_led', 'ref_diffuser', 'ref_lcd'];
const PRINTED = ['base', 'lid', 'lightbox', 'carriage', 'lens_mount', 'sleeve', 'lens_cap', 'ring_holder', 'dome', 'pins_asm'];

const s1 = ['base', 'ref_speaker'];
const s2 = [...s1, 'ref_tm1637', 'ref_window', 'ref_usbc', 'ref_buttonB'];
const s4 = [...s2, 'lightbox', 'ref_mirror', ...ENGINE];
const s5 = [...s4, ...ELEC];
const s6 = [...s5, 'lid', 'ref_button', 'ref_ldr', 'pins_asm'];
const s7 = [...s6, 'lens_mount', 'sleeve', 'ref_lens', 'lens_cap'];
const s8 = [...s7, 'ring_holder', 'ref_ring', 'dome', 'ref_wires'];

const ISO = { camera: [300, 250, 390], target: [0, 40, 0] };

export const STEPS = [
  {
    title: 'Print the parts',
    view: { visible: PRINTED, highlight: [], explode: 0.75, camera: [420, 380, 560], target: [0, 120, 0] },
    html: `<p>Print the ten files in <code>hardware/stl/</code>. They are already in printing orientation. The case needs <b>no screws</b>: printed snap pins hold the lid, lens mount and ring holder, and the circuit board snaps under printed hooks.</p>
<table><thead><tr><th>Part</th><th>Material</th><th>Notes</th></tr></thead><tbody>
<tr><td>base.stl</td><td>PLA/PETG, black or dark grey</td><td>170 × 120 × 64 mm. 0.2 mm layers, 3 walls, 15% infill. The display rails need no supports. For a 0.56" display, print <code>base_056.stl</code> instead.</td></tr>
<tr><td>lid.stl</td><td>Same as base</td><td>Prints flat, no supports.</td></tr>
<tr><td>lightbox.stl</td><td><b>Black</b> PLA/PETG</td><td>Must be opaque, or light leaks into the case. Prints upright with the mirror ramp inside; no supports.</td></tr>
<tr><td>carriage.stl</td><td>PETG preferred</td><td>Holds the LED, so PETG copes with the warmth better.</td></tr>
<tr><td>lens_mount.stl</td><td>Black</td><td>Flange down, no supports.</td></tr>
<tr><td>sleeve.stl</td><td>Black</td><td>Prints lens-seat face down.</td></tr>
<tr><td>lens_cap.stl</td><td>Any</td><td>3 mm ring that traps the lens.</td></tr>
<tr><td>ring_holder.stl</td><td>Any</td><td>—</td></tr>
<tr><td>dome.stl</td><td>White or natural PLA</td><td>Vase mode or 2 walls, 0% infill, so it glows evenly.</td></tr>
<tr><td>pins.stl</td><td><b>PETG</b> (or PLA)</td><td>12 snap pins (9 needed, 3 spares) and 2 focus pins, lying on their flats. Use <b>100% infill</b> and 0.12–0.16 mm layers. PETG flexes without snapping.</td></tr>
</tbody></table>
<p>Total print time is about 12–15 hours, mostly the base and lid. The base needs a bed of at least 180 × 130 mm; everything else is smaller.</p>`,
  },
  {
    title: 'Fit the speaker',
    view: { visible: s1, highlight: ['ref_speaker'], explode: 0, camera: [-170, 250, 230], target: [-45, 5, 15] },
    html: `<ol>
<li>Solder 15 cm leads to the speaker.</li>
<li>Press it cone-down into the round retaining ring on the base floor (front left), over the grille holes.</li>
<li>Run a thin bead of hot glue around the rim. This seals it so the sound goes out through the grille, not into the box.</li></ol>`,
  },
  {
    title: 'Front display and side panel',
    view: { visible: s2, highlight: ['ref_tm1637', 'ref_window', 'ref_usbc', 'ref_buttonB'], explode: 0.35, camera: [-330, 190, 300], target: [-30, 30, 15] },
    html: `<ol>
<li>Cut a 31 × 15 mm piece of 2 mm red or smoked acrylic and glue it into the front window, flush with the outside. It makes the digits darker and nicer at night. Tinted film stuck on the outside works too.</li>
<li>Solder a 4-pin lead to the TM1637 module, then slide its PCB down into the two slotted rails behind the window, digits facing out. The left rail has a notch for the module's header. The rails fit the 42 × 24 mm board of a 0.36" module. If you're using a 0.56" module, print <code>base_056.stl</code> instead of <code>base.stl</code>.</li>
<li>Glue the USB-C breakout onto its cradle on the <b>left side wall</b> so the socket lines up with the slot. Solder red/black leads to VBUS/GND.</li>
<li>Fit the second 16 mm button (button B) into the round hole in the left side wall, above the USB-C slot.</li></ol>`,
  },
  {
    title: 'Build the light engine',
    view: { visible: [...s2, 'lightbox', 'ref_mirror', ...ENGINE], highlight: ENGINE, explode: 0.6, camera: [-230, 300, 260], target: [-40, 90, -30] },
    html: `<p>The carriage holds, from back to front: the LED, a diffuser, and the LCD. Light shines forward through the LCD toward the mirror.</p>
<ol>
<li><b>LED:</b> solder two 15 cm leads to the star, then stick it into the round pocket on the inside of the carriage's back plate with thermal tape or a dab of thermal glue, LED facing forward. Feed the leads up through the small hole in the top plate.</li>
<li><b>Diffuser:</b> cut a 46 × 46 mm square of frosted plastic (or two layers of baking paper) and drop it into the first slot from the top.</li>
<li><b>Prepare the LCD:</b> the Nokia 5110's own circuit board sits behind the glass and blocks light, so it needs a window:
  <ul>
  <li>Bend up the four metal tabs and lift off the frame, glass and white light guide. Keep the rubber zebra strips clean and in place.</li>
  <li>Discard the light guide. Mark the active pixel area (about 30 × 22 mm) on the board, centred under where the glass sits.</li>
  <li>Check both sides of the board in that area. If a trace crosses it, bridge it later with thin wire. Then cut the window with a rotary tool and file it smooth.</li>
  <li>Refit the glass and frame, and bend the tabs back. Plug it into the ESP32 and check the display still works before going further.</li>
  </ul></li>
<li>Mask the glass border with black electrical tape so only the pixel area lets light through.</li>
<li>Drop the LCD board into the front slot, <b>glass facing forward</b> (away from the LED), header at the top. Plug an 8-wire lead onto the header.</li></ol>`,
  },
  {
    title: 'Mirror and light box',
    view: { visible: s4, highlight: ['lightbox', 'ref_mirror', ...ENGINE], explode: 0.3, camera: [150, 420, 170], target: [5, 30, -30] },
    html: `<ol>
<li>Peel the protective film off the mirror only now, holding it by the edges. The coating is on the front, so any fingerprint shows up on the ceiling. Clean it, if needed, with a puff of air or a lens tissue.</li>
<li>Put two short strips of thin double-sided tape on the 45° ramp at the right-hand end of the light box. Lay the mirror on them, <b>shiny side up</b>, with its lower edge against the stop at the bottom of the ramp.</li>
<li>Lower the carriage into the left-hand end of the light box until it sits on the floor between the back wall and the two small ribs.</li>
<li>Set the light box into the base along the back wall so the two pegs in the floor go into the holes underneath. Lead the LED and LCD wires out through the notch at the top of its front wall.</li></ol>
<p>The lid closes the top of the light box, so nothing else holds it.</p>`,
  },
  {
    title: 'Build the electronics board',
    view: { visible: s5, highlight: ELEC, explode: 0.6, camera: [240, 330, 270], target: [30, 40, 15] },
    html: `<p>Use a 70 × 50 mm perfboard. Follow the <a href="wiring.html">wiring page</a> for every connection.</p>
<ol>
<li>Solder two rows of female headers so the ESP32-S3 board plugs in rather than being soldered. That way you can replace or reflash it easily.</li>
<li>Add the 5 V and GND rails, the 1000 µF capacitor (for the LED ring) and the 100 µF capacitor (by the amplifier). Solder the 4.7 Ω 2 W LED resistor here too, standing a few millimetres off the board so air can reach it.</li>
<li>The MAX98357A, DS3231 and MOSFET module sit on the base floor in front of the board, on short leads.</li>
<li>Bring every off-board connection to a pin header along the board's left edge: LCD, LED, ring, display, speaker, buttons, LDR, power. Then each wire plugs in during final assembly.</li>
<li><b>Test before mounting:</b> flash the firmware (see <a href="firmware.html">Firmware</a>), check the web page loads and "Ring now" beeps.</li>
<li>Press the board down onto the four corner pads (front right of the base) until the four hooks on its short edges click over it. To remove it, ease the hooks outward with a fingernail.</li></ol>`,
  },
  {
    title: 'Lid and snooze button',
    view: { visible: s6, highlight: ['lid', 'ref_button', 'ref_ldr', 'pins_asm'], explode: 0.4, camera: [300, 330, 380], target: [0, 90, 0] },
    html: `<ol>
<li>Push the 16 mm snooze button through the hole near the front of the lid and tighten its nut.</li>
<li>Glue the LDR into the small hole at the front-right corner, with its face flush with the top.</li>
<li>Thread the ring leads up through the lid's centre hole on the left before closing it.</li>
<li>Set the lid on the base and push a snap pin into each corner hole until it clicks and the head sits flush. To open the case later, pull the pins with pliers; they're reusable, and there are spares.</li></ol>`,
  },
  {
    title: 'Lens mount and lens',
    view: { visible: s7, highlight: ['lens_mount', 'sleeve', 'ref_lens', 'lens_cap'], explode: 0.3, camera: [250, 300, 240], target: [40, 110, -30] },
    html: `<ol>
<li>Set the lens mount over the round hole at the back right of the lid, focus-pin hole facing the front. Push a snap pin through each of its two tabs until it clicks.</li>
<li>Drop the 50 mm lens into the round seat at the top of the sleeve. Glue the lens cap on top with three small dots of glue, keeping glue off the glass.</li>
<li>Slide the sleeve, lens end up, into the lens mount. Leave the focus pin out for now; it goes in after focusing.</li></ol>`,
  },
  {
    title: 'Sunrise light',
    view: { visible: s8, highlight: ['ring_holder', 'ref_ring', 'dome'], explode: 0.4, camera: [-280, 280, 300], target: [-45, 90, 20] },
    html: `<ol>
<li>Solder three leads (5V, GND, DIN) to the ring's input pads and feed them down through the centre hole of the holder and the lid.</li>
<li>Press the ring LEDs-up into the holder pocket.</li>
<li>Fix the holder to the lid with three snap pins through the holes inside the ring.</li>
<li>Press the dome into the groove around the holder. A dab of glue holds it if it's loose.</li></ol>`,
  },
  {
    title: 'Focus and finish',
    view: { visible: s8, highlight: [], explode: 0, ...ISO },
    html: `<ol>
<li>Plug in the 5 V supply. The projector shows <code>WIFI SETUP</code> until you connect it (see <a href="firmware.html">Firmware</a>).</li>
<li>Darken the room. Slide the lens sleeve up and down (about ±5 mm of travel) until the digits on the ceiling are sharp, then push the tapered focus pin into the hole at the front of the lens mount to lock it.</li>
<li>The mirror flips the image once. If the time reads mirrored or upside down, fix it with <b>Mirror left/right</b> and <b>Flip upside down</b> on the settings page.</li>
<li>Adjust <b>LCD contrast</b> until the background is as dark as it gets without the digits fading.</li></ol>
<p>With a 100 mm lens and a 1.8 m throw (8 ft ceiling, nightstand height), expect an image about 50 cm wide. The clock stands about 9 cm tall.</p>`,
  },
];
