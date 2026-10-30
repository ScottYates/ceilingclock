// Ceiling Clock enclosure - parametric OpenSCAD model
//
// Coordinates are the assembled position (mm). Origin = centre of the base footprint,
// z = 0 at the bottom of the feet, front of the clock faces -Y.
//
// Render one part:   openscad -D 'part="base"' -D 'print=true' -o base.stl enclosure.scad
// Parts: base lid lightbox carriage lens_mount sleeve lens_cap ring_holder dome pins (snap pins + focus pins)
// No screws: the lid, lens mount and ring holder are held by printed snap pins; the circuit board snaps under hooks.
// Bought components (not printed, for the 3D viewer): see components.scad. Add -D 'mat="..."' to
//   render one material of a component, e.g. -D 'part="ref_tm1637"' -D 'mat="led_red"'.
//
// Folded projector: the LED, diffuser and LCD sit in a light box along the back of the base and shine
// toward +X. A 45 degree front-surface mirror at the far end turns the light straight up through the
// lens, which sits in a short sleeve on the lid. Focus by sliding the sleeve up or down.

part = "assembly";
print = false;     // true = move/rotate the part into its printing orientation
$fn = 64;
eps = 0.01;

// ---------------------------------------------------------------- main dimensions
box_w = 170;  box_d = 120;          // footprint
feet_h = 6;   floor_t = 2.5;        // feet raise the floor so the downward speaker can breathe
wall = 2.5;   corner_r = 6;
base_top = 64;                      // top edge of the base walls
lid_t = 3;
lid_top = base_top + lid_t;         // 67
floor_top = feet_h + floor_t;       // 8.5
post_xy = [box_w/2 - 6 - wall/2, box_d/2 - 6 - wall/2];  // lid posts (x, y)

// snap pins: split shaft with a barb. All joints use the same pin (grip = clamped thickness).
pin_d = 4.0;  pin_hole = 4.25;  pin_barb = 0.45;  pin_tip = 2.6;  pin_slot = 1.1;
pin_head_d = 7.5;  pin_head_t = 1.2;  pin_recess = 8.1;   // counterbore for the head
pin_catch = 4;                                         // how far the pin enters a lid post
pin_grip = lid_t - pin_head_t + pin_catch;             // 5.8 mm, same for every joint

// ---------------------------------------------------------------- folded optics
// Light runs along +X at height z_ax, centre line y = ax_y. Mirror centre at x = mx, lens straight above it.
lens_v = 106;                    // lens-to-LCD distance for a 100 mm lens and ~1.8 m throw
lb_in = 51;  lb_wall = 2;  lb_w = lb_in + 2 * lb_wall;     // light box: inside width fits the 50 mm mirror
ax_y = box_d/2 - wall - lb_w/2;                            // 30: the light box sits against the back wall
lb_z0 = floor_top;  lb_floor_top = lb_z0 + 2;  lb_top = base_top - 0.2;   // walls reach the lid, which is its roof
cg_floor = 2;                                              // carriage floor
z_ax = lb_floor_top + cg_floor + 22.5;                     // 35: centre of the 45 mm LCD board
mirror_L = 50;  mirror_W = 50;  mirror_t = 1.1;            // 50 x 50 x 1.1 mm front-surface mirror
mx = 40;                                                   // mirror centre x = lens x
lens_d = 50.5;  lens_seat = 3;  lens_clear = 46;
lens_c = 78;                                               // nominal lens centre height (focus range about +/-5)
lens_z = lens_c + lens_seat;                               // top of the lens seat = top of the sleeve
lcd_x = mx - (lens_v - (lens_c - z_ax));                   // -23: LCD pixel plane
led_x = lcd_x - 31;                                        // back of the LED star
diff_x = led_x + 10.5;                                     // diffuser
cg_x0 = led_x - 3;  cg_x1 = lcd_x + 4.5;  cg_w = lb_in - 0.6;  cg_top = 60;
mh = mirror_L / 2 / sqrt(2);                               // half the mirror's x (and z) extent
lb_x0 = cg_x0 - 0.3 - lb_wall;                             // -59.3
lb_x1 = mx + mh + mirror_t + 2.5 + lb_wall;                // end wall behind the mirror
// lens mount on the lid: socket the sleeve slides in, two snap-pin tabs
sl_od = 55;  sl_h = 9;
lm_wall = 2.2;  lm_id = sl_od + 0.4;  lm_od = lm_id + 2 * lm_wall;  lm_h = 22;  lm_tab = lm_od/2 + 5;  lm_flange_t = 4;
lid_lens_hole = 45;

