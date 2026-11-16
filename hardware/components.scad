// Bought components, modelled for the 3D viewer and the assembly pictures (not printed).
// Included by enclosure.scad, so it uses that file's dimensions.
//
// Each part is split by material so the viewer can colour it: render with
//   -D 'part="ref_tm1637"' -D 'mat="pcb_blue"'
// mat = "" renders every material together.

mat = "";
module M(name) { if (mat == "" || mat == name) children(); }

inner_front = -box_d/2 + wall;           // -52.5
inner_back = box_d/2 - wall;             //  52.5

// ---------------------------------------------------------------- small building blocks
module pcb(w, d, t = 1.6) cube([w, d, t]);
module pin_row(n, pitch = 2.54, len = 6) for (i = [0:n-1]) translate([i * pitch - 0.32, -0.32, 0]) cube([0.64, 0.64, len]);
module female_header(n) difference() {
  cube([n * 2.54, 2.54, 8.5]);
  for (i = [0:n-1]) translate([i * 2.54 + 0.9, 0.9, 1]) cube([0.74, 0.74, 9]);
}
module soic(l, w = 3.9, h = 1.5) cube([l, w, h]);
module screw_terminal(n) {     // 5.08 mm pitch, wire entry facing -y
  M("screw_green") difference() {
    cube([n * 5.08, 7.6, 9]);
    for (i = [0:n-1]) translate([i * 5.08 + 1.2, -1, 2]) cube([2.7, 4, 3]);
  }
  M("metal") for (i = [0:n-1]) translate([i * 5.08 + 2.54, 4.2, 9]) cylinder(d = 3, h = 0.4, $fn = 16);
}
module electrolytic(d, h) {
  M("cap_blue") cylinder(d = d, h = h - 0.6, $fn = 32);
  M("metal") translate([0, 0, h - 0.6]) cylinder(d = d - 0.4, h = 0.6, $fn = 32);
}
module resistor_2w(len = 15) {   // along x, centred
  M("resistor") rotate([0, 90, 0]) translate([0, 0, -len/2]) hull() {
    cylinder(d = 5, h = 0.5, $fn = 20); translate([0, 0, len - 0.5]) cylinder(d = 5, h = 0.5, $fn = 20);
  }
  M("seg_off") for (i = [0:3]) translate([-len/2 + 2.5 + i * 2.2, 0, 0]) rotate([0, 90, 0]) cylinder(d = 5.15, h = 1, $fn = 20);
  M("metal") for (s = [-1, 1]) translate([s * (len/2 + 2), 0, 0]) {
    rotate([0, 90, 0]) cylinder(d = 0.8, h = 4, center = true, $fn = 8);
    translate([s * 2, 0, -2.6]) cylinder(d = 0.8, h = 2.6, $fn = 8);
  }
}
// 7-segment digit, face in the x-z plane facing -y; lit = segment bitmask (a..g = bits 0..6)
module seg_digit(lit, h = 9.1, w = 4.9, t = 0.9) {
  hh = h / 2;
  segs = [[0.6, hh * 2 - t, w - 1.2, t], [w - t, hh + 0.3, t, hh - 0.9], [w - t, 0.6, t, hh - 0.9],
          [0.6, 0, w - 1.2, t], [0, 0.6, t, hh - 0.9], [0, hh + 0.3, t, hh - 0.9], [0.6, hh - t/2, w - 1.2, t]];
  for (i = [0:6]) {
    on = floor(lit / pow(2, i)) % 2 == 1;
    if (on) M("led_red") translate([segs[i][0], 0, segs[i][1]]) cube([segs[i][2], 0.3, segs[i][3]]);
    else M("seg_off") translate([segs[i][0], 0, segs[i][1]]) cube([segs[i][2], 0.3, segs[i][3]]);
  }
}
module button16(len = 18, panel = wall) {     // 16 mm flush metal push button; axis +z = outward
  M("metal") { translate([0, 0, 0]) cylinder(d = 19, h = 2, $fn = 48); translate([0, 0, -len]) cylinder(d = 15.8, h = len, $fn = 40); }
  M("alu") translate([0, 0, 2]) cylinder(d = 12, h = 0.3, $fn = 40);
  M("metal_dark") translate([0, 0, -panel - 0.2 - 3]) cylinder(d = 22 / cos(30), h = 3, $fn = 6);
  M("gold") for (s = [-1, 1]) translate([s * 3.5 - 1, -0.3, -len - 6]) cube([2, 0.6, 6]);
}
// wire along a quadratic Bezier from a to c with control point b
module wire(a, b, c, d = 1.3, n = 10) {
  pts = [for (i = [0:n]) let(t = i / n) (1 - t) * (1 - t) * a + 2 * (1 - t) * t * b + t * t * c];
  for (i = [0:n-1]) hull() { translate(pts[i]) sphere(d = d, $fn = 8); translate(pts[i + 1]) sphere(d = d, $fn = 8); }
}

