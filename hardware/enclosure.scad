// Ceiling Clock enclosure - parametric OpenSCAD model
//
// Coordinates are the assembled position (mm). Origin = centre of the base footprint,
// z = 0 at the bottom of the feet, front of the clock faces -Y.
//
// Render one part:   openscad -D 'part="base"' -D 'print=true' -o base.stl enclosure.scad
// Parts: base batt_base batt_plate lid barrel disp_holder end_cap lens_mount sleeve lens_cap pins
// No screws: printed quarter-turn lock pins hold the lid, end cap and lens mount; the circuit board snaps under hooks.
// Bought components (not printed, for the 3D viewer): see components.scad. Add -D 'mat="..."' to
//   render one material of a component, e.g. -D 'part="ref_tm1637"' -D 'mat="led_red"'.
//
// Tilting folded projector: a second TM1637 4-digit LED display, a 45 degree front-surface mirror and the
// lens ride in one barrel that lies along the back of the clock, half sunk into the base. The display faces
// along the barrel's axis (+X); its light hits the mirror and goes up through the lens, which images the
// glowing digits onto the ceiling. Turning the barrel about that axis tilts the beam forward (-Y) without
// rotating the picture, because the display turns with it. A fixed end cap closes the left end and carries
// the display's wires out. Detents every 5 degrees from -5 to +30. Set tilt below to see it tilted.

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

// Quarter-turn lock pins, the same as on the VoiceLabels case: push the pin in with its wing head
// lined up with the slot, then turn it a quarter turn either way. A lug on the shaft rides up a small
// ramp on the inside face of the wall (pulling the head tight), clicks into a notch, and a stop keeps
// it from turning further. The head shows the state: along the slot = open, crosswise = locked.
PIN_D = 4.0;  PIN_HOLE_D = 4.3;
PIN_HEAD_L = 12;  PIN_HEAD_W = 6;  PIN_HEAD_T = 2.4;     // wing head (VoiceLabels: 14 long; 12 here to turn beside the lens collar)
LUG_R = 3.2;  LUG_W = 1.8;  LUG_T = 1.2;  LUG_GAP = 0.15;
RAMP_H = 0.4;  NOTCH_H = 0.15;  STOP_H = 1.2;           // off the wall's inside face; lower RAMP_H if too stiff
KEYWAY_W = 2.3;  KEYWAY_R = 3.6;  POCKET_R = 3.8;  POCKET_L = 2.2;
GRIP_SHORT = lid_t;      // lid corners: through the lid, locking under it in a pocket in the post
GRIP_LONG = 7;           // end cap tabs (through them and the lid), lens collar (through it and the barrel wall)
tab_t = 4;               // pinned tabs: tab + 3 mm below = GRIP_LONG

