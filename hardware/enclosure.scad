// Ceiling Clock enclosure - parametric OpenSCAD model
//
// Coordinates are the assembled position (mm). Origin = centre of the base footprint,
// z = 0 at the bottom of the feet, front of the clock faces -Y.
//
// Render one part:   openscad -D 'part="base"' -D 'print=true' -o base.stl enclosure.scad
// Parts: base lid barrel lcd_holder led_cap lens_mount sleeve lens_cap ring_holder dome pins
// No screws: printed snap pins hold the lid, LED cap, lens mount and ring holder; the circuit board snaps under hooks.
// Bought components (not printed, for the 3D viewer): see components.scad. Add -D 'mat="..."' to
//   render one material of a component, e.g. -D 'part="ref_tm1637"' -D 'mat="led_red"'.
//
// Tilting folded projector: the LCD, a 45 degree front-surface mirror and the lens ride in one barrel that
// lies along the back of the clock, half sunk into the base. Light runs along the barrel's axis (+X) from a
// fixed LED cap at the left end, through the LCD, onto the mirror, and up through the lens. Turning the
// barrel about that axis tilts the beam forward (-Y) without rotating the picture, because the LCD turns
// with it. Detents every 5 degrees from -5 to +30. Set tilt below to see it tilted.

part = "assembly";
print = false;     // true = move/rotate the part into its printing orientation
tilt = 0;          // barrel tilt in degrees, + = image moves forward (assembled views only)
$fn = 64;
eps = 0.01;

// ---------------------------------------------------------------- main dimensions
box_w = 170;  box_d = 135;          // footprint
feet_h = 6;   floor_t = 2.5;        // feet raise the floor so the downward speaker can breathe
wall = 2.5;   corner_r = 6;
base_top = 44;                      // top edge of the base walls
lid_t = 3;
lid_top = base_top + lid_t;         // 47
floor_top = feet_h + floor_t;       // 8.5
post_xy = [box_w/2 - 6 - wall/2, box_d/2 - 6 - wall/2];   // lid posts (x, y)
posts = [[-1, -1], [1, -1], [-1, 1]];                      // the back-right corner is the barrel's bearing block

// snap pins: split shaft with a barb. All joints use the same pin (grip = clamped thickness).
pin_d = 4.0;  pin_hole = 4.25;  pin_barb = 0.45;  pin_tip = 2.6;  pin_slot = 1.1;
pin_head_d = 7.5;  pin_head_t = 1.2;  pin_recess = 8.1;   // counterbore for the head
pin_catch = 4;                                         // how far the pin enters a lid post
pin_grip = lid_t - pin_head_t + pin_catch;             // 5.8 mm, same for every joint
tab_t = 4;                                             // pinned tabs: 2.8 mm under the head + 3 mm below = grip

