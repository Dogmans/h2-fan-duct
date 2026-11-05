# Support-free duct sections, with short bridges

Use this folder's four `*_print.stl` files as a matching set. Their orientations differ from the previous revision. `H2_5015_SupportFree.FCStd` contains the assembled parts and hidden print-orientation copies. STEP files retain installed coordinates.

## Orientation and settings

| Part | Bed face / orientation | Deliberate bridges |
| --- | --- | --- |
| Tray | Broad flat bottom down | About 10 mm across each nozzle roof |
| Cover | Broad flat outer face down | 1.7 mm blind collar-screw pocket |
| Adapter front | Flat outer back down; cavity faces UP | Approximately 4 mm head-recess closures |
| Adapter rear | Wider mounting foot down; cavity faces UP | No flat external bridge faces in the mesh audit |

Start with 0.2 mm layers, a 0.4 mm nozzle, Arachne, four perimeters and 20% infill. Disable supports. A 3 mm brim is useful, especially for the taller rear adapter. Use your filament's appropriate bridge speed, flow and cooling; the longest clear span is about 10 mm. Keep the supplied STL orientations.

The cover is now a flat 4 mm plate. Its former nozzle fingers are part of the tray, closing across two sidewalls. The nozzle ceilings have 0.2 mm treads that follow the original 15-degree mean slope within 0.1 mm, making the intended bridges explicit. The rear adapter has a tapered keel growing from its foot and 45-degree roofs on the horizontal M3 holes and head recesses. Its wider foot retains the original screw-seat positions. The front adapter has a flat back and recessed M2 heads.

The rear adapter uses more material than the previous thin shell. This provides its own support during printing while retaining the installed outer bounds and the air passage. Fan position, mounting screw centers, main-duct interface and nozzle positions are retained.

## Hardware changes

- Adapter-half joint: **two M2x8 screws**, with heads seated in the front half's recesses. Tap the two 1.7 mm blind pilots in the rear half M2. These replace the previous M2x10-and-nut joints.
- Cover: four M2x8 screws into the tray's tapped M2 blind pilots, as before.
- Roof strap: one M2x4 screw into the cover's tapped blind pilot, as before.
- Mounting foot: the same two M3x10 screws and approximately 0.5 mm washers into the bracket's captive nuts. The new 7.2 mm head-recess diameter accommodates ordinary 7 mm OD M3 washers; use an Allen key to reach the recessed heads.
- Fan and combined chain bracket: retain their previous fasteners.

The locating collar is now a roof strap and positive end stop. Its rear edges are chamfered to eliminate free lips. The M2 strap screw locates the main duct laterally and holds it against the adapter. The roof has 0.2 mm clearance over the cover.

## Assembly

1. Inspect the bridges and clear any strings inside the nozzle passages. The adapter cavities print open upward and can be cleaned directly.
2. Tap the M2 pilots, test the specified screw lengths, then join the adapter halves with the two M2x8 screws.
3. Screw the flat cover to the matching new tray. Slide its end under the adapter strap, seat the inlet faces together, and fit the M2x4 strap screw.
4. Seal the exterior seams with foil tape or a thin removable sealing film. Keep material out of the air channels.
5. Mount the adapter using the two recessed M3 fixings. Check the blower butt joint, heater sock, nozzle plane and full travel on the cool printer.

## Verification and limitations

All four meshes are watertight with zero nonmanifold edges, and their STEP exports reopen as valid single solids. A facet audit finds **zero non-flat downward area steeper than 45 degrees** in the exported orientations. Faces beyond that limit are the intentional flat bridges listed above. The rear adapter has no such flat bridge faces. This audit is in `export_checks.json`.

All four files were sliced with supports disabled. SuperSlicer still reports stability/loose-extrusion alerts on the tray and adapter bridge/infill regions. Those alerts are retained in `slice_checks` rather than suppressed. The generated tray paths span approximately 10.4 mm including their ends, across the intended 10 mm nozzle gaps. This is a CAD and toolpath review, not a completed physical print; bridge quality depends on the material and cooling. Check these spans in your slicer before printing.

The duct remains one connected air passage with only the fan inlet and two nozzle outlets. No solid blocks that passage, the mating parts do not overlap, and there are no modeled collisions with the H2, stock heatsink fan, motor plug, mounting bracket, rods or bearing envelopes. Heater-sock clearance remains at least 2.09 mm, and the lowest surface is 1 mm above the nozzle datum. Right projection remains 20.9 mm including the socket; projection toward the camera remains 16 mm. Physical fit and airflow testing are still required.

The `slice_checks/*verification.gcode` files are geometry checks with no heating or homing sequence. Generate your own printer-ready G-code from the STLs.