// other lid features
ring_xy = [-45, -20];  ring_pin_r = 11;   ring_od = 44.5; ring_id = 31.5;  dome_d = 60;  dome_h = 20;
button_xy = [0, -25]; button_hole = 16.2;
ldr_xy = [60, -45];                      // well clear of the corner pins, the dome and the lens mount
// front display: TM1637 4-digit module. Set to "0.36" (42 x 24 mm board, default) or "0.56" (~50 mm display).
tm_size = "0.36";
tm_disp = tm_size == "0.56" ? [50.4, 19, 8] : [30.2, 14.2, 7.2];   // display face w, h, depth from the board
tm_board = tm_size == "0.56" ? [53, 25] : [42, 24];                // module PCB w, h
tm_w = tm_disp[0] + 1; tm_h = tm_disp[1] + 1; tm_z = 38;          // front window
tm_pcb_y = -box_d/2 + wall + tm_disp[2];                          // PCB plane (display face against the wall)
// left side panel: USB-C power and button B
usb_y = -36;  usb_z = 18;  btnb_y = -15;  btnb_z = 40;
// circuit board: 70 x 50 mm perfboard resting on 4 pads, held by 4 snap hooks on its short edges
pb_xy = [45, -23];  pb_size = [70, 50];  pb_hole = [66, 46];  pb_boss_h = 12;
pb_top = feet_h + floor_t + pb_boss_h + 1.6;           // top surface of the board
hook_t = 1.4;  hook_lip = 0.9;  hook_w = 8;  hook_dy = 12;
// speaker (40 mm), facing down through the floor
spk_xy = [-48, -20];  spk_d = 40.5;
// pegs on the base floor that locate the light box
lb_pegs = [[-35, ax_y], [5, ax_y]];

// ---------------------------------------------------------------- helpers
module rrect(w, d, h, r) {
  linear_extrude(h) offset(r) square([w - 2*r, d - 2*r], center = true);
}
module mirror_frame() translate([mx, ax_y, z_ax]) rotate([0, -45, 0]) children();   // local +z = mirror front normal

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
      for (sx = [-1, 1], sy = [-1, 1])
        translate([sx * post_xy[0], sy * post_xy[1], feet_h]) cylinder(r = 4.5, h = base_top - feet_h);
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
      // light box locating pegs
      for (p = lb_pegs) translate([p[0], p[1], floor_top - eps]) cylinder(d = 4, h = 1.8, $fn = 24);
    }
    // lid pin holes: straight bore, then a wider pocket the barb snaps into
    for (sx = [-1, 1], sy = [-1, 1]) translate([sx * post_xy[0], sy * post_xy[1], 0]) {
      translate([0, 0, base_top - pin_catch - eps]) cylinder(d = pin_hole, h = pin_catch + 1);
      translate([0, 0, base_top - pin_catch - pin_tip - 0.8]) cylinder(d = pin_d + 2 * pin_barb + 0.5, h = pin_tip + 0.8);
    }
    // front display window
    translate([-tm_w/2, -box_d/2 - 1, tm_z - tm_h/2]) cube([tm_w, wall + 2, tm_h]);
    // left side: USB-C, button B, vents next to the LED end of the light box
    translate([-box_w/2 - 1, usb_y - 5, usb_z - 2.25]) cube([wall + 2, 10, 4.5]);
    translate([-box_w/2 - 1, btnb_y, btnb_z]) rotate([0, 90, 0]) cylinder(d = button_hole, h = wall + 2);
    for (i = [0:4]) translate([-box_w/2 - 1, 12 + i * 8, 16]) cube([wall + 2, 3, 38]);
    // right side vents by the circuit board
    for (i = [0:4]) translate([box_w/2 - wall - 1, -40 + i * 8, 28]) cube([wall + 2, 3, 24]);
    // speaker grille
    translate([spk_xy[0], spk_xy[1], -1])
      for (r = [0, 7, 14], a = [0 : (r == 0 ? 360 : 360 / (r * 0.9)) : 359])
        rotate(a) translate([r, 0, 0]) cylinder(d = 3.5, h = feet_h + floor_t + 2, $fn = 16);
  }
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