// ---------------------------------------------------------------- TM1637 displays (front, and the projector in the barrel)
// The module at the origin: display face in the x-z plane facing -y, PCB behind it, header at the left end
// pointing back (+y). disp = [face w, h, depth from the board], board = [PCB w, h].
module tm_module(disp, board, big = false) {
  dw = disp[0]; dh = disp[1]; dd = disp[2];
  bw = board[0]; bh = board[1];
  dig_h = big ? 14.2 : 9.1;  dig_w = dig_h * 0.54;  pitch = dw / 4.2;
  M("pcb_blue") translate([-bw/2, dd, -bh/2]) difference() {
    cube([bw, 1.6, bh]);
    for (sx = [2.5, bw - 2.5], sz = [2.5, bh - 2.5]) translate([sx, -1, sz]) rotate([-90, 0, 0]) cylinder(d = 2.2, h = 4, $fn = 16);
  }
  M("black") translate([-dw/2, 0.3, -dh/2]) cube([dw, dd - 0.3, dh]);
  M("black") translate([-3, dd + 1.6, -2]) cube([6, 1.5, 4]);                      // TM1637 chip on the back
  // "12:30"
  digits = [6, 91, 79, 63];   // 1 2 3 0 as segment masks (OpenSCAD has no hex literals)
  for (i = [0:3]) translate([-dw/2 + 1.6 + i * pitch + (i >= 2 ? 1.2 : 0), 0, -dig_h/2]) seg_digit(digits[i], dig_h, dig_w);
  M("led_red") for (z = [-dig_h * 0.2, dig_h * 0.2]) translate([-0.5, 0, z - 0.5]) cube([1, 0.3, 1]);
  // 4-pin header at the left end, pointing back
  M("black") translate([-bw/2 + 1, dd + 1.6, -5.1]) cube([2.54, 2.54, 10.2]);
  M("gold") for (k = [0:3]) translate([-bw/2 + 1.95, dd + 1.6, -3.81 + k * 2.54]) cube([0.64, 8, 0.64]);
}
module ref_tm1637() translate([0, inner_front, tm_z]) tm_module(tm_disp, tm_board, tm_size == "0.56");
// Projector display: face toward the mirror (+x) at disp_x, long side vertical, header at the top.
// Columns: the module's x (along the digits) -> -z, its y (backwards) -> -x, its z (up the digits) -> +y.
module ref_projdisp() translate([disp_x, ax_y, z_ax]) multmatrix([[0, -1, 0, 0], [0, 0, 1, 0], [-1, 0, 0, 0], [0, 0, 0, 1]])
  tm_module(pj_disp, pj_board);
module ref_window() M("acrylic_red") translate([-tm_w/2 + 0.2, -box_d/2, tm_z - tm_h/2 + 0.2]) cube([tm_w - 0.4, wall, tm_h - 0.4]);

