# Four-section printable H2 duct

Use the four `*_print.stl` files in this folder. They are already rotated and seated at Z=0. The matching STEP files retain their **assembled** positions. `H2_5015_Printable.FCStd` contains the assembled sections, the H2 layout and hidden print orientations.

The fan stays flat on the **right motor end**. The mounting bracket and blower positions are retained. This revision replaces the closed duct with an open tray, a cover and two blower-adapter halves.

## Print orientation

| Section | Bed face | Support |
| --- | --- | --- |
| `tray_print.stl` | Broad, continuous flat bottom | None in the checked orientation |
| `cover_print.stl` | Broad, flat outer roof, upside down | Build-plate support under the short nozzle extensions if generated |
| `adapter_front_print.stl` | Flat split/mating face down | Build-plate support; remove through the open mating face |
| `adapter_back_print.stl` | Flat split/mating face down | Build-plate support for the elbow and mounting foot; remove through the open mating face |

Checked with SuperSlicer 2.7.62.0, a 0.4 mm nozzle, 0.2 mm layers, **Arachne**, four perimeters and 20% infill. Use your own printer and material settings. The tray is open upward; it needs no internal roof bridges. The 4 mm cover provides a flat bed surface and enough depth for the blind collar screw. Main and nozzle side walls are 1.6 mm. The tray floor is 3 mm under the main passage and about 1 mm at the outlet ends.

Keep the exported orientations. The adapter cavity is exposed on the split face, so any generated support can be removed before the halves are joined. Inspect those cavities and the cap nozzle extensions after support removal. A small brim can help the adapter halves.

The checked Arachne recipe matters: the installed slicer's classic thin-wall engine flags small loose extrusion paths on the tray. The Arachne check completes without that warning. Independently, all 55 tray layer sections at 0.2 mm were checked in CAD: each section is supported by the one below, with zero newly unsupported projected area.

## Additional hardware

- Four M2x8 screws for the cover. Tap the four 1.7 mm blind pilot holes in the tray M2, or use suitable plastic screws after checking their fit. Do not drill them through.
- Two M2x10 screws and two M2 hex nuts for the adapter halves. Nut pockets are about 4.3 mm across flats and 1.8 mm deep.
- One M2x4 screw for the locating collar. Tap the blind 1.7 mm pilot hole in the cover M2. A longer screw can enter the air passage.
- Retain the two M3x10 adapter-to-bracket screws, approximately 0.5 mm washers and the captive M3 nuts in the bracket. The fan still uses two M3x20 screws with approximately 1.5 mm of washers and the bracket's captive nuts.

## Assembly

1. Remove all support from the two adapter halves and the short cover extensions. Inspect and clean the exposed channels.
2. Fit the two M2 nuts, apply a very thin removable sealing film to the adapter seam or use foil tape on its exterior, and join the halves with the M2x10 screws. Keep sealant out of the air channel.
3. Fit the cover to the tray with the four M2x8 screws. The planar main rim and sloped nozzle rims meet continuously. Seal the exterior seam with foil tape or a thin removable sealing film if needed.
4. Slide the last 3 mm of the tray/cover assembly into the adapter's open-bottom collar. It has 0.2 mm clearance on each side and above the cover. Seat the inlet faces together and fit the M2x4 collar screw. Seal the exterior butt joint.
5. Refit the assembly to the existing right-end bracket using its two M3 fixings. The top socket still meets the blower at Z=28 mm as a butt joint; use a thin fan gasket or exterior seam tape.

The cover can be removed later by releasing the collar, sliding the main duct clear and undoing the four cover screws.

## Geometry and checks

The main passage is 14 x 8 mm. The planar U branches have rounded outer turns. The nozzle transitions are extruded 2D profiles with **no twist**, followed by straight channels sloping 15 degrees toward the nozzle. Their outlet end faces are vertical to avoid projecting print lips. Each outlet has 32 mm² area normal to the channel, centered at Z=3.65 mm, X=1.5 and 26.5, Y=1.3. The channel centerlines aim at approximately Z=0.30 at the nozzle.

The assembled geometry has one connected air passage, exactly one inlet and two outlets, no solid obstruction in that passage, and no overlapping print sections. All four STLs are watertight with no nonmanifold edges; all four STEP files reopen as valid single solids. The matching faces have no modeled interference. Screws stay out of the air passage.

The lowest surface remains 1 mm above the nozzle tip. Modeled heater-sock clearance is at least 2.09 mm. The collar extends the duct 16 mm toward the camera, about 1.35 mm more than the prior closed duct. Right extension remains 20.9 mm including the socket, with no added left projection beyond the existing heatsink fan. This is a geometric and slicer check, not a physical print or airflow test; retain the fit check against the real heater sock, wiring and carriage.

`validation.json`, `export_checks.json`, `tray_layer_check.json` and `slice_checks/slice_validation.json` contain the checks. G-code in `slice_checks` is **geometry verification only**, with no heating or homing sequence; slice the STLs again with your own printer profile for printing.