// ---------------------------------------------------------------- tilting barrel optics
// Barrel axis = optical axis: parallel to X through (ax_y, z_ax). r = distance from the axis.
br_R = 34;  br_ri = 32;                                    // the 45 mm LCD board's corners reach r = 31.8
z_ax = floor_top + 2 + br_R;                               // 44.5: the axis sits at lid level
ax_y = box_d/2 - wall - 0.5 - br_R;                        // 30.5
lens_v = 106;                    // lens-to-LCD distance for a 100 mm lens and ~1.8 m throw
mirror_L = 50;  mirror_W = 50;  mirror_t = 1.1;            // 50 x 50 x 1.1 mm front-surface mirror
mx = 38;                                                   // mirror centre x = lens x
rL = 54;                                                   // lens centre, radial distance above the axis (focus +/-5)
lcd_x = mx - (lens_v - rL);                                // -21: LCD pixel plane
mh = mirror_L / 2 / sqrt(2);
br_x0 = lcd_x - 12;                                        // -33: open left end (the LCD holder plugs in here)
br_x1 = 76.5;                                              // closed right end, with the axle stub
axle_d = 8;  axle_l = 7;
lh_x1 = lcd_x + 4;                                         // LCD holder: br_x0 .. lh_x1
// LED cap (fixed): LED star, diffuser, and a collar the barrel turns on
led_x = lcd_x - 31;                                        // back of the LED star
cap_x0 = led_x - 4;  cap_x1 = br_x0 - 0.5;  cap_R = 30;
collar_od = 44;  collar_id = 40;
diff_x = led_x + 9;
cap_tab_x = cap_x0 - 6;  cap_tab_dy = 18;                  // two pinned tabs resting on the lid's left arm
// focusing: the lens sits in a sleeve with a coarse thread, screwed into a threaded collar (the lens mount)
// that is pinned to the barrel. A knurled grip on top of the sleeve stands clear of the collar, so you turn
// it with your fingers: one turn = 3 mm. A springy tongue in the collar presses on the thread so it stays put.
lens_d = 50.5;  lens_seat = 3;  lens_clear = 46;
thr_P = 3;  thr_e = 0.8;  thr_R = 27.5;  thr_clr = 0.35;  // thread: pitch, depth/2, major radius, clearance
focus_mm = 0;                                              // focus position for the assembled model (-5 .. +5)
grip_h = 6;  grip_od = 61;  sl_thr = 17;                   // knurled grip, thread length below it
lens_z = z_ax + rL + 1.75 + focus_mm;                      // top of the sleeve (lens seat)
lm_od = 62;  lm_tab = lm_od/2 + 4;  lm_wall = lm_od/2 - thr_R - thr_clr;
lm_top = rL - 5 + 1.75 - grip_h - 0.5;                     // r of the collar's top: the grip clears it at the lowest focus
br_hole = 2 * thr_R + 1.5;                                 // the sleeve's thread passes through the barrel top
// detents: notches on the barrel's right end, a springy tongue on the bearing block below the axis
det_r = 22;  det_angles = [-5, 0, 5, 10, 15, 20, 25, 30];
// lid: covers the front and the left end; the barrel and LED cap sit in the cut-out
lid_cut = [cap_x0 - 0.5, br_x1 + 0.5, ax_y - br_R - 0.5];   // x from, x to, y from (open to the back)
blk_x = br_x1 + 0.5;                                       // right bearing block, x from here to the wall

// other lid features
ring_xy = [-50, -35];  ring_pin_r = 11;   ring_od = 44.5; ring_id = 31.5;  dome_d = 58;  dome_h = 20;
button_xy = [0, -35]; button_hole = 16.2;
ldr_xy = [60, -50];                      // clear of the corner pins, the dome and the barrel
// front display: TM1637 4-digit module. Set to "0.36" (42 x 24 mm board, default) or "0.56" (~50 mm display).
tm_size = "0.36";
tm_disp = tm_size == "0.56" ? [50.4, 19, 8] : [30.2, 14.2, 7.2];   // display face w, h, depth from the board
tm_board = tm_size == "0.56" ? [53, 25] : [42, 24];                // module PCB w, h
tm_w = tm_disp[0] + 1; tm_h = tm_disp[1] + 1; tm_z = 28;          // front window
tm_pcb_y = -box_d/2 + wall + tm_disp[2];                          // PCB plane (display face against the wall)
// left side panel: USB-C power and button B
usb_y = -8;  usb_z = 18;  btnb_y = -40;  btnb_z = 28;
// circuit board: 70 x 50 mm perfboard resting on 4 pads, held by 4 snap hooks on its short edges
pb_xy = [45, -27];  pb_size = [70, 50];  pb_boss_h = 12;
pb_top = feet_h + floor_t + pb_boss_h + 1.6;           // top surface of the board
hook_t = 1.4;  hook_lip = 0.9;  hook_w = 8;  hook_dy = 12;
// speaker (40 mm), facing down through the floor
spk_xy = [-48, -30];  spk_d = 40.5;

// ---------------------------------------------------------------- helpers
module rrect(w, d, h, r) {
  linear_extrude(h) offset(r) square([w - 2*r, d - 2*r], center = true);
}
module ax_cyl(r, x0, x1) translate([x0, ax_y, z_ax]) rotate([0, 90, 0]) cylinder(r = r, h = x1 - x0, $fn = 120);
module tilted() translate([0, ax_y, z_ax]) rotate([tilt, 0, 0]) translate([0, -ax_y, -z_ax]) children();
module mirror_frame() translate([mx, ax_y, z_ax]) rotate([0, -45, 0]) children();   // local +z = mirror front normal
// point at radius r, angle a (degrees from straight up, + toward the front) on a plane x
function polar(x, r, a) = [x, ax_y - r * sin(a), z_ax + r * cos(a)];

