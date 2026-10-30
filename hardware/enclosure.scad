// Ceiling Clock enclosure - parametric OpenSCAD model
//
// Coordinates are the assembled position (mm). Origin = centre of the base footprint,
// z = 0 at the bottom of the feet, front of the clock faces -Y.
//
// Render one part:   openscad -D 'part="base"' -D 'print=true' -o base.stl enclosure.scad
// Parts: base lid tower carrier sleeve lens_cap ring_holder dome
// Reference (not printed, for the 3D viewer): ref_esp32 ref_perfboard ref_lcd ref_led ref_lens
//   ref_ring ref_speaker ref_tm1637 ref_amp ref_rtc ref_mosfet ref_button ref_usbc

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
post_xy = [69 - wall/2, 49 - wall/2];  // lid screw posts (x, y)

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
ring_xy = [-42, 5];   ring_od = 44.5; ring_id = 31.5;  dome_d = 60;  dome_h = 32;
button_xy = [0, -42]; button_hole = 16.2;
ldr_xy = [-65, -45];
// front display window
tm_w = 42; tm_h = 18; tm_z = 32;
// rear panel
usbc_x = -45;  btnb_x = -25;  rear_z = 20;
// perfboard bosses (70 x 50 board, 66 x 46 hole spacing)
pb_xy = [22, 0];  pb_hole = [66, 46];  pb_boss_h = 6;
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
      // perfboard bosses
      for (sx = [-1, 1], sy = [-1, 1])
        translate([pb_xy[0] + sx * pb_hole[0]/2, pb_xy[1] + sy * pb_hole[1]/2, feet_h])
          cylinder(d = 7, h = floor_t + pb_boss_h);
      // speaker retaining ring
      translate([spk_xy[0], spk_xy[1], feet_h]) difference() {
        cylinder(d = spk_d + 4, h = floor_t + 5);
        cylinder(d = spk_d, h = 20);
      }
      // TM1637 rails behind the front window (PCB slides down into the slots)
      for (sx = [-1, 1]) translate([sx * (tm_w/2 + 2.5) - 2.5, -box_d/2 + wall - eps, tm_z - 16])
        difference() {
          cube([5, 12, 30]);
          translate([sx > 0 ? -eps : 2.5, 7.5 - 0.9, 3]) cube([2.5 + eps, 1.8, 30]);
        }
      // small cradle for the USB-C breakout
      translate([usbc_x - 9, box_d/2 - wall - 14, feet_h]) cube([18, 14, floor_t + rear_z - 3.5 - feet_h - 1.6]);
    }
    // lid screw pilot holes (M3 self-tapping)
    for (sx = [-1, 1], sy = [-1, 1])
      translate([sx * post_xy[0], sy * post_xy[1], base_top - 12]) cylinder(d = 2.5, h = 13);
    // perfboard pilot holes
    for (sx = [-1, 1], sy = [-1, 1])
      translate([pb_xy[0] + sx * pb_hole[0]/2, pb_xy[1] + sy * pb_hole[1]/2, feet_h + 1]) cylinder(d = 2.5, h = 20);
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

// ---------------------------------------------------------------- lid
module lid() {
  difference() {
    translate([0, 0, base_top]) rrect(box_w, box_d, lid_t, corner_r);
    // screw holes, countersunk
    for (sx = [-1, 1], sy = [-1, 1]) translate([sx * post_xy[0], sy * post_xy[1], base_top - 1]) {
      cylinder(d = 3.4, h = 10);
      translate([0, 0, 1 + lid_t - 1.8]) cylinder(d1 = 3.4, d2 = 6.6, h = 1.8 + eps);
    }
    // tower opening and flange screws
    translate([tower_xy[0], tower_xy[1], base_top - 1]) {
      rsquare(tower_in - 2*lip, 10, 3);
      for (sx = [-1, 1], sy = [-1, 1]) translate([sx * flange_hole, sy * flange_hole, 0]) cylinder(d = 2.5, h = 10);
    }
    // sunrise ring: wire hole + holder screws
    translate([ring_xy[0], ring_xy[1], base_top - 1]) {
      cylinder(d = 10, h = 10);
      for (a = [90, 210, 330]) rotate(a) translate([dome_d/2 - 4, 0, 0]) cylinder(d = 2.5, h = 10);
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
    // flange screws, counterbored
    for (sx = [-1, 1], sy = [-1, 1]) translate([sx * flange_hole, sy * flange_hole, -1]) {
      cylinder(d = 3.4, h = 10);
      translate([0, 0, flange_t - 1.5 + 1]) cylinder(d = 6.5, h = 10);
    }
    // focus lock screw (M3) near the top, on the +X side
    translate([tower_out/2 - 4, 0, tower_h - 12]) rotate([0, 90, 0]) cylinder(d = 2.5, h = 10);
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
    for (a = [90, 210, 330]) rotate(a) translate([dome_d/2 - 4, 0, -1]) {
      cylinder(d = 3.4, h = 10);
      translate([0, 0, 4]) cylinder(d = 6.5, h = 10);
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

// ---------------------------------------------------------------- reference components (not printed)
module ref_esp32()     translate([pb_xy[0] - 31.5, pb_xy[1] - 12.75, feet_h + floor_t + pb_boss_h + 1.6 + 8]) cube([63, 25.5, 1.6]);
module ref_perfboard() translate([pb_xy[0], pb_xy[1], feet_h + floor_t + pb_boss_h + 0.8]) cube([70, 50, 1.6], center = true);
module ref_lcd() {
  z = lid_top + lip + carrier_h - 6;
  translate([tower_xy[0], tower_xy[1], z]) {
    translate([0, 0, 0.8]) cube([45, 45, 1.6], center = true);
    translate([0, -2, 1.6 + 2]) cube([40, 34, 4], center = true);
  }
}
module ref_led()  translate([tower_xy[0], tower_xy[1], lid_top + lip + 1.5]) { cylinder(d = 20, h = 1.6); translate([0, 0, 1.6]) cylinder(d = 6, h = 2.5); }
module ref_lens() translate([tower_xy[0], tower_xy[1], lens_z - lens_seat]) scale([1, 1, 0.16]) sphere(d = 50);
module ref_ring() translate([ring_xy[0], ring_xy[1], lid_top + 1.5]) difference() { cylinder(d = ring_od, h = 1.6); translate([0, 0, -1]) cylinder(d = ring_id, h = 4); }
module ref_speaker() translate([spk_xy[0], spk_xy[1], feet_h + floor_t]) { cylinder(d = 40, h = 2); translate([0, 0, 2]) cylinder(d1 = 34, d2 = 18, h = 8); }
module ref_tm1637() translate([0, -box_d/2 + wall, tm_z]) {
  translate([0, 7.5 / 2, 0]) cube([40, 7.5, 16], center = true);
  translate([0, 7.5 + 0.8, 0]) cube([42, 1.6, 24], center = true);
}
module ref_amp()    translate([-15, 30, feet_h + floor_t]) cube([18, 18, 3]);
module ref_rtc()    translate([-15, -35, feet_h + floor_t]) cube([22, 38, 3]);
module ref_mosfet() translate([55, -40, feet_h + floor_t]) cube([17, 34, 6]);
module ref_button() translate([button_xy[0], button_xy[1], lid_top - 18]) { cylinder(d = 16, h = 18); translate([0, 0, 18]) cylinder(d = 19, h = 3); }
module ref_usbc()   translate([usbc_x - 7, box_d/2 - wall - 12, rear_z - 3.5]) cube([14, 12, 1.6]);

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