// ---------------------------------------------------------------- tilting barrel optics
// Barrel axis = optical axis: parallel to X through (ax_y, z_ax). r = distance from the axis.
br_R = 34;  br_ri = 32;
z_ax = floor_top + 2 + br_R;                               // 44.5: the axis sits at lid level
ax_y = box_d/2 - wall - 0.5 - br_R;                        // 30.5
lens_v = 130;                    // lens-to-display distance for a lens at the top of the sleeve; the real lens sits lens_drop lower (120 mm)
mirror_L = 50.4;  mirror_W = 50.4;  mirror_t = 2;          // 50 x 50 x 2 mm front-surface mirror (Scott's measures 50.1 x 50.2 x 2.0), 0.2 mm clearance
mx = 34;                                                   // mirror centre x = lens x
rL = 78;                                                   // lens centre, radial distance above the axis (focus +/-5); was 54 for f = 100
disp_x = mx - (lens_v - rL);                               // -18: the display's glowing face
mh = mirror_L / 2 / sqrt(2);
br_x0 = disp_x - 12;                                       // -33: open left end (the display holder plugs in here)
br_x1 = 76.5;                                              // closed right end, with the axle stub
axle_d = 8;  axle_l = 7;
lh_x1 = disp_x + 4;                                        // display holder: br_x0 .. lh_x1
// projector display: TM1637 0.36" module. Board 42 x 24 standing up, long side vertical so the digits run
// left to right on the ceiling; display face toward the mirror; 4-pin header at the top, pointing back.
pj_disp = [30.2, 14.2, 7.2];  pj_board = [42, 24];          // face w, h, depth from the board; PCB w, h
pj_pcb_x = disp_x - pj_disp[2];                            // front face of the module's PCB
// end cap (fixed): closes the barrel's left end, holds the display's wires, and has the collar the barrel turns on
cap_x0 = disp_x - 35;  cap_x1 = br_x0 - 0.5;  cap_R = 30;
collar_od = 52;  collar_id = 46;                           // inside r = 23 clears the header and its plugs
cap_tab_x = cap_x0 - 6;  cap_tab_dy = 18;                  // two pinned tabs resting on the lid's left arm
// focusing: the lens sits in a sleeve with a coarse thread, screwed into a threaded collar (the lens mount)
// that is pinned to the barrel. A knurled grip on top of the sleeve stands clear of the collar, so you turn
// it with your fingers: one turn = 3 mm. A springy tongue in the collar presses on the thread so it stays put.
lens_d = 48;  lens_seat = 3.45;  lens_clear = 45;            // Scott's lens: 47.7 mm across, 2.8 mm edge, 7.6 mm centre (R ~120, f = 121 measured).
                                                           // It rests on the ledge's inner corner, rim ~0.27 mm up; the cap clears it by ~0.1 mm
thr_P = 3;  thr_e = 0.8;  thr_R = 27.5;  thr_clr = 0.35;  // thread: pitch, depth/2, major radius, clearance
focus_mm = 0;                                              // focus position for the assembled model (-5 .. +5)
lens_drop = 10;                  // the lens sits this far down inside the sleeve (bench test 2026-11-20: the lens focuses
                                 // nearer than f = 121, so it must sit closer to the display; the lens mount is unchanged)
grip_h = 6;  grip_od = 61;  sl_thr = 17;                   // knurled grip, thread length below it
lens_z = z_ax + rL + 1.75 + focus_mm;                      // top of the sleeve (lens seat)
lm_od = 62;  lm_tab = lm_od/2 + PIN_HEAD_L/2 + 0.5;  lm_wall = lm_od/2 - thr_R - thr_clr;
lm_top = rL - 5 + 1.75 - grip_h - 0.5;                     // r of the collar's top: the grip clears it at the lowest focus
br_hole = 2 * thr_R + 1.5;                                 // the sleeve's thread passes through the barrel top
// detents: notches on the barrel's right end, a springy tongue on the bearing block below the axis
det_r = 22;  det_angles = [-5, 0, 5, 10, 15, 20, 25, 30];
// lid: covers the front and the left end; the barrel and end cap sit in the cut-out
lid_cut = [cap_x0 - 0.5, br_x1 + 0.5, ax_y - br_R - 0.5];   // x from, x to, y from (open to the back)
blk_x = br_x1 + 0.5;                                       // right bearing block, x from here to the wall

// other lid features
button_xy = [-50, -52]; button_hole = 16.2;
alarm_xy = [[38, -52], [62, -52]];        // lit alarm buttons 1 and 2: front right, well away from snooze. Their
                                          // bodies and tabs hang 27.5 mm below the lid, in front of the circuit board