// ---------------------------------------------------------------- lid
module lid() {
  difference() {
    translate([0, 0, base_top]) rrect(box_w, box_d, lid_t, corner_r);
    // pin holes with a recess so the pin heads sit flush
    for (sx = [-1, 1], sy = [-1, 1]) translate([sx * post_xy[0], sy * post_xy[1], base_top - 1]) {
      cylinder(d = pin_hole, h = 10);
      translate([0, 0, 1 + lid_t - pin_head_t]) cylinder(d = pin_recess, h = 10);
    }
    // light comes up from the mirror here; lens mount pins either side
    translate([mx, ax_y, base_top - 1]) {
      cylinder(d = lid_lens_hole, h = 10);
      for (s = [-1, 1]) translate([s * lm_tab, 0, 0]) cylinder(d = pin_hole, h = 10);
    }
    // sunrise ring: wire hole + holder pins
    translate([ring_xy[0], ring_xy[1], base_top - 1]) {
      cylinder(d = 10, h = 10);
      for (a = [90, 210, 330]) rotate(a) translate([ring_pin_r, 0, 0]) cylinder(d = pin_hole, h = 10);
    }
    translate([button_xy[0], button_xy[1], base_top - 1]) cylinder(d = button_hole, h = 10);
    translate([ldr_xy[0], ldr_xy[1], base_top - 1]) cylinder(d = 5.2, h = 10);
  }
}

// ---------------------------------------------------------------- light box (along the back of the base)
module lightbox() {
  difference() {
    union() {
      difference() {
        translate([lb_x0, ax_y - lb_w/2, lb_z0]) cube([lb_x1 - lb_x0, lb_w, lb_top - lb_z0]);
        lb_inside();
      }
      // 45 degree ramp the mirror lies on, and a stop at its lower edge
      intersection() {
        lb_inside();
        mirror_frame() union() {
          translate([-200, -100, -200]) cube([400, 200, 200 - mirror_t]);
          translate([-mirror_L/2 - 3, -100, -mirror_t - 1]) cube([3, 200, mirror_t + 3]);
        }
      }
      // ribs on the floor that stop the carriage sliding forward
      for (s = [-1, 1]) translate([cg_x1 + 0.3, ax_y + s * (lb_in/2 - 4) - 2, lb_floor_top - eps]) cube([3, 4, 4]);
    }
    // locating holes for the pegs in the base floor
    for (p = lb_pegs) translate([p[0], p[1], lb_z0 - 1]) cylinder(d = 4.5, h = 4, $fn = 24);
    // air slots in the back wall, behind the LED
    for (i = [-2:2]) translate([lb_x0 - 1, ax_y + i * 8 - 1.5, 16]) cube([lb_wall + 2, 3, 38]);
    // notch in the top of the front wall for the LED and LCD leads
    translate([lcd_x - 24, ax_y - lb_w/2 - 1, lb_top - 9]) cube([26, lb_wall + 2, 10]);
  }
}
module lb_inside() translate([lb_x0 + lb_wall, ax_y - lb_in/2, lb_floor_top]) cube([lb_x1 - lb_x0 - 2 * lb_wall, lb_in, 100]);

