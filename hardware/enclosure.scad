// Ceiling Clock enclosure - parametric OpenSCAD model
//
// Coordinates are the assembled position (mm). Origin = centre of the base footprint,
// z = 0 at the bottom of the feet, front of the clock faces -Y.
//
// Render one part:   openscad -D 'part="base"' -D 'print=true' -o base.stl enclosure.scad
// Parts: base lid tower carrier sleeve lens_cap ring_holder dome pins (plate of snap pins + focus pins)
// No screws: the lid, tower and ring holder are held by printed snap pins; the circuit board snaps under hooks.
// Bought components (not printed, for the 3D viewer): see components.scad. Add -D 'mat="..."' to
//   render one material of a component, e.g. -D 'part="ref_tm1637"' -D 'mat="led_red"'.

part = "assembly";
print = false;     // true = move/rotate the part into its printing orientation
$fn = 64;
eps = 0.01;

// ---------------------------------------------------------------- main dimensions
box_w = 150;  box_d = 110;          // footprint
feet_h = 6;   floor_t = 2.5;        // feet raise the floor so the downward speaker can breathe
wall = 2.5;   corner_r = 6;
base_top = 56;                      // top edge of the base walls
lid_t = 3;
lid_top = base_top + lid_t;         // 59
post_xy = [69 - wall/2, 49 - wall/2];  // lid posts (x, y)

// snap pins: split shaft with a barb. All joints use the same pin (grip = clamped thickness).
pin_d = 4.0;  pin_hole = 4.25;  pin_barb = 0.45;  pin_tip = 2.6;  pin_slot = 1.1;
pin_head_d = 7.5;  pin_head_t = 1.2;  pin_recess = 8.1;   // counterbore for the head
pin_catch = 4;                                         // how far the pin enters a lid post
pin_grip = lid_t - pin_head_t + pin_catch;             // 5.8 mm, same for every joint

// tower / optics
tower_xy = [30, 8];
tower_out = 62;  tower_in = 56;  tower_h = 140;
flange = 74;  flange_t = 4;  flange_hole = 31;  // holes at +/-31
lip = 2;                                 // ledge inside the tower bottom the carrier sits on
carrier_out = tower_in - 0.6;  carrier_h = 36;
sleeve_out = tower_in - 0.6;   sleeve_h = 60;
lens_d = 50.5;  lens_seat = 3;  lens_clear = 46;
lens_z = 201;                            // lens height for a 100 mm lens (slide to focus)

// other lid features
ring_xy = [-42, 5];   ring_pin_r = 11;   ring_od = 44.5; ring_id = 31.5;  dome_d = 60;  dome_h = 32;
button_xy = [0, -42]; button_hole = 16.2;
ldr_xy = [-65, -45];
// front display: TM1637 4-digit module. Set to "0.36" (42 x 24 mm board, default) or "0.56" (~50 mm display).
tm_size = "0.36";
tm_disp = tm_size == "0.56" ? [50.4, 19, 8] : [30.2, 14.2, 7.2];   // display face w, h, depth from the board
tm_board = tm_size == "0.56" ? [53, 25] : [42, 24];                // module PCB w, h
tm_w = tm_disp[0] + 1; tm_h = tm_disp[1] + 1; tm_z = 32;          // front window
tm_pcb_y = -box_d/2 + wall + tm_disp[2];                          // PCB plane (display face against the wall)
// rear panel
usbc_x = -45;  btnb_x = -25;  rear_z = 20;
// circuit board: 70 x 50 mm perfboard resting on 4 pads, held by 4 snap hooks
pb_xy = [22, 0];  pb_size = [70, 50];  pb_hole = [66, 46];  pb_boss_h = 12;
pb_top = feet_h + floor_t + pb_boss_h + 1.6;           // top surface of the board
hook_t = 1.4;  hook_lip = 0.9;  hook_w = 8;
// speaker (40 mm), facing down through the floor
spk_xy = [-42, 5];  spk_d = 40.5;