ldr_xy = [-70, -55];                     // front left: clear of the corner pins, button B, and the alarm buttons' lights
// front display: TM1637 4-digit module. Set to "0.36" (42 x 24 mm board, default) or "0.56" (~50 mm display).
tm_size = "0.36";
tm_disp = tm_size == "0.56" ? [50.4, 19, 8] : [30.2, 14.2, 7.2];   // display face w, h, depth from the board
tm_board = tm_size == "0.56" ? [53, 25] : [42, 24];                // module PCB w, h
tm_w = tm_disp[0] + 1; tm_h = tm_disp[1] + 1; tm_z = 28;          // front window
tm_pcb_y = -box_d/2 + wall + tm_disp[2];                          // PCB plane (display face against the wall)
// left side panel: USB-C power and button B
usb_y = -8;  usb_z = 18;  btnb_y = -40;  btnb_z = 28;
// circuit board: a 70 x 50 mm perfboard cut down to 70 x 40 (14 rows), resting on 4 pads, held by 4 snap hooks on
// its short edges. Its back edge stays clear of the bearing block; its front edge clears the alarm buttons' tabs.
pb_xy = [45, -24.5];  pb_size = [70, 40];  pb_boss_h = 12;
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
      // saddle under the end cap
      difference() {
        translate([cap_x0 + 3, ax_y - 12, feet_h]) cube([cap_x1 - cap_x0 - 12, 24, z_ax - cap_R - feet_h + 6]);
        ax_cyl(cap_R + 0.3, cap_x0, cap_x1);
      }
      bearing_block();
    }
    // lid pin holes: straight bore, then a wider pocket the barb snaps into
    for (p = posts) translate([p[0] * post_xy[0], p[1] * post_xy[1], lid_top]) lp_bore(GRIP_SHORT);   // lug pocket in the post top
    // the barrel turns just clear of the back wall; its axle goes into the bearing block
    ax_cyl(br_R + 0.5, br_x0 - 1, br_x1 + 0.2);
    translate([blk_x - 1, ax_y, z_ax]) rotate([0, 90, 0]) cylinder(d = axle_d + 0.4, h = axle_l + 1.5, $fn = 40);
    // front display window
    translate([-tm_w/2, -box_d/2 - 1, tm_z - tm_h/2]) cube([tm_w, wall + 2, tm_h]);
    // left side: USB-C, button B
    translate([-box_w/2 - 1, usb_y - 5, usb_z - 2.25]) cube([wall + 2, 10, 4.5]);
    translate([-box_w/2 - 1, btnb_y, btnb_z]) rotate([0, 90, 0]) cylinder(d = button_hole, h = wall + 2);
    // wire slot down to the battery base
    translate([0, 0, -1]) bb_slot(floor_top + 2);
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
    lid_pins() lp_bore($grip);
    translate([button_xy[0], button_xy[1], base_top - 1]) cylinder(d = button_hole, h = 10);
    for (p = alarm_xy) translate([p[0], p[1], base_top - 1]) cylinder(d = button_hole, h = 10);
    translate([ldr_xy[0], ldr_xy[1], base_top - 1]) cylinder(d = 5.2, h = 10);
  }
  lid_pins() lp_ramps($grip);   // on the lid's underside: the lid prints upside down
}
// Every lock pin that locks under the lid: frame at the pin's head seat, slot along local +x.
module lid_pins() {
  for (p = posts) translate([p[0] * post_xy[0], p[1] * post_xy[1], lid_top]) { $grip = GRIP_SHORT; children(); }
  for (s = [-1, 1]) translate([cap_tab_x, ax_y + s * cap_tab_dy, lid_top + tab_t]) { $grip = GRIP_LONG; children(); }
}
module barrel_pin_frames() for (s = [-1, 1]) translate([mx + s * lm_tab, ax_y, z_ax + br_R + tab_t]) children();