// ---------------------------------------------------------------- buttons
module ref_button()  translate([button_xy[0], button_xy[1], lid_top]) button16(panel = lid_t);
// lit alarm buttons: a 16 mm momentary button with an LED ring, shown lit green
// 16 mm lit button, Adafruit 1440 and its R16 family (dimension drawing: cdn-shop.adafruit.com/datasheets/R16diagram.jpg):
// 18 mm bezel, 13 mm cap standing 6.3 mm proud, body 22 mm below the panel's top face, then 5.5 mm tabs.
module button16lit(len = 22, panel = wall) {
  M("black") { cylinder(d = 18, h = 2, $fn = 48); translate([0, 0, -len]) cylinder(d = 15.6, h = len, $fn = 40); }
  M("led_green") translate([0, 0, 2]) cylinder(d = 13, h = 4.3, $fn = 40);
  M("black") translate([0, 0, -panel - 3]) cylinder(d = 21, h = 3, $fn = 40);          // plastic nut
  M("gold") for (s = [-1, 1], t = [-1, 1]) translate([s * 3 - 0.3, t * 3 - 1, -len - 5.5]) cube([0.6, 2, 5.5]);
}
module ref_alarmbtns() for (p = alarm_xy) translate([p[0], p[1], lid_top]) button16lit(panel = lid_t);
module ref_buttonB() translate([-box_w/2, btnb_y, btnb_z]) rotate([0, -90, 0]) button16();   // left side wall

// ---------------------------------------------------------------- light sensor (GL5528) in the lid
module ref_ldr() translate([ldr_xy[0], ldr_xy[1], lid_top - 2]) {
  M("white") cylinder(d = 5.1, h = 2, $fn = 32);
  M("copper") for (i = [-2:2]) translate([-1.8, i * 0.8 - 0.15, 2]) cube([3.6, 0.3, 0.05]);
  M("metal") for (s = [-1, 1]) translate([s * 1.7, 0, -12]) cylinder(d = 0.5, h = 12, $fn = 8);
}

// ---------------------------------------------------------------- circuit board: perfboard + ESP32-S3-DevKitC-1 + parts
pb0 = [pb_xy[0] - pb_size[0]/2, pb_xy[1] - pb_size[1]/2, pb_top - 1.6];
module ref_perfboard() {
  translate(pb0) {
    M("pcb_green") difference() {
      pcb(pb_size[0], pb_size[1]);
      for (sx = [2, pb_size[0] - 2], sy = [2, pb_size[1] - 2]) translate([sx, sy, -1]) cylinder(d = 3, h = 4, $fn = 16);
    }
    M("copper") for (ix = [0:25], iy = [0:17]) translate([3.6 + ix * 2.54, 3.4 + iy * 2.54, 1.6]) cylinder(d = 1.7, h = 0.06, $fn = 8);
  }
  // female headers for the ESP32 board
  M("black") for (s = [-1, 1]) translate([pb_xy[0] - 22 * 2.54 / 2, pb_xy[1] + s * 11.43 - 1.27, pb_top]) female_header(22);
  // 100 uF for the amplifier in the front strip at the left (the alarm buttons hang just in front of the strip's right
  // part, so keep it free of anything taller than 2.5 mm); 10 k for the light sensor and the two 220 R for the alarm
  // lights in the back strip; power terminal at the left end between the header rows
  translate([pb_xy[0] - 25, pb_xy[1] - 16.4, pb_top]) electrolytic(6.3, 11);
  for (i = [0:2]) translate([pb_xy[0] - 8 + i * 14, pb_xy[1] + 16.4, pb_top + 2.5]) resistor_2w(8);
  translate([pb_xy[0] - 26.4, pb_xy[1] - 5.5, pb_top]) rotate([0, 0, 90]) screw_terminal(2);   // between the header rows, left end
}
module ref_esp32() {
  L = 62.7; W = 25.4; z0 = pb_top + 8.5 + 2.5;      // its pin strips sit on top of the female headers
  x0 = pb_xy[0] - L/2; y0 = pb_xy[1] - W/2;
  translate([x0, y0, z0]) {
    M("pcb_black") pcb(L, W);
    // ESP32-S3-WROOM-1 module at the -x end: PCB, metal shield, antenna
    M("pcb_blue") translate([-0.5, (W - 18) / 2, 1.6]) cube([25.5, 18, 0.8]);
    M("metal") translate([6.5, (W - 15.8) / 2, 2.4]) cube([17.6, 15.8, 2.4]);
    M("gold") for (k = [0:3]) translate([0.6 + k * 1.3, (W - 14) / 2, 2.4]) cube([0.5, 14, 0.04]);
    // two USB-C ports at the +x end, buttons and RGB LED
    M("metal") for (s = [-1, 1]) translate([L - 7.3, W/2 + s * 6.3 - 4.5, 1.6]) cube([7.5, 9, 3.2]);
    M("black") for (s = [-1, 1]) translate([L - 14, W/2 + s * 9 - 2, 1.6]) cube([3.5, 4, 1.4]);
    M("white") translate([L - 18, W/2 - 1, 1.6]) cube([2, 2, 0.8]);
    M("black") translate([L - 30, W/2 - 4, 1.6]) cube([6, 4, 1.2]);            // regulator
    // pin rows going down into the headers
    M("gold") for (s = [0, 1]) translate([L/2 - 21 * 2.54 / 2, W/2 + (s * 2 - 1) * 11.43, -6]) pin_row(22, 2.54, 6);
    M("black") for (s = [0, 1]) translate([L/2 - 22 * 2.54 / 2, W/2 + (s * 2 - 1) * 11.43 - 1.27, -2.5]) cube([22 * 2.54, 2.54, 2.5]);
  }
}

