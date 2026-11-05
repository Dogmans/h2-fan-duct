$fn = 100;
rod_gap = 23;
bearing_length = 45;
h2_height = 35;
h2_depth = 35;
h2_length = 61.9;

// bearings vs body
top_offset_up = 25;
top_offset_right = 13;

bearing_surround_dia = 23;

module bearing_surround(dia=23) {
    cylinder(h=bearing_length, d=dia, center=true);
}

module bearing_hole() {
    cylinder(h=bearing_length, d=15.3, center=true);
}

module bolt_hole() {
    cylinder(d=3.2, h=100, center=true);
}

module mount_hole(x, y, z) {
    mount_hole_height = 100;
    translate([x, y, z + mount_hole_height / 2]) {
        bolt_hole();
        translate([0, 0, 7])
            cylinder(h=100, d=6.5, center=true);
    }
}

module tie_slot(x, y, z) {
    translate([x, y, z])
        difference() {
            cylinder(h=3, d=21, center=true);
            cylinder(h=3, d=17, center=true);
    }
}

module h2() {
    // zero point is between holes
    difference() {
        color("black")
            translate([-35/2, 37.4-h2_length, -h2_height/2])
                    cube([h2_depth, h2_length, h2_height]);
        translate([-7.5, 0, 0])
                bolt_hole();
        translate([7.5, 0, 0])
                bolt_hole();
        translate([0, 0, 7.5])
                rotate([0, 90, 0])
                    bolt_hole();
        translate([0, 0, -7.5])
                rotate([0, 90, 0])
                    bolt_hole();
    }
}

module bearing_holder_top() {
    back_offset = (-h2_depth + bearing_length) / 2;
    difference() {
        hull() {
                // the surround
                translate([back_offset, -top_offset_right, h2_height/2 + top_offset_up])
                    rotate([0, 90, 0])
                        bearing_surround(23);
                // bracket
                bracket_height = 2;
                translate([0, 0, (h2_height+bracket_height)/2])
                    cube([h2_depth, 10, bracket_height], center=true);
        }
        translate([back_offset, -top_offset_right, h2_height/2 + top_offset_up])
                rotate([0, 90, 0])
                    bearing_hole();
        mount_hole(7.5, 0, h2_height / 2);
        mount_hole(-7.5, 0, h2_height / 2);
        
        // cable tie slots
        translate([back_offset, -top_offset_right, h2_height/2 + top_offset_up])
                    rotate([0, 90, 0]) {
            tie_slot(0, 0, 5-bearing_length/2);
            tie_slot(0, 0, bearing_length/2-5);
        }
        
        // slice off top
        translate([0, 0, h2_height/2 + top_offset_up + 50 + 2])
            cube([100, 100, 100], center=true);

        // Make space for the back with some clearance
        bearing_holder_back(23.6);
    }
}

module bearing_holder_back(surround_dia=23) {
    // N.B. setting dia other than 23 is just used for subtracting for clearance in bearing_holder_top
    difference() {
        hull() {
            translate([(16 + h2_depth)/2, 0, 0])
                cube([16, bearing_length, surround_dia + 12], center=true);
            
            translate([(23 + h2_depth)/2, 0, h2_height/2 + top_offset_up - rod_gap])
                rotate([90, 0, 0])
                    bearing_surround(surround_dia);
        }
        translate([(23 + h2_depth)/2, 0, h2_height/2 + top_offset_up - rod_gap])
            rotate([90, 0, 0])
                bearing_hole();
        translate([0, 0, 7.5])
            rotate([0, 90, 0])
                mount_hole(0, 0, 17);
        translate([0, 0, -7.5])
            rotate([0, 90, 0])
                mount_hole(0, 0, 17);
        // Probe mount
        translate([h2_depth/2 + 12, 30, -3]) {
            rotate([90, 0, 0])
                cylinder(h=20, d=3);
            translate([0, 0, -10])
                rotate([90, 0, 0])
                    cylinder(h=20, d=3);
        }
        if (surround_dia == 23) {
        // slice off top
        translate([(23 + h2_depth)/2, 0, h2_height/2 + top_offset_up - rod_gap + 50 + 2])
            cube([100, 100, 100], center=true);
        }
        // cable tie slots
        translate([(23 + h2_depth)/2, 0, h2_height/2 + top_offset_up - rod_gap])
                rotate([90, 0, 0]) {
            tie_slot(0, 0, 5-bearing_length/2);
            tie_slot(0, 0, bearing_length/2-5);
        }
    }
}

h2();
bearing_holder_top();
bearing_holder_back();