// ---------------------------------------------------------------- barrel (turns; carries the display holder, mirror and lens mount)
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
      // bosses under the lens mount's pins, so the pins lock behind 3 mm of barrel
      for (s = [-1, 1]) translate([mx + s * lm_tab, ax_y, z_ax + br_ri - 1]) cylinder(d = 9, h = 1.5);
      barrel_pin_frames() lp_ramps(GRIP_LONG);
      // axle stub on the right end
      translate([br_x1 - eps, ax_y, z_ax]) rotate([0, 90, 0]) cylinder(d = axle_d, h = axle_l, $fn = 40);
    }
    // light hole in the top, under the lens. It stops at the ramp's surface: cutting into the solid ramp
    // past the mirror's top edge would leave a wall that faces straight down when the barrel is printed
    // standing on its end. The light never goes below the ramp's surface, so nothing is lost.
    intersection() {
      translate([mx, ax_y, z_ax]) cylinder(d = br_hole, h = br_R + 5);
      mirror_frame() translate([-200, -100, -mirror_t]) cube([400, 200, 200]);
    }
    // lens mount pins (the one at the right end turns in a pocket in the solid ramp)
    barrel_pin_frames() lp_bore(GRIP_LONG);
    // key slot for the display holder (bottom of the left end)
    translate([br_x0 - 1, ax_y - 2.2, z_ax - br_R - 1]) cube([7, 4.4, 4]);
    // detent notches on the right end face
    for (a = det_angles) translate(polar(br_x1 + axle_l * 0 + 0.0, det_r, 180 - a) + [0, 0, 0])
      rotate([0, 90, 0]) translate([0, 0, -1]) cylinder(r = 1.35, h = 2, $fn = 16);
    // tilt marks on the right end, above the lid: one groove per detent
    for (a = det_angles) translate(polar(br_x1 - 0.6, br_R - 3, a)) rotate([-a, 0, 0]) cube([2, 0.8, 6], center = true);
  }
}

// Display holder: a disc that plugs into the barrel's left end. The TM1637 module drops into its slot from
// the top (before the holder goes in), digits toward the mirror and the 4-pin header at the top; the barrel
// wall then closes the slot. The display body sits in a window that flares toward the lens and blocks
// stray light from the board.
module disp_holder() {
  bt = 1.6;                                                                         // module PCB thickness
  difference() {
    union() {
      ax_cyl(br_ri - 0.2, br_x0, lh_x1);
      translate([br_x0, ax_y - 2, z_ax - br_R + 0.6]) cube([6, 4, 3]);                 // key
    }
    ax_cyl(collar_od / 2 + 0.3, br_x0 - 1, br_x0 + 2);                                // recess for the end cap's collar
    // board slot, open at the top
    translate([pj_pcb_x - bt - 0.1, ax_y - pj_board[1]/2 - 0.2, z_ax - pj_board[0]/2 - 0.2]) cube([bt + 0.2, pj_board[1] + 0.4, 60]);
    // display window: the body passes through, then it flares toward the mirror
    hull() {
      translate([pj_pcb_x - 0.2, ax_y - (pj_disp[1] + 0.8)/2, z_ax - (pj_disp[0] + 0.8)/2]) cube([pj_disp[2] + 0.3, pj_disp[1] + 0.8, pj_disp[0] + 0.8]);
      translate([lh_x1 + 0.01, ax_y - (pj_disp[1] + 3)/2, z_ax - (pj_disp[0] + 3)/2]) cube([0.01, pj_disp[1] + 3, pj_disp[0] + 3]);
    }
    translate([lh_x1 - 0.5, ax_y - (pj_disp[1] + 3)/2, z_ax - (pj_disp[0] + 3)/2]) cube([1, pj_disp[1] + 3, pj_disp[0] + 3]);
    // channel from the window up to the rim, so the display body can slide down with the board
    translate([pj_pcb_x - 0.2, ax_y - (pj_disp[1] + 0.8)/2, z_ax]) cube([pj_disp[2] + 0.3, pj_disp[1] + 0.8, 60]);
    // behind the board: room for the chip and the header, open at the top, a 2 mm lip down each long edge
    translate([br_x0 - 1, ax_y - 10, z_ax - pj_board[0]/2 + 2]) cube([pj_pcb_x - bt - br_x0 + 1.01, 20, 60]);
  }
}