// ---------------------------------------------------------------- modules on the floor
module ref_amp() translate([-10, -50, floor_top]) {      // MAX98357A
  M("pcb_purple") pcb(17.8, 17.8);
  M("black") translate([7, 6, 1.6]) cube([3, 3, 0.9]);
  M("black") translate([1, 15, 1.6]) cube([7 * 2.54, 2.54, 2.5]);
  M("gold") translate([1 + 1.27, 16.27, 1.6]) pin_row(7, 2.54, 8.5);
  translate([3.8, 0.5, 1.6]) screw_terminal(2);
}
module ref_rtc() translate([-26, -50, floor_top]) {      // DS3231 mini (Raspberry Pi style)
  M("pcb_black") pcb(14.5, 14);
  M("black") translate([2, 1.5, 1.6]) soic(10.3, 7.5, 2.5);
  M("metal") translate([7.25, 9.5, 1.6]) cylinder(d = 12.5, h = 2, $fn = 40);
  M("black") translate([0.6, 11.5, 1.6]) cube([5 * 2.54, 2.54, 8.5]);
}
module ref_speaker() translate([spk_xy[0], spk_xy[1], floor_top]) {   // 40 mm, cone facing down through the grille
  M("black") difference() { cylinder(d = 40, h = 2, $fn = 64); translate([0, 0, -1]) cylinder(d = 34, h = 4, $fn = 64); }
  M("cone") translate([0, 0, 0.5]) difference() {
    cylinder(d1 = 34, d2 = 16, h = 6, $fn = 48);
    translate([0, 0, -0.01]) cylinder(d1 = 32.5, d2 = 14.5, h = 5.4, $fn = 48);
  }
  M("black") translate([0, 0, 6.5]) cylinder(d = 22, h = 6, $fn = 48);
  M("metal") translate([0, 0, 12.5]) cylinder(d = 18, h = 0.6, $fn = 40);
  M("gold") for (s = [-1, 1]) translate([s * 15 - 1, -0.3, 2]) cube([2, 0.6, 3]);
}
module ref_usbc() translate([-box_w/2 + wall + 12.3, usb_y - 7, usb_z - 3.2]) rotate([0, 0, 90]) {   // socket faces out of the left wall
  M("pcb_green") pcb(14, 12);
  M("metal") translate([7 - 4.5, 12 - 7.3, 1.6]) cube([9, 7.6, 3.2]);
  M("gold") for (i = [0:3]) translate([1.5 + i * 3.2, 0.6, 1.6]) cube([1.8, 2.2, 0.05]);
}

