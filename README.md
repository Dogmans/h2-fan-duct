# BIQU H2 right-end 5015 blower and opposed cooling ducts

The blower is mounted flat against the **right motor end**, with its intake facing right. A combined chain / fan bracket replaces the existing 3 mm chain plate and shares its two H2 M3 holes. The original 3510 heatsink cooling fan stays in place.

The current model is `output/support_free/H2_5015_SupportFree.FCStd`, built through the FreeCAD MCP bridge. Its four duct sections are designed for printing **without supports, using short bridges**: a flat-bottom tray with integrated nozzle roofs, a flat cover and two cavity-up adapter halves. The blue mounting bracket retains its native PartDesign features. See [printing and assembly instructions](output/support_free/PRINTING.md), including the revised M2x8 adapter joints and the recorded slicer bridge alerts.

## Nominal envelope

Coordinates follow the supplied photo: X is left to right, Y points away from the camera, Z is up. The standard nozzle tip is `(14, 1.3, 0)` mm. The H2 body is X=0..61.9, Y=-17.5..17.5, Z=22.2..57.2. The existing heatsink fan extends left to X=-14.9.

| Feature | Size / location |
| --- | --- |
| Fan / motor separation | 4 mm structural frame, no additional air gap |
| Fan + frame extension to right | 19 mm |
| Extension to right including duct socket | 20.9 mm; allow about 22.2 mm including button-head screws and washers |
| Added width on the photo's left | None relative to the existing heatsink fan |
| Extra projection toward camera | 16 mm at the removable collar; fan alone projects 12.7 mm beyond the body |
| Projection away from camera | Frame reaches Y=22.3, about 4.8 mm beyond the body; within the inferred carriage zone |
| Fan outlet height | Z=28 mm; the fan housing reaches approximately Z=79.7 mm |
| Chain mount top | Existing Z=117.7 mm retained |
| Duct outlets | About 32.9 mm2 per channel, centered near Z=3.70 mm, X=1.5 and 26.5, Y=1.3; vertical mouths |
| Jet direction | Nozzle floors and stepped roof envelope follow 15 degrees inward/down; nominal aim is near Z=0.35 at the nozzle |
| Lowest duct surface | 1 mm above nozzle tip |
| Heater / sock gap | At least 2.09 mm to the modeled 24 x 20 x 12 mm envelope |

A 5015 housing is larger than the 35 mm motor end. Some overhang in Y is unavoidable with this orientation. This layout avoids placing the fan's 15 mm depth on the near face and keeps the larger addition on the right as requested. Check the complete printer's travel envelope before homing.

## Fan reference

The interface targets the common two-ear centrifugal 5015 layout, nominally 50 x 50 x 15 mm. The detailed mechanical reference is the manufacturer's [BeCool 5015-1 drawing](https://www.becoolfan.com/uploadfile/202410/7d3269db40767fe.pdf), which shows a 51.6 mm housing outline, 15 mm thickness, and ear coordinates relative to the rotor center. A copy is in `reference/5015-1-drawing.pdf`. The housing here is a simplified reference, not a manufacturing model.