// End cap: fixed. Closes the barrel's left end, keeping room light out of the optics; its collar sits in the
// barrel's left end and the barrel turns on it. The display's four wires leave through the slot in the back
// plate, with enough slack in the cap to follow the tilt.
module end_cap() {
  difference() {
    union() {
      ax_cyl(cap_R, cap_x0, cap_x1 - 8);
      translate([cap_x1 - 8, ax_y, z_ax]) rotate([0, 90, 0]) cylinder(r1 = cap_R, r2 = collar_od / 2, h = 8, $fn = 120);
      ax_cyl(collar_od / 2, cap_x1 - eps, br_x0 + 1.8);
      for (s = [-1, 1]) translate([cap_tab_x - 6, ax_y + s * cap_tab_dy - 6, lid_top]) cube([cap_x0 - cap_tab_x + 7, 12, tab_t]);
    }
    ax_cyl(collar_id / 2, cap_x0 + 3, br_x0 + 3);                                   // wire chamber, 3 mm back plate
    // wire slot in the back plate, low down, rounded
    hull() for (sy = [-4, 4]) translate([cap_x0 - 1, ax_y + sy, z_ax - 15]) rotate([0, 90, 0]) cylinder(d = 6, h = 5, $fn = 24);
    for (s = [-1, 1]) translate([cap_tab_x, ax_y + s * cap_tab_dy, lid_top + tab_t]) lp_bore(GRIP_LONG);
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
    barrel_pin_frames() lp_bore(GRIP_LONG);
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
    translate([0, 0, lens_z - lens_drop - lens_seat]) cylinder(d = lens_d, h = lens_drop + 10, $fn = 96);   // lens seat, lens_drop down a bore
    // arrows on the top face: turn clockwise (seen from above) to focus further, anticlockwise to focus closer
    for (k = [0, 1]) rotate(k * 180 + 60) translate([0, 0, lens_z - 0.6]) {
      rotate_extrude(angle = 40, $fn = 60) translate([27.2, 0]) square([1.2, 1]);
      translate([27.8, 0, 0]) linear_extrude(1) polygon([[-2, 0], [2, 0], [0, -3]]);
    }
  }
}

module lens_cap() {   // a ring on the sleeve's top face, with a tube down the bore that holds the lens on its ledge
  translate([mx, ax_y, lens_z]) difference() {
    union() {
      cylinder(d = lens_d + 4, h = 2, $fn = 96);
      if (lens_drop > 0) translate([0, 0, -lens_drop]) cylinder(d = lens_d - 0.4, h = lens_drop + 1, $fn = 96);
    }
    translate([0, 0, -lens_drop - 2]) cylinder(d = lens_clear, h = lens_drop + 10, $fn = 96);
  }
}

// ---------------------------------------------------------------- quarter-turn lock pins
function lp_len(grip) = grip + LUG_GAP + LUG_T + 1.2;      // shaft length under the head

// The pin as printed: wing head flat on the bed, shaft up (+z). The lug (+x) lines up with the
// head's long axis. Its flat underside is a 1.4 mm overhang, which prints fine.
module lock_pin(grip) {
  T = PIN_HEAD_T;  L = lp_len(grip);
  hull() for (s = [-1, 1]) translate([s * (PIN_HEAD_L - PIN_HEAD_W) / 2, 0, 0]) cylinder(d = PIN_HEAD_W, h = T, $fn = 32);
  translate([0, 0, T - 0.01]) cylinder(d = PIN_D, h = L - 0.6 + 0.01, $fn = 32);
  translate([0, 0, T + L - 0.6]) cylinder(d1 = PIN_D, d2 = PIN_D - 1, h = 0.6, $fn = 32);
  z0 = T + grip + LUG_GAP;
  intersection() {
    translate([PIN_D / 2 - 0.3, -LUG_W / 2, z0]) cube([LUG_R - PIN_D / 2 + 0.3, LUG_W, LUG_T]);
    translate([0, 0, z0 - 0.5]) cylinder(r = LUG_R, h = LUG_T + 1, $fn = 32);
  }
}
// Hole for a pin through a stack `grip` thick: the head seats at z = 0, the pin goes down (-z), the
// slot the lug passes is along +x, and there is room below the stack for the lug to turn.
module lp_bore(grip) {
  translate([0, 0, -grip - POCKET_L - 1.2]) cylinder(d = PIN_HOLE_D, h = grip + POCKET_L + 3, $fn = 32);
  translate([0, -KEYWAY_W / 2, -grip - 0.01]) cube([KEYWAY_R, KEYWAY_W, grip + 1.02]);
  translate([0, 0, -grip - POCKET_L]) cylinder(r = POCKET_R, h = POCKET_L + 0.01, $fn = 40);
}
// Ramp, notch and stop on the stack's inside face (z = -grip), each side of the slot: thin sector
// slabs the lug rides over. 24-66 degrees from the slot: ramp up to RAMP_H; 66-112: notch; 112-140: stop.
module lp_ramps(grip) {
  r0 = PIN_HOLE_D / 2 + 0.05;  r1 = LUG_R + 0.35;
  for (side = [0, 1]) mirror([0, side, 0]) for (t = [24 : 3 : 137]) {
    tm = t + 1.5;
    h = tm < 66 ? RAMP_H * (tm - 24) / 42 + 0.02 : tm < 112 ? NOTCH_H : STOP_H;
    rotate(t) translate([0, 0, -grip - h]) rotate_extrude(angle = 3.5, $fn = 120) translate([r0, 0]) square([r1 - r0, h + 0.01]);
  }
}
// A pin in its hole: head on the surface at z = 0, locked = turned crosswise to the slot.
module lp_place(grip, locked = true) translate([0, 0, PIN_HEAD_T]) rotate([180, 0, 0]) rotate(locked ? 90 : 0) lock_pin(grip);