// ---------------------------------------------------------------- helpers
module rrect(w, d, h, r) {
  linear_extrude(h) offset(r) square([w - 2*r, d - 2*r], center = true);
}
module rsquare(s, h, r) { rrect(s, s, h, r); }

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
      // lid screw posts
      for (sx = [-1, 1], sy = [-1, 1])
        translate([sx * post_xy[0], sy * post_xy[1], feet_h]) cylinder(r = 4.5, h = base_top - feet_h);
      // circuit board support pads (under the corners) and snap hooks (on the long edges)
      for (sx = [-1, 1], sy = [-1, 1])
        translate([pb_xy[0] + sx * pb_hole[0]/2, pb_xy[1] + sy * pb_hole[1]/2, feet_h])
          cylinder(d = 7, h = floor_t + pb_boss_h);
      for (sy = [-1, 1], dx = [-20, 20]) board_hook(pb_xy[0] + dx, sy);
      // speaker retaining ring
      translate([spk_xy[0], spk_xy[1], feet_h]) difference() {
        cylinder(d = spk_d + 4, h = floor_t + 5);
        cylinder(d = spk_d, h = 20);
      }
      // TM1637 rails behind the front window: the PCB edges slide down into the slots
      for (sx = [-1, 1]) translate([sx * (tm_board[0]/2 + 1) - 3, -box_d/2 + wall - eps, tm_z - tm_board[1]/2 - 3])
        difference() {
          cube([6, tm_disp[2] + 4, tm_board[1] + 6]);
          translate([sx > 0 ? -eps : 3.5, tm_pcb_y - (-box_d/2 + wall) - 0.9, 3]) cube([2.5 + eps, 1.8, tm_board[1] + 10]);
        }
      // small cradle for the USB-C breakout
      translate([usbc_x - 9, box_d/2 - wall - 14, feet_h]) cube([18, 14, floor_t + rear_z - 3.5 - feet_h - 1.6]);
    }
    // lid pin holes: straight bore, then a wider pocket the barb snaps into
    for (sx = [-1, 1], sy = [-1, 1]) translate([sx * post_xy[0], sy * post_xy[1], 0]) {
      translate([0, 0, base_top - pin_catch - eps]) cylinder(d = pin_hole, h = pin_catch + 1);
      translate([0, 0, base_top - pin_catch - pin_tip - 0.8]) cylinder(d = pin_d + 2 * pin_barb + 0.5, h = pin_tip + 0.8);
    }
    // front display window
    translate([-tm_w/2, -box_d/2 - 1, tm_z - tm_h/2]) cube([tm_w, wall + 2, tm_h]);
    // rear: USB-C, button B, vents
    translate([usbc_x - 5, box_d/2 - wall - 1, rear_z - 2.25]) cube([10, wall + 2, 4.5]);
    translate([btnb_x, box_d/2 + 1, rear_z]) rotate([90, 0, 0]) cylinder(d = 16.2, h = wall + 2);
    for (i = [0:6]) translate([5 + i * 8, box_d/2 - wall - 1, 30]) cube([3, wall + 2, 18]);
    // side vents under the tower (cool air for the LED)
    for (i = [0:5]) translate([box_w/2 - wall - 1, -20 + i * 8, 15]) cube([wall + 2, 3, 30]);
    // speaker grille
    translate([spk_xy[0], spk_xy[1], -1])
      for (r = [0, 7, 14], a = [0 : (r == 0 ? 360 : 360 / (r * 0.9)) : 359])
        rotate(a) translate([r, 0, 0]) cylinder(d = 3.5, h = feet_h + floor_t + 2, $fn = 16);
  }
}

// Snap hook on a long edge of the circuit board (side = +1 back, -1 front)
module board_hook(x, side) {
  edge_y = pb_xy[1] + side * (pb_size[1]/2 + 0.25);
  z0 = feet_h + floor_t - eps;
  translate([x - hook_w/2, side > 0 ? edge_y : edge_y - hook_t, z0]) cube([hook_w, hook_t, pb_top + 2.6 - z0]);
  // lip: flat catch on the underside, ramp on top
  translate([x - hook_w/2, edge_y, 0]) rotate([90, 0, 90]) linear_extrude(hook_w)
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
    // tower opening and flange screws
    translate([tower_xy[0], tower_xy[1], base_top - 1]) {
      rsquare(tower_in - 2*lip, 10, 3);
      for (sx = [-1, 1], sy = [-1, 1]) translate([sx * flange_hole, sy * flange_hole, 0]) cylinder(d = pin_hole, h = 10);
    }
    // sunrise ring: wire hole + holder screws
    translate([ring_xy[0], ring_xy[1], base_top - 1]) {
      cylinder(d = 10, h = 10);
      for (a = [90, 210, 330]) rotate(a) translate([ring_pin_r, 0, 0]) cylinder(d = pin_hole, h = 10);
    }
    translate([button_xy[0], button_xy[1], base_top - 1]) cylinder(d = button_hole, h = 10);
    translate([ldr_xy[0], ldr_xy[1], base_top - 1]) cylinder(d = 5.2, h = 10);
  }
}