// ---------------------------------------------------------------- base
module base() {
  difference() {
    union() {
      // shell
      translate([0, 0, feet_h]) difference() {
        rrect(box_w, box_d, base_top - feet_h, corner_r);
        translate([0, 0, floor_t]) rrect(box_w - 2*wall, box_d - 2*wall, base_top, corner_r - wall);
      }
      // feet
      for (sx = [-1, 1], sy = [-1, 1])
        translate([sx * (box_w/2 - 14), sy * (box_d/2 - 14), 0]) cylinder(d = 14, h = feet_h + eps);
      // lid posts
      for (p = posts) translate([p[0] * post_xy[0], p[1] * post_xy[1], feet_h]) cylinder(r = 4.5, h = base_top - feet_h);
      // circuit board support pads (under the corners) and snap hooks (on the short edges)
      for (sx = [-1, 1], sy = [-1, 1])
        translate([pb_xy[0] + sx * (pb_size[0]/2 - 3.5), pb_xy[1] + sy * (pb_size[1]/2 - 3.5), feet_h])
          cylinder(d = 7, h = floor_t + pb_boss_h);
      for (side = [-1, 1], dy = [-hook_dy, hook_dy]) board_hook(pb_xy[1] + dy, side);
      // speaker retaining ring
      translate([spk_xy[0], spk_xy[1], feet_h]) difference() {
        cylinder(d = spk_d + 4, h = floor_t + 5);
        cylinder(d = spk_d, h = 20);
      }
      // TM1637 rails behind the front window: the PCB edges slide down into the slots
      for (sx = [-1, 1]) translate([sx * (tm_board[0]/2 + 1) - 3, -box_d/2 + wall - eps, tm_z - tm_board[1]/2 - 3])
        difference() {
          cube([6, tm_disp[2] + 4, tm_board[1] + 6]);
          translate([sx > 0 ? -eps : 3.5, tm_pcb_y - (-box_d/2 + wall) - 0.1, 3]) cube([2.5 + eps, 1.8, tm_board[1] + 10]);
          // the left rail is notched behind the board where the module's 4-pin header sits
          if (sx < 0) translate([3.5, tm_pcb_y - (-box_d/2 + wall) + 1.6, tm_board[1]/2 - 3]) cube([2.5 + eps, 10, 12]);
        }
      // cradle for the USB-C breakout against the left wall
      translate([-box_w/2 + wall - eps, usb_y - 7, feet_h]) cube([12.3, 14, usb_z - 3.2 - feet_h]);
      // saddle under the LED cap
      difference() {
        translate([cap_x0 + 3, ax_y - 12, feet_h]) cube([cap_x1 - cap_x0 - 12, 24, z_ax - cap_R - feet_h + 6]);
        ax_cyl(cap_R + 0.3, cap_x0, cap_x1);
      }
      bearing_block();
    }
    // lid pin holes: straight bore, then a wider pocket the barb snaps into
    for (p = posts) translate([p[0] * post_xy[0], p[1] * post_xy[1], 0]) {
      translate([0, 0, base_top - pin_catch - eps]) cylinder(d = pin_hole, h = pin_catch + 1);
      translate([0, 0, base_top - pin_catch - pin_tip - 0.8]) cylinder(d = pin_d + 2 * pin_barb + 0.5, h = pin_tip + 0.8);
    }
    // the barrel turns just clear of the back wall; its axle goes into the bearing block
    ax_cyl(br_R + 0.5, br_x0 - 1, br_x1 + 0.2);
    translate([blk_x - 1, ax_y, z_ax]) rotate([0, 90, 0]) cylinder(d = axle_d + 0.4, h = axle_l + 1.5, $fn = 40);
    // front display window
    translate([-tm_w/2, -box_d/2 - 1, tm_z - tm_h/2]) cube([tm_w, wall + 2, tm_h]);
    // left side: USB-C, button B, vents by the LED cap
    translate([-box_w/2 - 1, usb_y - 5, usb_z - 2.25]) cube([wall + 2, 10, 4.5]);
    translate([-box_w/2 - 1, btnb_y, btnb_z]) rotate([0, 90, 0]) cylinder(d = button_hole, h = wall + 2);
    for (i = [0:4]) translate([-box_w/2 - 1, 14 + i * 8, 14]) cube([wall + 2, 3, 24]);
    // speaker grille
    translate([spk_xy[0], spk_xy[1], -1])
      for (r = [0, 7, 14], a = [0 : (r == 0 ? 360 : 360 / (r * 0.9)) : 359])
        rotate(a) translate([r, 0, 0]) cylinder(d = 3.5, h = feet_h + floor_t + 2, $fn = 16);
  }
}