// Print plate: 4 short pins (3 needed) and 5 long ones (4 needed), heads down.
module pin_plate() {
  for (i = [0:3]) translate([i * 14, 0, 0]) lock_pin(GRIP_SHORT);
  for (i = [0:4]) translate([(i % 4) * 14, 12 + floor(i / 4) * 12, 0]) lock_pin(GRIP_LONG);
}

// ---------------------------------------------------------------- battery base
// A printed tray the clock stands on: same footprint, bb_h tall, z from -bb_h to 0. It holds one or two
// 4 x 18650 packs (bays at the back) and the charger, fuel gauge and boost (front strip). A top plate drops
// into a rebate in the tray walls; rings on it locate the clock's four feet, so the clock's weight holds
// the plate down. The wires (USB VBUS down, 5 V back up, I2C, CE, PGOOD) pass through a slot in the clock's
// floor and a matching slot in the plate.
bb_h = 27;  bb_wall = 2.5;  bb_floor = 2;
bbp_t = 2.5;  bbp_reb = 1.2;  bbp_gap = 0.3;               // top plate thickness, rebate width, fit clearance
bay = [78, 74];  bay_h = 21;                               // one pack bay (fits packs up to about 76 x 72 x 20)
bay_y0 = -11;                                              // bays run from here to the back wall
bay_x = [-41, 41];                                         // bay centres
cslot = [-77, -26];  cslot_sz = [8, 16];                   // wire slot, clock floor and plate (x, y centre; w, l)
bb_boards = [   // name, centre x, y, size x, y  (front strip; pockets with 1.2 mm walls)
  ["charger", -52, -42, 38.6, 33.6],   // Adafruit bq24074 (4755), 38 x 33
  ["gauge",   -14, -42, 26, 18.4],     // Adafruit MAX17048 (5580), 25.4 x 17.8
  ["boost",    14, -42, 15.8, 15.8]];  // Pololu U3V40F5, 15.2 x 15.2
module bb_slot(h) translate([cslot[0], cslot[1], 0]) hull() for (s = [-1, 1])
  translate([0, s * (cslot_sz[1] - cslot_sz[0]) / 2, 0]) cylinder(d = cslot_sz[0], h = h, $fn = 32);