// ---------------------------------------------------------------- projector tower
module tower() {
  translate([tower_xy[0], tower_xy[1], lid_top]) difference() {
    union() {
      rsquare(flange, flange_t, 6);
      rsquare(tower_out, tower_h, 4);
    }
    // bore
    translate([0, 0, lip]) rsquare(tower_in, tower_h, 2);
    // lip opening (light + wires pass through to the base)
    translate([0, 0, -1]) rsquare(tower_in - 2*lip, lip + 2, 2);
    // flange pin holes, recessed for the pin heads
    for (sx = [-1, 1], sy = [-1, 1]) translate([sx * flange_hole, sy * flange_hole, -1]) {
      cylinder(d = pin_hole, h = 10);
      translate([0, 0, 1 + flange_t - pin_head_t]) cylinder(d = pin_recess, h = 10);
    }
    // focus lock: a tapered printed pin pushed through this hole presses on the lens sleeve
    translate([tower_out/2 - 4, 0, tower_h - 12]) rotate([0, 90, 0]) cylinder(d = pin_hole, h = 10);
    // vents at the LED level
    for (sx = [-1, 1]) for (i = [-1, 0, 1])
      translate([sx * tower_out/2, i * 12, 10]) cube([10, 4, 14], center = true);
  }
}

// ---------------------------------------------------------------- optics carrier (LED + diffuser + LCD)
module carrier() {
  z0 = lid_top + lip;
  translate([tower_xy[0], tower_xy[1], z0]) difference() {
    rsquare(carrier_out, carrier_h, 2);
    // light chamber (narrower than the LCD board so the board rests on a ledge)
    translate([0, 0, 3]) rsquare(40, carrier_h, 1);
    // LED star pocket (20 mm) and wire slots in the floor
    translate([0, 0, 1.5]) cylinder(d = 20.4, h = 5);
    for (s = [-1, 1]) translate([s * 13, 0, -1]) cube([4, 10, 10], center = true);
    // floor vents
    for (sx = [-1, 1], sy = [-1, 1]) translate([sx * 17, sy * 17, -1]) cylinder(d = 8, h = 10);
    // diffuser slot (slide a 51 x 51 mm frosted sheet in from the -X side)
    translate([-carrier_out/2 - 1, -25.5, 12]) cube([carrier_out, 51, 1.2]);
    // LCD pocket: module PCB 45.5 x 45.5, sits 6 mm deep at the top
    translate([-22.9, -22.9, carrier_h - 6]) cube([45.8, 45.8, 20]);
    // header/wire notch on the +Y side for the LCD pins
    translate([-16, carrier_out/2 - 6, carrier_h - 14]) cube([32, 10, 20]);
    // side vents
    for (sx = [-1, 1]) translate([sx * carrier_out/2, 0, 8]) cube([10, 30, 6], center = true);
  }
}

// ---------------------------------------------------------------- lens sleeve + cap
module sleeve() {
  translate([tower_xy[0], tower_xy[1], lens_z - sleeve_h]) difference() {
    rsquare(sleeve_out, sleeve_h, 2);
    translate([0, 0, -1]) rsquare(sleeve_out - 4, sleeve_h - 3 + 1, 1);   // open bottom
    translate([0, 0, sleeve_h - lens_seat]) cylinder(d = lens_d, h = 10);  // lens seat
    translate([0, 0, sleeve_h - 10]) cylinder(d = lens_clear, h = 20);    // light path
  }
}