// Right-hand bearing: a block in the back-right corner, with a hole for the barrel's axle and a springy
// tongue whose nub clicks into the detent notches on the barrel's end.
module bearing_block() {
  bx1 = box_w/2 - wall/2;
  difference() {
    union() {
      translate([blk_x, ax_y - br_R - 0.5, feet_h]) cube([bx1 - blk_x, box_d/2 - wall/2 - (ax_y - br_R - 0.5), lid_top - feet_h]);
      translate([blk_x, ax_y, z_ax]) rotate([0, 90, 0]) cylinder(r = 11, h = bx1 - blk_x + wall/2 - 0.01, $fn = 64);
    }
    translate([blk_x - 1, ax_y, z_ax]) rotate([0, 90, 0]) cylinder(d = axle_d + 0.4, h = axle_l + 1.5, $fn = 40);
    // tongue: two slots and a pocket behind it leave a 1.6 mm spring
    for (s = [-1, 1]) translate([blk_x - 1, ax_y + s * 4 - 0.6, z_ax - det_r - 8]) cube([4, 1.2, 14]);
    translate([blk_x + 1.6, ax_y - 4.6, z_ax - det_r - 8]) cube([3, 9.2, 14]);
  }
  // nub
  translate([blk_x + 0.2, ax_y, z_ax - det_r]) sphere(r = 1.2, $fn = 20);
}

// Snap hook on a short edge of the circuit board (side = +1 right edge, -1 left edge)
module board_hook(y, side) {
  edge_x = pb_xy[0] + side * (pb_size[0]/2 + 0.25);
  z0 = feet_h + floor_t - eps;
  translate([side > 0 ? edge_x : edge_x - hook_t, y - hook_w/2, z0]) cube([hook_t, hook_w, pb_top + 2.6 - z0]);
  // lip: flat catch on the underside, ramp on top
  translate([edge_x, y + hook_w/2, 0]) rotate([90, 0, 0]) linear_extrude(hook_w)
    polygon([[0, pb_top + 0.15], [-side * hook_lip, pb_top + 0.15], [-side * hook_lip, pb_top + 0.75], [0, pb_top + 2.6]]);
}

// ---------------------------------------------------------------- lid (front plus the left end; barrel sits in the cut-out)
module lid() {
  difference() {
    translate([0, 0, base_top]) rrect(box_w, box_d, lid_t, corner_r);
    translate([lid_cut[0], lid_cut[2], base_top - 1]) cube([200, 200, 10]);
    // bevel the edge in front of the barrel so the lens mount clears it at full tilt
    translate([mx - lm_od/2 - 2, lid_cut[2], base_top]) rotate([0, 90, 0]) linear_extrude(lm_od + 4)
      polygon([[0.01, 0.01], [0.01, -2.5], [-lid_t - 0.01, -6], [-lid_t - 0.01, 0.01]]);
    // pin holes with a recess so the pin heads sit flush
    for (p = posts) translate([p[0] * post_xy[0], p[1] * post_xy[1], base_top - 1]) {
      cylinder(d = pin_hole, h = 10);
      translate([0, 0, 1 + lid_t - pin_head_t]) cylinder(d = pin_recess, h = 10);
    }
    // LED cap tab pins
    for (s = [-1, 1]) translate([cap_tab_x, ax_y + s * cap_tab_dy, base_top - 1]) cylinder(d = pin_hole, h = 10);
    // sunrise ring: wire hole + holder pins
    translate([ring_xy[0], ring_xy[1], base_top - 1]) {
      cylinder(d = 10, h = 10);
      for (a = [90, 210, 330]) rotate(a) translate([ring_pin_r, 0, 0]) cylinder(d = pin_hole, h = 10);
    }
    translate([button_xy[0], button_xy[1], base_top - 1]) cylinder(d = button_hole, h = 10);
    translate([ldr_xy[0], ldr_xy[1], base_top - 1]) cylinder(d = 5.2, h = 10);
  }
}