module batt_base() translate([0, 0, -bb_h]) {
  in_w = box_w - 2*bb_wall;  in_d = box_d - 2*bb_wall;
  difference() {
    union() {
      difference() {
        rrect(box_w, box_d, bb_h, corner_r);
        translate([0, 0, bb_floor]) rrect(in_w, in_d, bb_h, corner_r - bb_wall);
      }
      // bay walls: a divider between the bays and a front rail, both up to the plate
      translate([-1, bay_y0, 0]) cube([2, box_d/2 - bb_wall - bay_y0, bb_h - bbp_t]);
      translate([-in_w/2, bay_y0 - 2, 0]) difference() {
        cube([in_w, 2, bb_h - bbp_t]);
        for (bx = bay_x) translate([in_w/2 + bx - 12, -1, bb_floor + 4]) cube([24, 4, bb_h]);   // lead notches
      }
      // plate supports in the front strip
      for (x = [-30, 30, 62]) translate([x - 3, -box_d/2 + bb_wall - eps, 0]) cube([6, 3, bb_h - bbp_t]);
      // board pockets
      for (b = bb_boards) translate([b[1], b[2], 0]) difference() {
        translate([-b[3]/2 - 1.2, -b[4]/2 - 1.2, 0]) cube([b[3] + 2.4, b[4] + 2.4, bb_floor + 3]);
        translate([-b[3]/2, -b[4]/2, bb_floor]) cube([b[3], b[4], 10]);
        translate([-b[3]/2 - 2, -4, bb_floor + 1]) cube([b[3] + 4, 8, 10]);   // gaps for the wires
      }
    }
    // rebate for the top plate
    translate([0, 0, bb_h - bbp_t]) rrect(in_w + 2*bbp_reb, in_d + 2*bbp_reb, bbp_t + 1, corner_r - bb_wall + bbp_reb);
    // finger notches to lift the plate (front and back)
    for (sy = [-1, 1]) translate([0, sy * (box_d/2 - bb_wall/2), bb_h]) rotate([0, 90, 0]) cylinder(r = 4, h = 24, center = true);
    // vents in the back wall
    for (x = [-60 : 12 : 60]) translate([x - 2, box_d/2 - bb_wall - 1, 8]) cube([4, bb_wall + 2, 10]);
  }
}
module batt_plate() translate([0, 0, -bbp_t]) {
  in_w = box_w - 2*bb_wall + 2*bbp_reb - 2*bbp_gap;  in_d = box_d - 2*bb_wall + 2*bbp_reb - 2*bbp_gap;
  difference() {
    union() {
      rrect(in_w, in_d, bbp_t, corner_r - bb_wall + bbp_reb - bbp_gap);
      // rings that locate the clock's feet
      for (sx = [-1, 1], sy = [-1, 1]) translate([sx * (box_w/2 - 14), sy * (box_d/2 - 14), bbp_t - eps])
        difference() { cylinder(d = 19, h = 2); translate([0, 0, -1]) cylinder(d = 14.8, h = 4); }
    }
    translate([0, 0, -1]) bb_slot(bbp_t + 2);
  }
}
module ref_packs() for (bx = bay_x) translate([bx, bay_y0 + bay[1]/2, -bb_h + bb_floor]) {   // 4 x 18650 in parallel
  M("cap_blue") for (i = [0:3]) translate([-37 + 9.25 + i * 18.5, 0, 9.25]) rotate([90, 0, 0]) cylinder(d = 18.4, h = 65, center = true, $fn = 32);
  M("black") translate([-37, -33.5, 0]) cube([74, 1, 18.5]);
  M("black") translate([-37, 32.5, 0]) cube([74, 1, 18.5]);
}
module ref_bb_boards() for (b = bb_boards) translate([b[1] - b[3]/2 + 0.3, b[2] - b[4]/2 + 0.3, -bb_h + bb_floor]) {
  M(b[0] == "boost" ? "pcb_green" : "pcb_black") pcb(b[3] - 0.6, b[4] - 0.6);
  M("black") translate([b[3]/2 - 3, b[4]/2 - 3, 1.6]) cube([5, 5, 1]);
}

// ---------------------------------------------------------------- bought components (viewer only, not printed)
include <components.scad>