module lens_cap() {
  translate([tower_xy[0], tower_xy[1], lens_z]) difference() {
    rsquare(sleeve_out, 3, 2);
    translate([0, 0, -1]) cylinder(d = lens_clear, h = 10);
    // 4 pegs fit into holes drilled/glued in the sleeve top
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

// Focus lock: tapered so it wedges in the tower hole; the tip presses on the lens sleeve.
module focus_pin() {
  flat = pin_d / 2 - 0.5;
  intersection() {
    union() {
      translate([0, 0, -2]) cylinder(d = 9, h = 2, $fn = 48);            // finger tab
      cylinder(d1 = pin_hole + 0.35, d2 = pin_d - 0.2, h = wall_tower() + 1.2, $fn = 40);
    }
    translate([-50, -flat, -50]) cube([100, 2 * flat, 100]);
  }
}
function wall_tower() = (tower_out - tower_in) / 2;

// Print plate: 14 snap pins (11 needed + spares) and 2 focus pins, lying on their flats.
module pin_plate() {
  flat = pin_d / 2 - 0.5;
  for (i = [0:13]) translate([(i % 7) * 11, floor(i / 7) * 16, flat]) rotate([90, 0, 0]) translate([0, 0, 0]) snap_pin();
  for (i = [0:1]) translate([i * 13, 34, flat]) rotate([90, 0, 0]) focus_pin();
}

// ---------------------------------------------------------------- bought components (viewer only, not printed)
include <components.scad>

// ---------------------------------------------------------------- dispatch
module show(p) {
  if (p == "base") base();
  else if (p == "lid") lid();
  else if (p == "tower") tower();
  else if (p == "carrier") carrier();
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
}

// Printing orientation: lay each part on the bed at z = 0.
module print_pose(p) {
  if (p == "sleeve")           translate([-tower_xy[0], -tower_xy[1], lens_z]) mirror([0, 0, 1]) children();  // seat face down
  else if (p == "lid")         translate([0, 0, -base_top]) children();
  else if (p == "tower")       translate([-tower_xy[0], -tower_xy[1], -lid_top]) children();
  else if (p == "carrier")     translate([-tower_xy[0], -tower_xy[1], -lid_top - lip]) children();
  else if (p == "lens_cap")    translate([-tower_xy[0], -tower_xy[1], -lens_z]) children();
  else if (p == "ring_holder") translate([-ring_xy[0], -ring_xy[1], -lid_top]) children();
  else if (p == "dome")        translate([-ring_xy[0], -ring_xy[1], -lid_top - 3.5]) children();
  else children();
}

if (part == "assembly") {
  color("#3a3f47") base();
  color("#4a505a") lid();
  color("#2b2f36") tower();
  color("#7a8290") carrier();
  color("#9aa3b0") sleeve();
  color("#f0f0f0", 0.6) dome();
  color("#2a6") ref_perfboard();
  color("#246") ref_esp32();
  color("#c33") ref_lcd();
  color("#ddd") ref_led();
  color("#9cf", 0.5) ref_lens();
} else if (print) {
  print_pose(part) show(part);
} else {
  show(part);
}

// ---------------------------------------------------------------- pins in their assembled positions (viewer / checks)
module assembled_pins() {
  // lid -> base posts
  for (sx = [-1, 1], sy = [-1, 1])
    translate([sx * post_xy[0], sy * post_xy[1], lid_top - pin_head_t]) rotate([180, 0, 0]) snap_pin();
  // tower flange -> lid
  for (sx = [-1, 1], sy = [-1, 1])
    translate([tower_xy[0] + sx * flange_hole, tower_xy[1] + sy * flange_hole, lid_top + flange_t - pin_head_t]) rotate([180, 0, 0]) snap_pin();
  // ring holder -> lid
  for (a = [90, 210, 330]) translate([ring_xy[0], ring_xy[1], 0]) rotate(a)
    translate([ring_pin_r, 0, lid_top + 1 + lid_t - pin_head_t + pin_catch - lid_t - 1]) rotate([180, 0, 0]) snap_pin();
}
if (part == "pins_asm") assembled_pins();
if (part == "joint_check") { base(); lid(); assembled_pins(); }