// ---------------------------------------------------------------- barrel (turns; carries the LCD holder, mirror and lens mount)
module barrel() {
  difference() {
    union() {
      difference() {
        ax_cyl(br_R, br_x0, br_x1);
        ax_cyl(br_ri, br_x0 - 1, br_x1 - 2);
      }
      // 45 degree ramp the mirror lies on, and a stop at its lower edge
      intersection() {
        ax_cyl(br_ri + 0.1, br_x0, br_x1 - 1.9);
        mirror_frame() union() {
          translate([-200, -100, -200]) cube([400, 200, 200 - mirror_t]);
          translate([-mirror_L/2 - 3, -100, -mirror_t - 1]) cube([3, 200, mirror_t + 3]);
        }
      }
      // bosses under the lens mount's pins, so the pins grip 3 mm of barrel
      for (s = [-1, 1]) translate([mx + s * lm_tab, ax_y, z_ax + br_ri - 1]) cylinder(d = 9, h = 1.5);
      // axle stub on the right end
      translate([br_x1 - eps, ax_y, z_ax]) rotate([0, 90, 0]) cylinder(d = axle_d, h = axle_l, $fn = 40);
    }
    // light hole in the top, under the lens
    translate([mx, ax_y, z_ax]) cylinder(d = br_hole, h = br_R + 5);
    // lens mount pins, with a pocket for the barb where the pin ends up in the solid ramp
    for (s = [-1, 1]) translate([mx + s * lm_tab, ax_y, z_ax + br_ri - 1 - pin_tip - 1]) {
      cylinder(d = pin_hole, h = 10);
      cylinder(d = pin_d + 2 * pin_barb + 0.5, h = pin_tip + 1);
    }
    // key slot for the LCD holder (bottom of the left end)
    translate([br_x0 - 1, ax_y - 2.2, z_ax - br_R - 1]) cube([7, 4.4, 4]);
    // slot for the LCD leads, low on the front side (stays in the base at every tilt)
    hull() for (dx = [0, 10]) translate(polar(lcd_x + 6 + dx, br_R - 3, 120)) rotate([-120, 0, 0]) cylinder(d = 7, h = 8, $fn = 24);
    // detent notches on the right end face
    for (a = det_angles) translate(polar(br_x1 + axle_l * 0 + 0.0, det_r, 180 - a) + [0, 0, 0])
      rotate([0, 90, 0]) translate([0, 0, -1]) cylinder(r = 1.35, h = 2, $fn = 16);
    // tilt marks on the right end, above the lid: one groove per detent
    for (a = det_angles) translate(polar(br_x1 - 0.6, br_R - 3, a)) rotate([-a, 0, 0]) cube([2, 0.8, 6], center = true);
  }
}

// LCD holder: a disc that plugs into the barrel's left end. The board drops into its slot from the top
// (before the holder goes in), glass toward the mirror; the barrel wall then closes the slot.
module lcd_holder() {
  difference() {
    union() {
      ax_cyl(br_ri - 0.2, br_x0, lh_x1);
      translate([br_x0, ax_y - 2, z_ax - br_R + 0.6]) cube([6, 4, 3]);                 // key
    }
    ax_cyl(collar_od / 2 + 0.3, br_x0 - 1, br_x0 + 2);                                // recess for the LED cap's collar
    translate([br_x0 - 1, ax_y - 12, z_ax - 16]) cube([20, 24, 32]);                  // window: 32 tall x 24 wide
    translate([lcd_x - 3.15, ax_y - 22.8, z_ax - 22.8]) cube([1.8, 45.6, 60]);        // board slot, open at the top
    translate([lcd_x - 1.4, ax_y - 22, z_ax - 22]) cube([20, 44, 60]);                // frame, glass and header
  }
}