// ---------------------------------------------------------------- dispatch
// Parts that ride in the barrel are drawn at the current tilt.
module show(p) {
  if (p == "base") base();
  else if (p == "batt_base") batt_base();
  else if (p == "batt_plate") batt_plate();
  else if (p == "ref_packs") ref_packs();
  else if (p == "ref_bb_boards") ref_bb_boards();
  else if (p == "lid") lid();
  else if (p == "barrel") tilted() barrel();
  else if (p == "disp_holder") tilted() disp_holder();
  else if (p == "end_cap") end_cap();
  else if (p == "lens_mount") tilted() lens_mount();
  else if (p == "sleeve") tilted() sleeve();
  else if (p == "lens_cap") tilted() lens_cap();
  else if (p == "pins") pin_plate();
  else if (p == "pin") lock_pin(GRIP_LONG);
  else if (p == "ref_esp32") ref_esp32();
  else if (p == "ref_perfboard") ref_perfboard();
  else if (p == "ref_projdisp") tilted() ref_projdisp();
  else if (p == "ref_lens") tilted() ref_lens();
  else if (p == "ref_mirror") tilted() ref_mirror();
  else if (p == "ref_speaker") ref_speaker();
  else if (p == "ref_tm1637") ref_tm1637();
  else if (p == "ref_amp") ref_amp();
  else if (p == "ref_rtc") ref_rtc();
  else if (p == "ref_button") ref_button();
  else if (p == "ref_alarmbtns") ref_alarmbtns();
  else if (p == "ref_usbc") ref_usbc();
  else if (p == "ref_buttonB") ref_buttonB();
  else if (p == "ref_window") ref_window();
  else if (p == "ref_ldr") ref_ldr();
  else if (p == "ref_wires") ref_wires();
  else if (p == "pins_asm") assembled_pins();
  else if (p == "pins_barrel") tilted() barrel_pins();
}

// Printing orientation: lay each part on the bed at z = 0.
module print_pose(p) {
  if (p == "batt_base")        translate([0, 0, bb_h]) children();
  else if (p == "batt_plate")  translate([0, 0, bbp_t]) children();
  else if (p == "lid")              translate([0, 0, lid_top]) rotate([180, 0, 0]) children();   // upside down (turned over, not mirrored): the pin ramps are on its underside
  // barrel stands on its open left end; the mirror ramp is then a 45 degree slope, no supports
  else if (p == "barrel")      rotate([0, -90, 0]) translate([-br_x0, -ax_y, -z_ax]) children();
  else if (p == "disp_holder") rotate([0, -90, 0]) translate([-br_x0, -ax_y, -z_ax]) children();
  // end cap stands on its collar; the tabs then rise as upright walls
  else if (p == "end_cap")     rotate([0, 90, 0]) translate([-(br_x0 + 1.8), -ax_y, -z_ax]) children();
  // lens mount prints upside down, top ring on the bed. NOTE: these two poses are mirror images, so the printed
  // collar and sleeve have a left-hand thread (anticlockwise from above lowers the lens). Both are mirrored, so they
  // mate, and the sleeve's arrows are mirrored with them. Scott has printed sleeves this way: keep both as they are.
  else if (p == "lens_mount")  translate([0, 0, z_ax + lm_top]) mirror([0, 0, 1]) translate([-mx, -ax_y, 0]) children();
  else if (p == "sleeve")      translate([-mx, -ax_y, lens_z]) mirror([0, 0, 1]) children();  // seat face down
  else if (p == "lens_cap")    translate([0, 0, 2]) rotate([180, 0, 0]) translate([-mx, -ax_y, -lens_z]) children();   // ring on the bed, tube up
  else children();
}
module show_print(p) {   // as show(), but untilted
  if (p == "barrel") barrel(); else if (p == "disp_holder") disp_holder(); else if (p == "lens_mount") lens_mount();
  else if (p == "sleeve") sleeve(); else if (p == "lens_cap") lens_cap(); else show(p);
}

// ---------------------------------------------------------------- pins in their assembled positions (viewer / checks)
module barrel_pins() barrel_pin_frames() lp_place(GRIP_LONG);   // lens mount -> barrel (these turn with the barrel)
module assembled_pins() lid_pins() lp_place($grip);   // lid corners, end cap tabs

if (part == "assembly") {
  color("#3a3f47") base();
  color("#2f343b") batt_base();
  color("#4a505a") batt_plate();
  color("#4a505a") lid();
  color("#2b2f36") tilted() barrel();
  color("#e8743b") tilted() disp_holder();
  color("#2b2f36") end_cap();
  color("#2b2f36") tilted() lens_mount();
  color("#9aa3b0") tilted() sleeve();
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
