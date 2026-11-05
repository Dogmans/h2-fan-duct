include <../unionRound.scad>;

$fn=100;

difference() {
    unionRoundMask(r=2) {
        translate([15, 0, 0])
        cube([80, 3, 10], center=true);
        translate([-26, 0, 0])
            cube([20, 3, 17], center=true);
        translate([-15, 0, 0])
            cube([10, 3, 17], center=true);
    }
    // Mounting holes
    translate([-27, 0, -5+17/2]) {
        rotate([90, 0, 0])
            cylinder(h=100, d=3.3, center=true);
    }
    // Others back 7.5 with 7mm between it would seem
    translate([-27+3.5, 0, -12.5+17/2]) {
        rotate([90, 0, 0])
            cylinder(h=100, d=3.3, center=true);
    }
    translate([-27-3.5, 0, -12.5+17/2]) {
        rotate([90, 0, 0])
            cylinder(h=100, d=3.3, center=true);
    }
    // 59mm from middle mount hole to middle of h2 holes
    translate([-27+69, 0, 0]) {
        translate([7.5, 0, 0])
            rotate([90, 0, 0])
                cylinder(h=100, d=3.3, center=true);
        translate([-7.5, 0, 0])
            rotate([90, 0, 0])
                cylinder(h=100, d=3.3, center=true);
    } 
}