// ---------------------------------------------------------------- carriage (LED + diffuser + LCD), slides into the light box
module carriage() {
  difference() {
    translate([cg_x0, ax_y - cg_w/2, lb_floor_top]) cube([cg_x1 - cg_x0, cg_w, cg_top - lb_floor_top]);
    // light chamber, open at the front
    translate([cg_x0 + 3, ax_y - 22, lb_floor_top + cg_floor]) cube([cg_x1 - cg_x0, 44, cg_top - lb_floor_top - cg_floor - 2]);
    // above and in front of the LCD it's open so the header and leads clear
    translate([lcd_x - 1.35, ax_y - 22, lb_floor_top + cg_floor]) cube([20, 44, 100]);
    // LED star pocket in the back plate, and holes for air and the LED leads
    translate([led_x - 1, ax_y, z_ax]) rotate([0, 90, 0]) cylinder(d = 20.4, h = 5);
    for (sy = [-1, 1], sz = [-1, 1]) translate([cg_x0 - 1, ax_y + sy * 16, z_ax + sz * 16]) rotate([0, 90, 0]) cylinder(d = 6, h = 10);
    // diffuser slot (46 x 46 mm sheet, dropped in from the top)
    translate([diff_x - 0.6, ax_y - 23.5, lb_floor_top + cg_floor - 0.5]) cube([1.2, 47, 100]);
    // LCD slot: the 45 x 45 mm board drops in from the top, glass facing the mirror
    translate([lcd_x - 3.15, ax_y - 22.8, lb_floor_top + cg_floor]) cube([1.8, 45.6, 100]);
    // hole in the top plate for the LED leads
    translate([led_x + 4, ax_y, cg_top - 5]) cylinder(d = 6, h = 10, $fn = 24);
    // finger notch to lift the carriage out
    translate([(cg_x0 + diff_x) / 2, ax_y, cg_top]) rotate([90, 0, 0]) cylinder(d = 10, h = cg_w + 2, center = true);
  }
}

// ---------------------------------------------------------------- lens mount (on the lid), sleeve and cap
module lens_mount() {
  translate([mx, ax_y, lid_top]) difference() {
    union() {
      cylinder(d = lm_od, h = lm_h, $fn = 96);
      hull() for (s = [-1, 1]) translate([s * lm_tab, 0, 0]) cylinder(d = 12, h = lm_flange_t);
    }
    translate([0, 0, -1]) cylinder(d = lm_id, h = lm_h + 2, $fn = 96);
    for (s = [-1, 1]) translate([s * lm_tab, 0, -1]) {
      cylinder(d = pin_hole, h = 10);
      translate([0, 0, 1 + lm_flange_t - pin_head_t]) cylinder(d = pin_recess, h = 10);
    }
    // focus lock: a tapered printed pin pushed through this hole presses on the sleeve
    translate([0, -lm_od/2 - 1, lm_h - 7]) rotate([-90, 0, 0]) cylinder(d = pin_hole, h = lm_wall + 2);
  }
}

module sleeve() {
  translate([mx, ax_y, lens_z - sl_h]) difference() {
    cylinder(d = sl_od, h = sl_h, $fn = 96);
    translate([0, 0, -1]) cylinder(d = lens_clear, h = sl_h + 2, $fn = 96);    // light path
    translate([0, 0, sl_h - lens_seat]) cylinder(d = lens_d, h = 10, $fn = 96); // lens seat
  }
}

