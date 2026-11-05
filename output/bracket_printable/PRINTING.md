# Printable right-face H2 bracket

This replaces the one-piece right-face bracket with two bolted pieces. All existing extruder, cable-chain, blower and duct mounting positions are preserved. No duct parts were changed. The root-level `h2_5015_printed_assembly.step` is an earlier near-face design; use this folder for the revised right-face bracket.

## Printing

Import the two `*_print.stl` files separately, retaining their supplied orientation and placing each on the bed:

- `chain_plate_print.stl`: broad flat extruder-facing plate down; the thick joint block and locating key point up. Approximately 34.5 x 91 x 12 mm.
- `fan_frame_print.stl`: flat motor-facing side down, nut-pocket openings on the bed and countersunk screw mouths up. Approximately 67.9 x 53.5 x 6 mm.

Suggested starting settings: 0.4 mm nozzle, 0.2 mm layers, four walls, 20–30% infill, supports disabled. A 3 mm brim is optional. Enable bridging over the small pockets. The joint nut pockets bridge about 3.3 mm; the existing fan nut pockets bridge about 5.75 mm. Keep elephant-foot compensation enabled so the bed-facing pockets remain usable. Use the slicer's material profile appropriate for your printer.

The geometry audit finds no non-horizontal downward faces steeper than 45 degrees in these print orientations. Both STLs are closed two-manifold meshes. Both slice successfully with supports disabled, but SuperSlicer retains generic collapsing-overhang/loose-extrusion warnings around the bridging geometry. Review those layers in preview; these are intentional bridges, not a physical print validation. The verification G-code is not printer-ready.

## Assembly

1. Insert two ordinary M3 hex nuts into the side pockets in the chain plate's thick joint block.
2. Fit the locating key into the shallow recess in the fan frame. The original plates meet at 90 degrees.
3. Install two M3 x 10 mm countersunk screws from the fan side. Their heads must sit flush with the fan-frame face so they clear the blower. Tighten gently into the captive nuts.
4. Mount using the existing extruder/chain holes, then attach the fan and existing duct parts as before. Check physical fit and full carriage travel before operation.

`bracket_assembled.step` contains both new pieces in their installed positions. `H2_5015_PrintableBracket.FCStd` contains the assembled pieces hidden and the two print-oriented pieces visible. Toggle these sets for assembly/print views. `print_orientation.png` shows the supplied print orientations.

Validation includes zero volume interference with the existing reference extruder, blower, carriage, rods and all four current duct parts. Existing files in `output/support_free` were checked by SHA-256 and left byte-for-byte unchanged.
