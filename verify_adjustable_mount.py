"""Check the rebuilt fan mount and save a copy of the current duct assembly.

Run with the installed FreeCAD Python, or in FreeCAD. The existing monolithic
document (which may contain manual edits) is read and saved under a NEW name.
Regenerate the bracket first with build_h2_5015_right.py.
"""
import hashlib
import json
import math
import os
from collections import Counter

import FreeCAD as App
import Mesh
import Part
from FreeCAD import Vector as V

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, 'output', 'right_face')
P = json.load(open(os.path.join(ROOT, 'right_face_parameters.json')))
source = os.path.join(ROOT, 'output', 'monolithic', 'H2_5015_Monolithic.FCStd')
source_hash = hashlib.sha256(open(source, 'rb').read()).hexdigest()
right = App.openDocument(os.path.join(OUT, 'H2_5015_Right.FCStd'))
bracket = right.CombinedBracket.Shape
step = Part.read(os.path.join(OUT, 'h2_5015_right_bracket.step'))
mesh = Mesh.Mesh(os.path.join(OUT, 'h2_5015_right_bracket.stl'))
_, facets = mesh.Topology
edges = Counter(tuple(sorted((f[i], f[(i+1) % 3]))) for f in facets for i in range(3))
assert bracket.isValid() and len(bracket.Solids) == 1
assert step.isValid() and len(step.Solids) == 1
assert mesh.isSolid() and all(n == 2 for n in edges.values())
export_path = os.path.join(OUT, 'export_checks.json')
export_checks = json.load(open(export_path))
export_checks['h2_5015_right_bracket'] = {
    'stl_facets': len(facets), 'stl_edges_not_two': 0, 'stl_solid': True,
    'step_valid': True, 'step_solids': 1, 'step_volume': step.Volume}
with open(export_path, 'w') as out:
    json.dump(export_checks, out, indent=2)

report = {'bracket_valid': True, 'bracket_solids': 1, 'stl_watertight': True,
          'nonmanifold_edges': 0, 'step_valid': True, 'step_solids': 1,
          'adjustment_mm': [-P['fan_adjust_down'], P['fan_adjust_up']],
          'slot_width_mm': 3.3,
          'slot_length_mm': 3.3 + P['fan_adjust_down'] + P['fan_adjust_up'],
          'nut_floor_thickness_mm': P['right_frame_thickness'] - 2.5,
          'travel_checks': []}
zc = P['fan_outlet_z'] + 25.8
fanholes = [(P['fan_center_y'] - 22.2, zc + 21.6),
            (P['fan_center_y'] + 19.3, zc - 17.4)]
# Check the actual M3 shank and 5.5 mm AF hex at nine positions in BOTH slots.
for i in range(9):
    dz = -P['fan_adjust_down'] + i * (P['fan_adjust_down'] + P['fan_adjust_up']) / 8
    for y, z in fanholes:
        shank = Part.makeCylinder(1.5, P['right_frame_thickness'] + .2,
                                 V(61.8, y, z + dz), V(1, 0, 0))
        rr = 5.5 / math.sqrt(3)
        pts = [V(61.95, y + rr * math.cos(math.radians(30 + j * 60)),
                 z + dz + rr * math.sin(math.radians(30 + j * 60))) for j in range(6)]
        nut = Part.Face(Part.makePolygon(pts + pts[:1])).extrude(V(2.4, 0, 0))
        collisions = {'shank_mm3': shank.common(bracket).Volume,
                      'nut_mm3': nut.common(bracket).Volume}
        assert max(collisions.values()) < 1e-5, (y, dz, collisions)
        report['travel_checks'].append({'ear_y_mm': y, 'offset_z_mm': dz, **collisions})

assembly = App.openDocument(source)
old = assembly.CombinedBracket
for child in list(reversed(old.Group)):
    assembly.removeObject(child.Name)
assembly.removeObject(old.Name)
assembly.copyObject(right.CombinedBracket, True)
assembly.recompute()
report['current_duct_interference_mm3'] = assembly.Duct.Shape.common(bracket).Volume
assert report['current_duct_interference_mm3'] < 1e-5
report['fan_vs_fixed_references_mm3'] = []
for dz in report['adjustment_mm']:
    fan = right.Blower5015.Shape.copy()
    fan.translate(V(0, 0, dz))
    collisions = {name: fan.common(right.getObject(name).Shape).Volume for name in
                  ['CombinedBracket', 'H2Body', 'Stock3510', 'MotorConnector',
                   'CarriageEnvelope', 'RodKeepouts']}
    assert max(collisions.values()) < 1e-5, (dz, collisions)
    report['fan_vs_fixed_references_mm3'].append({'offset_z_mm': dz, **collisions})
report['fit_note'] = ('Travel is available in the bracket. Stop lowering at the actual '
                      'fan/duct seam; the nominal blower already meets the inlet.')
assembly.Label = 'H2 5015 - current duct with vertically adjustable fan bracket'
target = os.path.join(OUT, 'H2_5015_AdjustableMount.FCStd')
assembly.saveAs(target)
assert hashlib.sha256(open(source, 'rb').read()).hexdigest() == source_hash
report['preserved_monolithic_source_sha256'] = source_hash
report['assembly_copy'] = os.path.basename(target)
with open(os.path.join(OUT, 'adjustable_mount_checks.json'), 'w') as out:
    json.dump(report, out, indent=2)
print(json.dumps(report, indent=2))