module lens_cap() {
  translate([mx, ax_y, lens_z]) difference() {
    cylinder(d = sl_od, h = 3, $fn = 96);
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

// Focus lock: tapered so it wedges in the lens mount hole; the tip presses on the sleeve.
module focus_pin() {
  flat = pin_d / 2 - 0.5;
  intersection() {
    union() {
      translate([0, 0, -2]) cylinder(d = 9, h = 2, $fn = 48);            // finger tab
      cylinder(d1 = pin_hole + 0.35, d2 = pin_d - 0.2, h = lm_wall + 1.2, $fn = 40);
    }
    translate([-50, -flat, -50]) cube([100, 2 * flat, 100]);
  }
}

// Print plate: 12 snap pins (9 needed + spares) and 2 focus pins, lying on their flats.
module pin_plate() {
  flat = pin_d / 2 - 0.5;
  for (i = [0:11]) translate([(i % 6) * 11, floor(i / 6) * 16, flat]) rotate([90, 0, 0]) snap_pin();
  for (i = [0:1]) translate([i * 13, 34, flat]) rotate([90, 0, 0]) focus_pin();
}

// ---------------------------------------------------------------- bought components (viewer only, not printed)
include <components.scad>

// ---------------------------------------------------------------- dispatch
module show(p) {
  if (p == "base") base();
  else if (p == "lid") lid();
  else if (p == "lightbox") lightbox();
  else if (p == "carriage") carriage();
  else if (p == "lens_mount") lens_mount();
  else if (p == "sleeve") sleeve();
  else if (p == "lens_cap") lens_cap();
  else if (p == "ring_holder") ring_holder();
  else if (p == "dome") dome();
  else if (p == "pins") pin_plate();
  else if (p == "pin") snap_pin();
  else if (p == "ref_esp32") ref_esp32();
  else if (p == "ref_perfboard") ref_perfboard();
  else if (p == "ref_lcd") ref_lcd();
  else if (p == "ref_led") ref_led();
  else if (p == "ref_lens") ref_lens();
  else if (p == "ref_mirror") ref_mirror();
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
}

// Printing orientation: lay each part on the bed at z = 0.
module print_pose(p) {
  if (p == "sleeve")           translate([-mx, -ax_y, lens_z]) mirror([0, 0, 1]) children();  // seat face down
  else if (p == "lid")         translate([0, 0, -base_top]) children();
  else if (p == "lightbox")    translate([0, -ax_y, -lb_z0]) children();
  else if (p == "carriage")    translate([0, -ax_y, -lb_floor_top]) children();
  else if (p == "lens_mount")  translate([-mx, -ax_y, -lid_top]) children();
  else if (p == "lens_cap")    translate([-mx, -ax_y, -lens_z]) children();
  else if (p == "ring_holder") translate([-ring_xy[0], -ring_xy[1], -lid_top]) children();
  else if (p == "dome")        translate([-ring_xy[0], -ring_xy[1], -lid_top - 3.5]) children();
  else children();
}

// ---------------------------------------------------------------- pins in their assembled positions (viewer / checks)
module assembled_pins() {
  // lid -> base posts
  for (sx = [-1, 1], sy = [-1, 1])
    translate([sx * post_xy[0], sy * post_xy[1], lid_top - pin_head_t]) rotate([180, 0, 0]) snap_pin();
  // lens mount -> lid
  for (s = [-1, 1])
    translate([mx + s * lm_tab, ax_y, lid_top + lm_flange_t - pin_head_t]) rotate([180, 0, 0]) snap_pin();
  // ring holder -> lid
  for (a = [90, 210, 330]) translate([ring_xy[0], ring_xy[1], 0]) rotate(a)
    translate([ring_pin_r, 0, lid_top + 1 + lid_t - pin_head_t + pin_catch - lid_t - 1]) rotate([180, 0, 0]) snap_pin();
}

if (part == "assembly") {
  color("#3a3f47") base();
  color("#4a505a") lid();
  color("#2b2f36") lightbox();
  color("#7a8290") carriage();
  color("#2b2f36") lens_mount();
  color("#9aa3b0") sleeve();
  color("#f0f0f0", 0.6) dome();
  color("#2a6") ref_perfboard();
  color("#246") ref_esp32();
  color("#c33") ref_lcd();
  color("#ddd") ref_led();
  color("#eef") ref_mirror();
  color("#9cf", 0.5) ref_lens();
} else if (part == "joint_check") {
  base(); lid(); assembled_pins();
} else if (print) {
  print_pose(part) show(part);
} else {
  show(part);
}