// LED cap: fixed. Holds the LED star and the diffuser disc; its collar sits in the barrel's left end.
module led_cap() {
  difference() {
    union() {
      ax_cyl(cap_R, cap_x0, cap_x1 - 8);
      translate([cap_x1 - 8, ax_y, z_ax]) rotate([0, 90, 0]) cylinder(r1 = cap_R, r2 = collar_od / 2, h = 8, $fn = 120);
      ax_cyl(collar_od / 2, cap_x1 - eps, br_x0 + 1.8);
      for (s = [-1, 1]) translate([cap_tab_x - 6, ax_y + s * cap_tab_dy - 6, lid_top]) cube([cap_x0 - cap_tab_x + 7, 12, tab_t]);
    }
    ax_cyl(23, led_x, cap_x1 - 8);                                                   // light chamber
    translate([cap_x1 - 9, ax_y, z_ax]) rotate([0, 90, 0]) cylinder(r1 = 23, r2 = collar_id / 2, h = 9.01, $fn = 96);
    ax_cyl(collar_id / 2, cap_x1 - 1, br_x0 + 3);
    ax_cyl(10.2, led_x - 1, led_x + 1);                                              // LED star pocket
    // diffuser slot: a 48 mm disc dropped in from the top
    translate([diff_x - 0.6, ax_y - 24.3, z_ax - 24.3]) cube([1.2, 48.6, 60]);
    // air holes in the back plate (above and below the star) and the LED lead hole
    for (sy = [-1, 1], sz = [-1, 1]) translate([cap_x0 - 1, ax_y + sy * 15, z_ax + sz * 15]) rotate([0, 90, 0]) cylinder(d = 7, h = 10);
    translate([cap_x0 - 1, ax_y, z_ax - 14]) rotate([0, 90, 0]) cylinder(d = 4, h = 10);
    for (s = [-1, 1]) translate([cap_tab_x, ax_y + s * cap_tab_dy, lid_top - 1]) {
      cylinder(d = pin_hole, h = 10);
      translate([0, 0, 1 + tab_t - pin_head_t]) cylinder(d = pin_recess, h = 10);
    }
  }
}

// ---------------------------------------------------------------- lens mount (threaded collar on the barrel), sleeve and cap
// Single-start thread: a circle offset by thr_e, swept up a helix. Its phase depends only on absolute z,
// so the sleeve and the collar always mesh. Internal = the same with a little clearance.
module helix(r, z0, z1) {
  h = z1 - z0;
  translate([0, 0, z0]) linear_extrude(height = h, twist = -360 * h / thr_P, slices = ceil(h / thr_P * 30), convexity = 6)
    rotate(360 * (z0 - z_ax) / thr_P) translate([thr_e, 0]) circle(r = r - thr_e, $fn = 96);
}

module lens_mount() {
  difference() {
    union() {
      // the saddle reaches down the barrel's sides so it covers the light hole all round
      translate([mx, ax_y, z_ax + 13]) cylinder(d = lm_od, h = lm_top - 13, $fn = 96);
      hull() for (s = [-1, 1]) translate([mx + s * lm_tab, ax_y, z_ax + br_R - 4]) cylinder(d = 12, h = tab_t + 4);
    }
    ax_cyl(br_R + 0.2, br_x0 - 50, br_x1 + 50);                                     // saddle on the barrel
    translate([mx, ax_y, 0]) helix(thr_R + thr_clr, z_ax + 12, z_ax + lm_top + 1);   // internal thread
    for (s = [-1, 1]) translate([mx + s * lm_tab, ax_y, z_ax]) {
      cylinder(d = pin_hole, h = 100);
      translate([0, 0, br_R + tab_t - pin_head_t]) cylinder(d = pin_recess, h = 100);
    }
    // springy tongue at the back of the collar: two slots
    for (s = [-1, 1]) translate([mx + s * 3.5 - 0.5, ax_y, z_ax + lm_top - 8]) cube([1, lm_od, 9]);
  }
  // the tongue's nub presses on the sleeve's thread so it doesn't creep
  translate([mx, ax_y + thr_R + thr_clr + 0.6, z_ax + lm_top - 4]) sphere(r = 1.2, $fn = 20);
}

module sleeve() {
  translate([mx, ax_y, 0]) difference() {
    union() {
      translate([0, 0, lens_z - grip_h]) difference() {                            // knurled grip
        cylinder(d = grip_od, h = grip_h, $fn = 120);
        for (a = [0 : 10 : 359]) rotate(a) translate([grip_od / 2, 0, -1]) cylinder(d = 2.4, h = grip_h + 2, $fn = 12);
      }
      helix(thr_R, lens_z - grip_h - sl_thr, lens_z - grip_h + 0.01);              // external thread
    }
    translate([0, 0, lens_z - grip_h - sl_thr - 1]) cylinder(d = lens_clear, h = 100, $fn = 96);   // light path
    translate([0, 0, lens_z - lens_seat]) cylinder(d = lens_d, h = 10, $fn = 96);                  // lens seat
    // arrows on the top face: turn clockwise (seen from above) to focus further, anticlockwise to focus closer
    for (k = [0, 1]) rotate(k * 180 + 60) translate([0, 0, lens_z - 0.6]) {
      rotate_extrude(angle = 40, $fn = 60) translate([27.2, 0]) square([1.2, 1]);
      translate([27.8, 0, 0]) linear_extrude(1) polygon([[-2, 0], [2, 0], [0, -3]]);
    }
  }
}