GDSTIME GDB5015 is an example of the usual printer blower format. The [Voron Stealthburner design](https://github.com/VoronDesign/Voron-Stealthburner) is an example of a printer toolhead using a 5015. Housing outlines, ear patterns and outlet lips differ among 5015 suppliers. Before printing the full bracket, compare the selected fan with the drawing and the model: 15 mm thickness, approximately 19.3-19.5 mm outlet width, two ear centers approximately 57 mm apart. The mounting slots allow +/-1.5 mm in Y. They do not accommodate every possible 5015 variant.

The socket opening is 15.6 mm along X and 20 mm along Y. Its top meets the fan outlet as a **butt joint**. Use a thin foam gasket or tape around the outside seam; do not push the fan down into the duct. The fan is held by the bracket screws, not by the socket lip.

## Hardware and assembly

- Two M3 screws for the H2, nominally M3x8 as used with the original 3 mm chain plate. Reuse the existing screws if engagement is suitable.
- Two M3x20 button-head screws for the fan, with about **1.5 mm of washers under each head**, and two M3 hex nuts. Use washers with enough outside diameter to span the blower's approximately 4.7 mm ear holes.
- Two M3x10 button-head screws for the duct, about 0.5 mm washers, and two M3 hex nuts.
- For the four duct sections: four M2x8 cover screws, two M2x8 adapter-half screws into tapped blind pilots, and one M2x4 strap screw. See the [section assembly guide](output/support_free/PRINTING.md).

All four fan/duct nuts load from the **motor-facing side** of the right frame. Recesses are 2.5 mm deep with approximately 5.75 mm across flats. The fan recesses are elongated to preserve the slot adjustment. The fan recesses leave 1.5 mm of plastic between the nut and fan face. The duct recesses leave 3.5 mm between nut and duct mounting face.

1. Fit the four nuts into the rear recesses. Check the real nut fit before mounting the bracket.
2. Replace the existing chain plate with the combined bracket and refit the chain. The source SCAD's 15 mm H2 spacing, chain-hole positions and 69 mm distance between hole-group centers are retained. The comment saying 59 mm conflicts with the SCAD geometry; the geometry was followed. The original rounded union blend is omitted.
3. Mount the blower on the right frame, intake pointing right, outlet pointing down. Use the specified washer stack so screw ends stop inside the frame instead of projecting into the motor. Check actual screw lengths and washer thicknesses during assembly.
4. Assemble the four duct sections using the section assembly guide, then fit the adapter's two-screw mounting foot. The inlet meets the blower outlet. Fit the gasket around the seam and tighten the two M3 duct screws.
5. With the printer cool and powered down, check the heater sock, nozzle, motor plug, wires, rods and full carriage travel. The tips should remain above the nozzle plane. Adjust the CAD if the real sock or nozzle differs from the reference.

The old part-cooling fan and its mounting duct are replaced. Do not remove the stock heatsink cooling fan.

## Printing and verification

This is a **CAD and toolpath-reviewed prototype**, not a physically tested airflow design. The duct has 1.6 mm nominal side walls, a flat-bottom tray and a flat 4 mm cover. The manifold is 14 x 8 mm. Nozzle roofs now bridge approximately 10 mm between their sidewalls and use 0.2 mm internal treads. Both adapter cavities print upward; the rear half grows from a wider foot on tapered surfaces. Airflow balance and cooling performance require testing on the printer.

Use a heat-resistant material appropriate to the printer. The combined mounting bracket is unchanged and still needs supports. For the duct, use all four matching `output/support_free/*_print.stl` files in their supplied orientations with supports disabled. They were sliced using Arachne, 0.2 mm layers and a 0.4 mm nozzle. The mesh audit finds no steep non-bridge overhangs; SuperSlicer's remaining bridge/infill stability alerts are recorded in the instructions and logs. A 3 mm brim helps the rear adapter. This revision relies on short bridges rather than added supports.

`output/support_free/validation.json` records four valid print solids, one connected air volume with exactly three openings, no blockage or overlapping mating parts, and no modeled collision with the body, nozzle, heater, stock fan, motor connector, bearing envelopes, rods or bracket. Export checks include watertight STL meshes, reopened STEP solids and a facet-based overhang audit. Rod and bearing positions were inferred from `croxy_carriage_h2_touch_less_offset.scad`, not measured from the photograph; the 8 mm rod diameter is assumed. The heater sock, plug, wiring and carriage are simplified references.

## Files and regeneration

- `output/support_free/H2_5015_SupportFree.FCStd`: current four-section duct and mounting layout, with hidden print orientations.
- `output/support_free/{tray,cover,adapter_front,adapter_back}_print.stl`: the four current duct print files, seated on Z=0.
- `output/support_free/*_assembled.step`: sections at installed coordinates; `duct_assembled.step` contains all four.
- `output/right_face/h2_5015_right_bracket.stl`: the mounting bracket, including chain mount.
- `build_support_free_duct.py`: rebuild this revision via the FreeCAD MCP `execute_python_file` tool, using the saved right-face mount/layout.
- `verify_support_free.ps1`: repeat no-support slicing and record warnings. `-FailOnWarnings` provides strict warning handling. Generated G-code is geometry verification only.
- `build_h2_5015_right.py` and `right_face_parameters.json`: generate the reference mounting bracket and fan layout. Some H2 datums and routing stations are fixed in the scripts.

H2 dimensions were read from BIQU's original manufacturer drawing [mirrored here](https://meltbro.de/images/product_images/original_images/Ha3e48c4557434aab986f21c8810ed609K.png), saved as `reference/H2-dimensions.png`, and checked against the user's carriage SCAD. The supplied chain SCAD was read as geometry reference and left unchanged.