// ---------------------------------------------------------------- projector parts
// The projector display (above), mirror and lens ride in the barrel (enclosure.scad tilts them).
module ref_mirror() mirror_frame() {                    // 50 x 50 mm front-surface mirror on the 45 degree ramp
  M("mirror") translate([-mirror_L/2, -mirror_W/2, -0.05]) cube([mirror_L, mirror_W, 0.05]);
  M("glass") translate([-mirror_L/2, -mirror_W/2, -mirror_t]) cube([mirror_L, mirror_W, mirror_t - 0.05]);
}
// 50 mm biconvex lens, f = 100 (R about 100 mm, 1.5 mm edge), resting on the seat ledge
module ref_lens() M("glass") translate([mx, ax_y, lens_z - lens_seat + 0.5]) {
  R = 100; c = sqrt(R * R - 25 * 25);
  intersection() {
    translate([0, 0, 1.5 - c]) sphere(r = R, $fn = 160);
    translate([0, 0, c]) sphere(r = R, $fn = 160);
    translate([0, 0, -5]) cylinder(d = 50, h = 12, $fn = 96);
  }
}
// ---------------------------------------------------------------- main wiring runs
module ref_wires() {
  hz = pb_top + 0.5;
  bx = pb_xy[0] - pb_size[0]/2 + 3;          // left edge of the board, where the off-board headers are
  // front display -> board
  for (k = [0:3]) M(["wire_red", "wire_black", "wire_yellow", "wire_white"][k])
    wire([-tm_board[0]/2 + 1.9, inner_front + tm_disp[2] + 9, tm_z - 3.8 + k * 2.54], [0, -46, 40], [bx + 4 + k * 2.54, pb_xy[1] - 20, hz]);
  // button B and USB power (left wall) -> board
  for (s = [-1, 1]) M(s < 0 ? "wire_blue" : "wire_black")
    wire([-box_w/2 + 21, btnb_y, btnb_z + s * 3.5], [-20, -24, 40], [bx, pb_xy[1] + 18 + s * 1.3, hz]);
  for (s = [-1, 1]) M(s < 0 ? "wire_red" : "wire_black")
    wire([-box_w/2 + wall + 11.5, usb_y + s * 3, usb_z - 1.4], [-30, -8, 36], [bx + 1, pb_xy[1] + 12 + s * 1.3, hz]);
  // top button -> board
  for (s = [-1, 1]) M(s < 0 ? "wire_green" : "wire_black")
    wire([button_xy[0] + s * 3.5, button_xy[1], lid_top - 24], [-30, -12, 24], [bx + 3 + s, pb_xy[1] - 4, hz]);
  // alarm buttons -> board: two switch wires and two light wires each
  for (i = [0:1], k = [0:3]) M(["wire_white", "wire_black", "wire_red", "wire_black"][k])
    wire([alarm_xy[i][0] + (k % 2 ? 1 : -1) * 3, alarm_xy[i][1] + (k < 2 ? -3 : 3), lid_top - 27.5], [alarm_xy[i][0] - 25, -58, floor_top + 3],
         [bx + 6 + i * 6 + k * 1.3, pb_xy[1] - 14, hz]);
  // speaker -> amplifier -> board
  M("wire_red") wire([spk_xy[0] + 15, spk_xy[1], floor_top + 4], [-18, -44, 14], [-6.2, -49.5, floor_top + 7]);
  M("wire_black") wire([spk_xy[0] + 8, spk_xy[1] - 12, floor_top + 4], [-20, -54, 16], [-1.1, -49.5, floor_top + 7]);
  for (k = [0:2]) M(["wire_yellow", "wire_green", "wire_blue"][k])
    wire([-7.7 + k * 2.54, -33.7, floor_top + 10], [4, -30, 30], [bx + k * 2.54, pb_xy[1] + 4, hz]);
  // projector display: out of the end cap's back slot, down past the cap and along the floor to the board
  for (k = [0:3]) M(["wire_red", "wire_black", "wire_yellow", "wire_white"][k])
    wire([cap_x0 - 1, ax_y - 3.8 + k * 2.54, z_ax - 15], [-74, ax_y - 10, floor_top + 4], [-62, -2 + k * 2.54, floor_top + 4]);
  for (k = [0:3]) M(["wire_red", "wire_black", "wire_yellow", "wire_white"][k])
    wire([-62, -2 + k * 2.54, floor_top + 4], [-10, 20, floor_top + 6], [bx + 8 + k * 2.54, pb_xy[1] + 22, hz]);
  // clock module -> board
  for (k = [0:3]) M(["wire_red", "wire_black", "wire_blue", "wire_yellow"][k])
    wire([-24.7 + k * 2.54, -37, floor_top + 8], [-6, -30, 30], [bx + 14 + k * 2.54, pb_xy[1] - 21, hz]);
}
