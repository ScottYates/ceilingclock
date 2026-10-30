// Assembly steps. Each step drives the 3D view (visible parts, highlighted parts,
// explode amount, camera) and the instructions on assembly.html.
const ELEC = ['ref_perfboard', 'ref_esp32', 'ref_amp', 'ref_rtc', 'ref_mosfet'];
const PRINTED = ['base', 'lid', 'tower', 'carrier', 'sleeve', 'lens_cap', 'ring_holder', 'dome', 'pins_asm'];

const s1 = ['base', 'ref_speaker'];
const s2 = [...s1, 'ref_tm1637', 'ref_window', 'ref_usbc', 'ref_buttonB'];
const s3 = [...s2, ...ELEC];
const s4 = [...s3, 'lid', 'ref_button', 'ref_ldr', 'pins_asm'];
const s5 = [...s4, 'tower'];
const s6 = [...s5, 'carrier', 'ref_led', 'ref_diffuser', 'ref_lcd'];
const s7 = [...s6, 'sleeve', 'ref_lens', 'lens_cap'];
const s8 = [...s7, 'ring_holder', 'ref_ring', 'dome', 'ref_wires'];

const ISO = { camera: [360, 360, 540], target: [0, 120, 0] };

export const STEPS = [
  {
    title: 'Print the parts',
    view: { visible: PRINTED, highlight: [], explode: 0.75, camera: [470, 400, 690], target: [0, 160, 0] },
    html: `<p>Print the nine files in <code>hardware/stl/</code>. They are already in printing orientation. The case needs <b>no screws</b>: printed snap pins hold the lid, tower and ring holder, and the circuit board snaps under printed hooks.</p>
<table><thead><tr><th>Part</th><th>Material</th><th>Notes</th></tr></thead><tbody>
<tr><td>base.stl</td><td>PLA/PETG, black or dark grey</td><td>0.2 mm layers, 3 walls, 15% infill. The display rails need no supports. For a 0.56" display, print <code>base_056.stl</code> instead.</td></tr>
<tr><td>lid.stl</td><td>Same as base</td><td>Prints flat, no supports.</td></tr>
<tr><td>tower.stl</td><td><b>Black</b> PLA/PETG</td><td>Must be opaque, or the tower glows. Flange down, no supports.</td></tr>
<tr><td>carrier.stl</td><td>PETG preferred</td><td>Sits near the LED, so PETG copes with the warmth better.</td></tr>
<tr><td>sleeve.stl</td><td>Black</td><td>Prints lens-seat face down.</td></tr>
<tr><td>lens_cap.stl</td><td>Any</td><td>3 mm ring that traps the lens.</td></tr>
<tr><td>ring_holder.stl</td><td>Any</td><td>—</td></tr>
<tr><td>dome.stl</td><td>White or natural PLA</td><td>Vase mode or 2 walls, 0% infill, so it glows evenly.</td></tr>
<tr><td>pins.stl</td><td><b>PETG</b> (or PLA)</td><td>14 snap pins (11 needed, 3 spares) and 2 focus pins, lying on their flats. Use <b>100% infill</b> and 0.12–0.16 mm layers. PETG flexes without snapping.</td></tr>
</tbody></table>
<p>Total print time is about 14–18 hours, mostly the base and tower. Every part fits a 180 × 180 mm bed.</p>`,
  },
  {
    title: 'Fit the speaker',
    view: { visible: s1, highlight: ['ref_speaker'], explode: 0, camera: [-60, 330, 190], target: [-30, 0, -5] },
    html: `<ol>
<li>Solder 15 cm leads to the speaker.</li>
<li>Press it cone-down into the round retaining ring on the base floor, over the grille holes.</li>
<li>Run a thin bead of hot glue around the rim. This seals it so the sound goes out through the grille, not into the box.</li></ol>`,
  },
  {
    title: 'Front display and rear panel',
    view: { visible: s2, highlight: ['ref_tm1637', 'ref_window', 'ref_usbc', 'ref_buttonB'], explode: 0.35, camera: [-200, 180, 380], target: [0, 30, 0] },
    html: `<ol>
<li>Cut a 31 × 15 mm piece of 2 mm red or smoked acrylic and glue it into the front window, flush with the outside. It makes the digits darker and nicer at night. Tinted film stuck on the outside works too.</li>
<li>Solder a 4-pin lead to the TM1637 module, then slide its PCB down into the two slotted rails behind the window, digits facing out. The rails fit the 42 × 24 mm board of a 0.36" module. If you're using a 0.56" module, print <code>base_056.stl</code> instead of <code>base.stl</code>.</li>
<li>Glue the USB-C breakout onto its cradle so the socket lines up with the rear cutout. Solder red/black leads to VBUS/GND.</li>
<li>Fit a second 16 mm button (button B) into the round hole on the rear wall.</li></ol>`,
  },
  {
    title: 'Build the electronics board',
    view: { visible: s3, highlight: ELEC, explode: 0.6, camera: [120, 380, 260], target: [10, 40, 0] },
    html: `<p>Use a 70 × 50 mm perfboard. Follow the <a href="wiring.html">wiring page</a> for every connection.</p>
<ol>
<li>Solder two rows of female headers so the ESP32-S3 board plugs in rather than being soldered. That way you can replace or reflash it easily.</li>
<li>Mount the MAX98357A, DS3231 and MOSFET module on the board, or beside it on short leads.</li>
<li>Add the 5 V and GND rails, the 1000 µF capacitor (for the LED ring) and the 100 µF capacitor (by the amplifier). Solder the 4.7 Ω 2 W LED resistor here too, standing a few millimetres off the board so air can reach it.</li>
<li>Bring every off-board connection to a pin header: LCD, LED, ring, display, speaker, buttons, LDR, power. Then each wire plugs in during final assembly.</li>
<li><b>Test before mounting:</b> flash the firmware (see <a href="firmware.html">Firmware</a>), check the web page loads and "Ring now" beeps.</li>
<li>Press the board down onto the four corner pads until the four hooks along its long edges click over it. To remove it, ease the hooks outward with a fingernail.</li></ol>`,
  },
  {
    title: 'Lid and snooze button',
    view: { visible: s4, highlight: ['lid', 'ref_button', 'ref_ldr', 'pins_asm'], explode: 0.45, camera: [260, 300, 400], target: [0, 60, 0] },
    html: `<ol>
<li>Push the 16 mm snooze button through the front hole of the lid and tighten its nut.</li>
<li>Glue the LDR into the small hole at the front-left corner, with its face flush with the top.</li>
<li>Thread the LED, LCD and ring leads up through the lid openings before closing it.</li>
<li>Set the lid on the base and push a snap pin into each corner hole until it clicks and the head sits flush. To open the case later, pull the pins with pliers; they're reusable, and there are spares.</li></ol>`,
  },
  {
    title: 'Mount the projector tower',
    view: { visible: s5, highlight: ['tower'], explode: 0.4, camera: [320, 320, 480], target: [0, 120, 0] },
    html: `<ol>
<li>Set the tower over the square opening, with the flange flat on the lid.</li>
<li>Push a snap pin through each of the four flange holes. The barb clicks in under the lid.</li>
<li>Check the vents near the bottom face left and right. They let air flow past the LED.</li></ol>`,
  },
  {
    title: 'Build the light engine',
    view: { visible: s6.filter((n) => n !== 'tower'), highlight: ['carrier', 'ref_led', 'ref_diffuser', 'ref_lcd'], explode: 0.75, camera: [230, 230, 260], target: [30, 145, -8] },
    html: `<p>The carrier holds, from bottom to top: the LED, a diffuser, and the LCD.</p>
<ol>
<li><b>LED:</b> stick the 20 mm star into the floor pocket with thermal tape or a dab of thermal glue. Feed its two wires down through the floor slots.</li>
<li><b>Diffuser:</b> cut a 51 × 51 mm square of frosted plastic (or two layers of baking paper) and slide it into the side slot 12 mm above the LED.</li>
<li><b>Prepare the LCD:</b> the Nokia 5110's own circuit board sits behind the glass and blocks light, so it needs a window:
  <ul>
  <li>Bend up the four metal tabs and lift off the frame, glass and white light guide. Keep the rubber zebra strips clean and in place.</li>
  <li>Discard the light guide. Mark the active pixel area (about 30 × 22 mm) on the board, centred under where the glass sits.</li>
  <li>Check both sides of the board in that area. If a trace crosses it, bridge it later with thin wire. Then cut the window with a rotary tool and file it smooth.</li>
  <li>Refit the glass and frame, and bend the tabs back. Plug it into the ESP32 and check the display still works before going further.</li>
  </ul></li>
<li>Set the LCD board into the pocket at the top of the carrier, glass facing up, header toward the notch.</li>
<li>Mask the glass border with black electrical tape so only the pixel area lets light through.</li>
<li>Lower the carrier into the tower from the top until it rests on the ledge at the bottom. Plug in the LED and LCD leads below.</li></ol>`,
  },
  {
    title: 'Lens sleeve',
    view: { visible: s7, highlight: ['sleeve', 'ref_lens', 'lens_cap'], explode: 0.3, camera: [300, 360, 380], target: [30, 210, -8] },
    html: `<ol>
<li>Drop the 50 mm lens into the round seat at the top of the sleeve.</li>
<li>Glue the lens cap on top with three small dots of glue. Keep glue off the glass.</li>
<li>Slide the sleeve, lens end up, into the top of the tower.</li>
<li>Leave the focus pin out for now; it goes in after focusing.</li></ol>`,
  },
  {
    title: 'Sunrise light',
    view: { visible: s8, highlight: ['ring_holder', 'ref_ring', 'dome'], explode: 0.5, camera: [-300, 300, 360], target: [-42, 80, -5] },
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
<li>Darken the room. Slide the lens sleeve up and down until the digits on the ceiling are sharp, then push the tapered focus pin into the hole near the top of the tower to lock the sleeve.</li>
<li>If the time reads mirrored or upside down, fix it with <b>Mirror left/right</b> and <b>Flip upside down</b> on the settings page.</li>
<li>Adjust <b>LCD contrast</b> until the background is as dark as it gets without the digits fading.</li></ol>
<p>With a 100 mm lens and a 1.8 m throw (8 ft ceiling, nightstand height), expect an image about 50 cm wide.</p>`,
  },
];