module lens_cap() {
  translate([mx, ax_y, lens_z]) difference() {
    cylinder(d = lens_d + 4, h = 2, $fn = 96);
    translate([0, 0, -1]) cylinder(d = lens_clear, h = 10, $fn = 96);
  }
}

// ---------------------------------------------------------------- sunrise ring holder + diffuser dome
module ring_holder() {
  translate([ring_xy[0], ring_xy[1], lid_top]) difference() {
    cylinder(d = dome_d, h = 5);
    translate([0, 0, 1.5]) difference() { cylinder(d = ring_od + 0.6, h = 10); cylinder(d = ring_id - 0.6, h = 10); }
    translate([0, 0, -1]) cylinder(d = 10, h = 10);
    for (a = [90, 210, 330]) rotate(a) translate([ring_pin_r, 0, -1]) {
      cylinder(d = pin_hole, h = 10);
      translate([0, 0, 1 + lid_t - pin_head_t + pin_catch - lid_t]) cylinder(d = pin_recess, h = 10);  // floor 2.8 mm up
    }
    // dome locating groove
    translate([0, 0, 3.5]) difference() { cylinder(d = dome_d - 8 + 0.6, h = 5); cylinder(d = dome_d - 8 - 3, h = 5); }
  }
}

module dome() {
  // print in white or clear PLA, 2 perimeters
  translate([ring_xy[0], ring_xy[1], lid_top + 3.5]) difference() {
    scale([1, 1, dome_h / ((dome_d - 8)/2)]) sphere(d = dome_d - 8);
    scale([1, 1, (dome_h - 1.4) / ((dome_d - 8)/2 - 1.4)]) sphere(d = dome_d - 8 - 2.8);
    translate([0, 0, -100]) cube(200, center = true);
  }
}

// ---------------------------------------------------------------- snap pins
// Modelled along +z with the head below z = 0. Flats on two sides so it prints lying down
// (layers run along the pin, which makes it far stronger than printing it upright).
module snap_pin() {
  flat = pin_d / 2 - 0.5;                 // pin is 3 mm thick across the flats
  intersection() {
    difference() {
      union() {
        translate([0, 0, -pin_head_t]) cylinder(d = pin_head_d, h = pin_head_t, $fn = 48);
        cylinder(d = pin_d, h = pin_grip, $fn = 40);
        translate([0, 0, pin_grip]) cylinder(d1 = pin_d + 2 * pin_barb, d2 = pin_d - 0.8, h = pin_tip, $fn = 40);
      }
      // split so the barb can squeeze through the hole
      translate([-pin_slot/2, -pin_d, pin_grip + pin_tip - (pin_tip + 3.6)]) cube([pin_slot, 2 * pin_d, pin_tip + 4]);
    }
    translate([-50, -flat, -50]) cube([100, 2 * flat, 100]);
  }
}

// Print plate: 12 snap pins (10 needed + spares), lying on their flats.
module pin_plate() {
  flat = pin_d / 2 - 0.5;
  for (i = [0:11]) translate([(i % 6) * 11, floor(i / 6) * 16, flat]) rotate([90, 0, 0]) snap_pin();
}

// ---------------------------------------------------------------- bought components (viewer only, not printed)
include <components.scad>

// ---------------------------------------------------------------- dispatch
// Parts that ride in the barrel are drawn at the current tilt.
module show(p) {
  if (p == "base") base();
  else if (p == "lid") lid();
  else if (p == "barrel") tilted() barrel();
  else if (p == "lcd_holder") tilted() lcd_holder();
  else if (p == "led_cap") led_cap();
  else if (p == "lens_mount") tilted() lens_mount();
  else if (p == "sleeve") tilted() sleeve();
  else if (p == "lens_cap") tilted() lens_cap();
  else if (p == "ring_holder") ring_holder();
  else if (p == "dome") dome();
  else if (p == "pins") pin_plate();
  else if (p == "pin") snap_pin();
  else if (p == "ref_esp32") ref_esp32();
  else if (p == "ref_perfboard") ref_perfboard();
  else if (p == "ref_lcd") tilted() ref_lcd();
  else if (p == "ref_led") ref_led();
  else if (p == "ref_lens") tilted() ref_lens();
  else if (p == "ref_mirror") tilted() ref_mirror();
  else if (p == "ref_ring") ref_ring();
  else if (p == "ref_speaker") ref_speaker();
  else if (p == "ref_tm1637") ref_tm1637();
  else if (p == "ref_amp") ref_amp();
  else if (p == "ref_rtc") ref_rtc();
  else if (p == "ref_mosfet") ref_mosfet();
  else if (p == "ref_button") ref_button();
  else if (p == "ref_usbc") ref_usbc();
  else if (p == "ref_buttonB") ref_buttonB();
  else if (p == "ref_window") ref_window();
  else if (p == "ref_ldr") ref_ldr();
  else if (p == "ref_diffuser") ref_diffuser();
  else if (p == "ref_wires") ref_wires();
  else if (p == "pins_asm") assembled_pins();
  else if (p == "pins_barrel") tilted() barrel_pins();
}

