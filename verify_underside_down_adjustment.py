"""Verify nut loading and coupled fan/duct height travel in FreeCAD.

Called by build_underside_down_duct.py before exporting the outward/downward design.
May also be run on the saved assembly with FreeCAD execute_python_file.
"""
import json
import math
import os
import Part
from FreeCAD import Vector as V


def verify_and_add_spacers(doc, parameters):
    frame_x = 61.9 + parameters['motor_clearance_mm'] - 4
    mounts = [(44.4, -7.0), (44.4, 9.6)]
    ears = [(-3 + parameters['fan_shift_y_mm'] - 22.2, 75.4 + parameters['fan_shift_z_mm']),
            (-3 + parameters['fan_shift_y_mm'] + 19.3, 36.4 + parameters['fan_shift_z_mm'])]
    bracket = doc.UndersideBracket.Shape
    duct = doc.Duct.Shape
    fan = doc.Blower5015.Shape
    fixed = ['H2Body', 'Stock3510', 'HeaterSock', 'Nozzle', 'Heatbreak',
             'MotorConnector', 'CarriageEnvelope', 'RodKeepouts', 'ChainPlate']

    def cylinder(radius, height, x, y, z, axis=V(0, 0, 1)):
        return Part.makeCylinder(radius, height, V(x, y, z), axis)

    def hexagon(y, z, x, depth, af):
        rr = af / math.sqrt(3)
        pp = [V(x, y + rr*math.cos(math.radians(30+i*60)),
                z + rr*math.sin(math.radians(30+i*60))) for i in range(6)]
        return Part.Face(Part.makePolygon(pp+pp[:1])).extrude(V(depth, 0, 0))

    def spacer(y, height, z):
        return Part.makeBox(9, 11, height, V(40.9, y-5.5, z)).cut(
            cylinder(1.65, height, 44.4, y, z)).removeSplitter()

    def moved(shape, dz):
        result = shape.copy()
        result.translate(V(0, 0, dz))
        return result

    def overlap(a, b):
        value = a.common(b).Volume
        assert value < 1e-5, ('Interference', value)
        return value

    report = {'design': 'underside/downward with accessible rear nuts and coupled height adjustment',
              'assembly_raise_mm': [0, 2, 4], 'lowest_duct_above_nozzle_mm': [parameters['duct_base_z_mm']+d for d in [0,2,4]],
              'spacer_thickness_mm': [4, 2, 0], 'duct_screw_lengths_mm': [12, 10, 8],
              'duct_washer_stack_mm': 2, 'fan_slot_travel_mm': [-1, 4],
              'fan_slot_width_mm': 3.3, 'fan_slot_length_mm': 8.3,
              'fan_nut_retaining_floor_mm': 1.5,
              'nut_loading_envelope_af_mm': 5.75, 'nut_loading_approach_mm': frame_x-50, 'nut_loading_checks': [],
              'height_travel_checks': [], 'physical_tested': False}
    # These swept volumes cover the complete insertion path from outside the
    # motor end, through the support arm, to the back of the captive pocket.
    for i in range(21):
        delta = -1 + i/4
        for y, z in ears:
            corridor = hexagon(y, z+delta, 50, frame_x+2.5-50, 5.75)
            shank = cylinder(1.5, 4.2, frame_x-.1, y, z+delta, V(1,0,0))
            nut = hexagon(y, z+delta, frame_x+.05, 2.4, 5.5)
            values = {'bracket': overlap(corridor, bracket)}
            for name in fixed:
                values[name] = overlap(corridor, doc.getObject(name).Shape)
            overlap(shank, bracket)
            overlap(nut, bracket)
            report['nut_loading_checks'].append({'ear_y_mm': y, 'offset_z_mm': delta,
                                                  'path_collisions_mm3': values})
    # Check intermediate heights too, including hardware, moving air volume,
    # socket alignment, spacer contact and the fixed bracket.
    for i in range(17):
        dz = i/4
        ds, fs = moved(duct, dz), moved(fan, dz)
        shapes = [ds, fs]
        for j, (x, y) in enumerate(mounts):
            if dz < 4:
                shapes.append(spacer(y, 4-dz, 14.2+dz))
            start = 10.2 + dz
            bolt = cylinder(1.5, 12-dz, x, y, start).fuse(
                cylinder(2.85, 1.65, x, y, start-1.65))
            washer = cylinder(3.5, 2, x, y, start).cut(cylinder(1.6, 2, x, y, start))
            shapes.extend([bolt, washer])
        for name in ['Hardware_fan_1', 'Hardware_fan_2']:
            shapes.append(moved(doc.getObject(name).Shape, dz))
        # Existing duct nuts stay in the fixed top pockets.
        values = {}
        for k, shape in enumerate(shapes):
            values[str(k)+'_bracket'] = shape.common(bracket).Volume
            assert values[str(k)+'_bracket'] < 1e-5, ('Bracket interference', dz, k, values[str(k)+'_bracket'])
            for name in fixed:
                values[str(k)+'_'+name] = overlap(shape, doc.getObject(name).Shape)
            for j, other in enumerate(shapes[:k]):
                values[str(k)+'_'+str(j)] = overlap(shape, other)
        air = moved(doc.CompleteAir.Shape, dz)
        # The simplified blower housing intentionally closes the inlet extension.
        for index, shape in enumerate([bracket, ds]+shapes[2:]):
            value = shape.common(air).Volume
            assert value < 1e-5, ('Air interference', dz, index, value)
        intake = moved(doc.IntakeKeepout.Shape, dz)
        for shape in [bracket, ds, doc.H2Body.Shape, doc.CarriageEnvelope.Shape]:
            overlap(shape, intake)
        rod_gap = fs.distToShape(doc.RodKeepouts.Shape)[0]
        heater_gap = ds.distToShape(doc.HeaterSock.Shape)[0]
        assert rod_gap >= 2, ('Rod clearance', dz, rod_gap)
        assert heater_gap >= 2-1e-5, ('Heater clearance', dz, heater_gap)
        seam = fs.optimalBoundingBox(False).ZMin - ds.optimalBoundingBox(False).ZMax
        assert abs(seam) < 1e-5, ('Fan/duct seam opened', dz, seam)
        assert abs(ds.distToShape(fs)[0] - duct.distToShape(fan)[0]) < 1e-5
        report['height_travel_checks'].append({
            'raise_mm': dz, 'lowest_duct_mm': ds.optimalBoundingBox(False).ZMin,
            'rod_clearance_mm': rod_gap, 'heater_clearance_mm': heater_gap,
            'fan_duct_seam_mm': seam, 'max_collision_mm3': max(values.values())})
    report['minimum_blower_rod_clearance_mm'] = min(
        row['rod_clearance_mm'] for row in report['height_travel_checks'])
    report['minimum_heater_clearance_mm'] = min(
        row['heater_clearance_mm'] for row in report['height_travel_checks'])
    report['note'] = ('Use matching spacers at both duct bolts: 4 mm for nominal, '
                      '2 mm for +2 mm, none for +4 mm. Change both duct screws to '
                      'M3x12/x10/x8 respectively, retaining 2 mm washers. Raise '
                      'the fan by the same amount and reseal the butt joint. '
                      'The -1 mm fan slot reserve only corrects real fan fit. '
                      'Nominal down-angled jets target the nozzle plane; extra lift raises the target. Check cooling on the printer.')
    spacer_shapes = {'spacer_2mm': spacer(-7, 2, 14.2),
                     'spacer_4mm': spacer(-7, 4, 14.2)}
    for i, (_, y) in enumerate(mounts, 1):
        name = 'HeightSpacer'+str(i)
        ob = doc.getObject(name) or doc.addObject('PartDesign::Feature', name)
        ob.Shape = spacer(y, 4, 14.2)
        ob.Label = 'PRINT - 4 mm spacer (nominal duct height)'
        ob.ViewObject.ShapeColor = (.3, .75, .5)
        doc.PrintedParts.addObject(ob)
        ob.Visibility = True
    doc.recompute()
    return report, spacer_shapes


if __name__ == '__main__':
    root = os.path.dirname(os.path.abspath(__file__))
    target = os.path.join(root, 'output', 'underside_down')
    doc = App.listDocuments().get('H2_5015_Underside_Down') or App.openDocument(
        os.path.join(target, 'H2_5015_Underside_Down.FCStd'))
    parameters = json.load(open(os.path.join(root, 'underside_down_parameters.json')))
    report, _ = verify_and_add_spacers(doc, parameters)
    with open(os.path.join(target, 'adjustable_mount_checks.json'), 'w') as out:
        json.dump(report, out, indent=2)
    print(json.dumps(report, indent=2))