// Printing orientation: lay each part on the bed at z = 0.
module print_pose(p) {
  if (p == "lid")              translate([0, 0, -base_top]) children();
  // barrel stands on its open left end; the mirror ramp is then a 45 degree slope, no supports
  else if (p == "barrel")      rotate([0, -90, 0]) translate([-br_x0, -ax_y, -z_ax]) children();
  else if (p == "lcd_holder")  rotate([0, -90, 0]) translate([-br_x0, -ax_y, -z_ax]) children();
  // LED cap stands on its collar; the tabs then rise as upright walls
  else if (p == "led_cap")     rotate([0, 90, 0]) translate([-(br_x0 + 1.8), -ax_y, -z_ax]) children();
  // lens mount prints upside down, top ring on the bed
  else if (p == "lens_mount")  translate([0, 0, z_ax + lm_top]) mirror([0, 0, 1]) translate([-mx, -ax_y, 0]) children();
  else if (p == "sleeve")      translate([-mx, -ax_y, lens_z]) mirror([0, 0, 1]) children();  // seat face down
  else if (p == "lens_cap")    translate([-mx, -ax_y, -lens_z]) children();
  else if (p == "ring_holder") translate([-ring_xy[0], -ring_xy[1], -lid_top]) children();
  else if (p == "dome")        translate([-ring_xy[0], -ring_xy[1], -lid_top - 3.5]) children();
  else children();
}
module show_print(p) {   // as show(), but untilted
  if (p == "barrel") barrel(); else if (p == "lcd_holder") lcd_holder(); else if (p == "lens_mount") lens_mount();
  else if (p == "sleeve") sleeve(); else if (p == "lens_cap") lens_cap(); else show(p);
}

// ---------------------------------------------------------------- pins in their assembled positions (viewer / checks)
module barrel_pins() for (s = [-1, 1])     // lens mount -> barrel (these turn with the barrel)
  translate([mx + s * lm_tab, ax_y, z_ax + br_R + tab_t - pin_head_t]) rotate([180, 0, 0]) snap_pin();
module assembled_pins() {
  // lid -> base posts
  for (p = posts)
    translate([p[0] * post_xy[0], p[1] * post_xy[1], lid_top - pin_head_t]) rotate([180, 0, 0]) snap_pin();
  // LED cap tabs -> lid
  for (s = [-1, 1])
    translate([cap_tab_x, ax_y + s * cap_tab_dy, lid_top + tab_t - pin_head_t]) rotate([180, 0, 0]) snap_pin();
  // ring holder -> lid
  for (a = [90, 210, 330]) translate([ring_xy[0], ring_xy[1], 0]) rotate(a)
    translate([ring_pin_r, 0, lid_top + 1 + lid_t - pin_head_t + pin_catch - lid_t - 1]) rotate([180, 0, 0]) snap_pin();
}

if (part == "assembly") {
  color("#3a3f47") base();
  color("#4a505a") lid();
  color("#2b2f36") tilted() barrel();
  color("#e8743b") tilted() lcd_holder();
  color("#2b2f36") led_cap();
  color("#2b2f36") tilted() lens_mount();
  color("#9aa3b0") tilted() sleeve();
  color("#f0f0f0", 0.6) dome();
  color("#2a6") ref_perfboard();
  color("#246") ref_esp32();
  color("#9cf", 0.5) tilted() ref_lens();
} else if (part == "joint_check") {
  base(); lid(); assembled_pins(); tilted() barrel_pins();
} else if (print) {
  print_pose(part) show_print(part);
} else {
  show(part);
}
