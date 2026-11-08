"""Build the outward-facing downward 5015 and adjustable underside ring duct.

Run inside FreeCAD with execute_python_file. All reference geometry is generated locally.
All manufacturing geometry, hardware checks and exports use installed datums.
"""
import hashlib
import json
import math
import os
from collections import Counter

import Part
import Mesh
import MeshPart
from FreeCAD import Vector as V

ROOT = os.path.dirname(os.path.abspath(__file__))
FOLDER = 'underside_down'
OUT = os.path.join(ROOT, 'output', FOLDER)
os.makedirs(OUT, exist_ok=True)
P = json.load(open(os.path.join(ROOT, 'underside_down_parameters.json')))
assert P['rod_diameter_mm']==8, 'This revision uses the verified 8 mm rod reference'
assert P['bottom_mount_z_mm']==22.2, 'Underside datum must match the supplied H2 reference'
assert P['channel_width_mm']/2 < 7, 'Ring bend radius is too small for channel width'
input_files = ['build_underside_down_duct.py', 'h2_hardware_reference.py', 'underside_down_parameters.json']
input_hashes = {name:hashlib.sha256(open(os.path.join(ROOT,name),'rb').read()).hexdigest() for name in input_files}
NAME = 'H2_5015_Underside_Down'
if NAME in App.listDocuments():
    App.closeDocument(NAME)
doc = App.newDocument(NAME)
doc.Label = ('H2 - underside ring duct and outward downward 5015')
import runpy
reference_geometry = runpy.run_path(os.path.join(ROOT,'h2_hardware_reference.py'))['create_references'](doc,App)
refs = doc.References
parts = doc.addObject('App::DocumentObjectGroup', 'PrintedParts')
parts.Label = 'PRINT - duct, underside fan bracket, chain plate'
construction = doc.addObject('App::DocumentObjectGroup', 'Construction')
construction.Label = 'Hidden air volumes and verification envelopes'
layouts = doc.addObject('App::DocumentObjectGroup', 'PrintLayout')
layouts.Visibility = False
hardware = doc.addObject('App::DocumentObjectGroup', 'Hardware')

WALL = P['wall_mm']
CW = P['channel_width_mm']
BASE = 1.0
FLOOR = BASE + WALL
ROOF = FLOOR + P['channel_height_mm']
TOP = ROOF + WALL
YC = 1.3
MOTOR_GAP = P['motor_clearance_mm']
FX = 61.9 + MOTOR_GAP
FRAME_X = FX - 4.0
SHIFT = V(MOTOR_GAP-4.0,P['fan_shift_y_mm'],P['fan_shift_z_mm'])
# The duct and blower rise together; the H2 bracket remains fixed.
HEIGHT_TRAVEL = (P.get('assembly_raise_mm', 4.0))
assert HEIGHT_TRAVEL == 4.0, 'Spacer/bolt schedule is verified for 4 mm travel'
FAN_UP = (HEIGHT_TRAVEL)
DUCT_MOUNT_TOP = 18.2 - HEIGHT_TRAVEL


def box(dx, dy, dz, x, y, z):
    return Part.makeBox(dx, dy, dz, V(x, y, z))


def cyl(r, h, p, axis=(0, 0, 1)):
    return Part.makeCylinder(r, h, V(*p), V(*axis))


def union(shapes):
    result = shapes[0]
    for shape in shapes[1:]:
        result = result.fuse(shape)
    result = result.removeSplitter()
    assert result.isValid(), 'Invalid boolean union'
    return result


def feature(name, label, shape, group=parts, color=(.95, .46, .12), visible=True):
    ob = doc.addObject('PartDesign::Feature', name)
    ob.Label = label
    ob.Shape = shape
    group.addObject(ob)
    ob.ViewObject.ShapeColor = color
    ob.ViewObject.LineColor = (.14, .16, .18)
    ob.ViewObject.Deviation = .08
    ob.Visibility = visible
    return ob


def transformed(shape):
    s = shape.copy()
    s.translate(SHIFT)
    return s


def transform_point(point):
    return transformed(Part.Vertex(V(*point))).Vertexes[0].Point


def rounded_rect(x0, x1, y0, y1, radius):
    return union([
        box(x1-x0-2*radius, y1-y0, 1, x0+radius, y0, 0),
        box(x1-x0, y1-y0-2*radius, 1, x0, y0+radius, 0),
        *[cyl(radius, 1, (x, y, 0)) for x in [x0+radius, x1-radius]
          for y in [y0+radius, y1-radius]]])


def ring_plan(half):
    # Centerline is a rounded rectangle surrounding the heater, not the motor.
    return rounded_rect(-6.8-half, 34.8+half, -16-half, 18.6+half, 7+half).cut(
        rounded_rect(-6.8+half, 34.8-half, -16+half, 18.6-half, 7-half))


def extrude_plan(plan, z, height):
    faces = [f for f in plan.Faces if f.normalAt(0, 0).z > .99]
    face = max(faces, key=lambda f: f.Area)
    s = face.extrude(V(0, 0, height))
    s.translate(V(0, 0, z-1))
    return s


def stroke(points, radius):
    shapes = [cyl(radius, 1, (x, y, 0)) for x, y in points]
    for (ax, ay), (bx, by) in zip(points, points[1:]):
        length = math.hypot(bx-ax, by-ay)
        nx, ny = -(by-ay)/length*radius, (bx-ax)/length*radius
        ps = [V(x, y, 0) for x, y in [(ax+nx, ay+ny), (bx+nx, by+ny),
                                      (bx-nx, by-ny), (ax-nx, ay-ny)]]
        shapes.append(Part.Face(Part.makePolygon(ps+ps[:1])).extrude(V(0, 0, 1)))
    return union(shapes)


def quarter(cx, cy, radius, half, ysign):
    annulus = cyl(radius+half, 1, (cx, cy, 0)).cut(cyl(radius-half, 1, (cx, cy, 0)))
    return annulus.common(box(radius+half+.1, radius+half+.1, 1,
                             cx, cy if ysign > 0 else cy-radius-half-.1, 0))


def feeds(half):
    # Equal front/back feed legs; short-span 7 mm roofs on both sides.
    front = union([box(2*half, 10.3, 1, 54-half, -9, 0),
                   quarter(47, -9, 7, half, -1),
                   box(19.2, 2*half, 1, 27.8, -16-half, 0)])
    back = front.mirror(V(0, YC, 0), V(0, 1, 0))
    return front.fuse(back)




def xz_solid(points, y, width):
    pp = [V(x, y, z) for x, z in points]
    return Part.Face(Part.makePolygon(pp+pp[:1])).extrude(V(0, width, 0))


def mirror_x(s):
    return s.mirror(V(14, 0, 0), V(1, 0, 0))


# Move only the blower reference. All stock cooling, rods, carriage and H2 stay.
fan = transformed(reference_geometry['blower'])
feature('Blower5015', ('BUY - 5015 intake outward, discharge down'), fan,
        refs, (.18, .20, .23))
ears = [transform_point((73.4, y, z)) for y, z in [(-25.2, 75.4), (16.3, 36.4)]]
rotor = transform_point((73.4, -3, 53.8))
outlet = transform_point((73.4, -20.55, 28))

# Main O manifold plus two feed channels. The existing X-directed jets remain.
airplan = union([ring_plan(CW/2), feeds(CW/2)] + (([])))
outerplan = union([ring_plan(CW/2+WALL), feeds(CW/2+WALL)] + (([])))
air = extrude_plan(airplan, FLOOR, ROOF-FLOOR)
outer = extrude_plan(outerplan, BASE, TOP-BASE)
# Close straight longitudinal legs two layers before the transverse channels.
# Separate bridge islands stop the slicer laying strands along the whole ring.
for x0_leg,x1_leg in [(-10.3,-3.3),(31.3,38.3),(50.5,57.5)]:
    air = air.cut(box(x1_leg-x0_leg,20.6,.4,x0_leg,-9,ROOF-.4))
# Curved panels close between the straight-leg and transverse-roof layers.
# Overlap the tangent datums slightly to avoid zero-width material seams where
# the ring corners and straight feed channels merge.
for xa,xb in [(-11,.25),(27.75,38.35),(46.95,57.55)]:
    for ya,yb in [(-30,-8.95),(11.55,30)]:
        air = air.cut(box(xb-xa,yb-ya,.2,xa,ya,ROOF-.2))

# Retract raised-design jet lips 1.5 mm from the sock, retaining the aim line.
TIP_X, TIP_Z, TIP_W, TIP_H = ((0., 4.05, 10., 3.2))
angle = math.radians(15)
co, ta = math.cos(angle), math.tan(angle)
tip_bottom = (TIP_X, TIP_Z-TIP_H/2/co)
tip_top = (TIP_X, TIP_Z+TIP_H/2/co)
corner_bottom = (-2, TIP_Z+(TIP_X+2)*ta-TIP_H/2/co)
corner_top = (-2, TIP_Z+(TIP_X+2)*ta+TIP_H/2/co)
roof = [(-4.9, ROOF), (-3.3, ROOF), corner_top, tip_top]
lines = []
for a, b in zip(roof, roof[1:]):
    dx, dz = b[0]-a[0], b[1]-a[1]
    ll = math.hypot(dx, dz)
    lines.append(((a[0]-dz/ll*WALL, a[1]+dx/ll*WALL),
                  (b[0]-dz/ll*WALL, b[1]+dx/ll*WALL)))
outside_roof = [lines[0][0]]
for (a, b), (c, e) in zip(lines, lines[1:]):
    ux, uz, vx, vz = b[0]-a[0], b[1]-a[1], e[0]-c[0], e[1]-c[1]
    k = ((c[0]-a[0])*vz-(c[1]-a[1])*vx)/(ux*vz-uz*vx)
    outside_roof.append((a[0]+k*ux, a[1]+k*uz))
outside_roof.append((TIP_X, TIP_Z+(TIP_H/2+WALL)/co))
left_outer = xz_solid([(-4.9, BASE), (TIP_X, BASE)]+outside_roof[::-1],
                      YC-TIP_W/2-WALL, TIP_W+2*WALL)
level = round(corner_top[1]/.2)*.2
end_level = round(tip_top[1]/.2)*.2
steps = [(-2, level)]
while level > end_level+.01:
    x = TIP_X+(tip_top[1]-(level-.1))/ta
    steps.extend([(x, level), (x, level-.2)])
    level -= .2
steps.append((TIP_X, end_level))
left_air = xz_solid([(-3.3, FLOOR), corner_bottom, tip_bottom]+steps[::-1]+[(-3.3, ROOF)],
                    YC-TIP_W/2, TIP_W)
mouth = [V(TIP_X, YC-TIP_W/2, tip_bottom[1]), V(TIP_X, YC+TIP_W/2, tip_bottom[1]),
         V(TIP_X, YC+TIP_W/2, end_level), V(TIP_X, YC-TIP_W/2, end_level)]
left_air = left_air.fuse(Part.Face(Part.makePolygon(mouth+mouth[:1])).extrude(V(.6, 0, 0)))
trim = box(16.7, TIP_W+2*WALL, 30, -3.3, YC-TIP_W/2-WALL, BASE)
outer = union([outer.cut(trim).cut(mirror_x(trim)), left_outer, mirror_x(left_outer)])
air = union([air, left_air, mirror_x(left_air)])

# Tangent XZ elbow into the near feed leg. Intake is a horizontal Z plane;
# no diagonal Y dogleg or central-feed receiver is needed.
sx, sy, iz = outlet.x, outlet.y, outlet.z
assert iz >= 15.5, 'Insufficient height for the downward elbow'
pl, pr = sx-7.8, sx+7.8
rtop, rbottom = 3.4, 7.4
cx_top, cz_top = pl-rtop, ROOF+rtop
cx_bottom, cz_bottom = pr-rbottom, FLOOR+rbottom
def xv(point,y):
    return V(point[0],y,point[1])
def profile_with_arcs(points,y,width):
    edges=[]
    start=points[0]
    current=start
    for item in points[1:]:
        if len(item)==3 and item[0]=='arc':
            mid,end=item[1],item[2]
            edges.append(Part.Arc(xv(current,y),xv(mid,y),xv(end,y)).toShape())
            current=end
        else:
            if math.dist(current,item)>1e-8:
                edges.append(Part.makeLine(xv(current,y),xv(item,y)))
            current=item
    edges.append(Part.makeLine(xv(current,y),xv(start,y)))
    return Part.Face(Part.Wire(edges)).extrude(V(0,width,0))
# Roof treads follow the tangent inner radius to within 0.1 mm. They provide
# explicit short bridge panels across Y while preserving the curved turn.
stair=[(61,ROOF),(cx_top,ROOF)]
level=ROOF
while level<cz_top-.01:
    next_level=min(cz_top,level+.2)
    transition=cx_top+math.sqrt(max(0,rtop**2-(cz_top-(next_level-.1))**2))
    stair.extend([(transition,level),(transition,next_level)])
    level=next_level
stair.append((pl,cz_top))
air_section=[(61,FLOOR),(cx_bottom,FLOOR),
    ('arc',(cx_bottom+rbottom/math.sqrt(2),cz_bottom-rbottom/math.sqrt(2)),(pr,cz_bottom)),
    (pr,iz+.6),(pl,iz+.6),(pl,cz_top)]+stair[-2::-1]
elbow_air=profile_with_arcs(air_section,sy-7,14)
ro=rtop-WALL
outer_section=[(61,BASE),(pr+WALL,BASE),(pr+WALL,iz),(pl-WALL,iz),(pl-WALL,cz_top),
    ('arc',(cx_top+ro/math.sqrt(2),cz_top-ro/math.sqrt(2)),(cx_top,TOP)),(61,TOP)]
elbow_outer=profile_with_arcs(outer_section,sy-7-WALL,14+2*WALL)
def port_rect(z,wx,wy):
    pp=[V(sx-wx/2,sy-wy/2,z),V(sx+wx/2,sy-wy/2,z),
        V(sx+wx/2,sy+wy/2,z),V(sx-wx/2,sy+wy/2,z)]
    return Part.makePolygon(pp+pp[:1])
port_air=Part.makeLoft([port_rect(12,15.6,14),port_rect(iz,15.6,20)],True,True)
port_air=port_air.fuse(box(15.6,20,.6,pl,sy-10,iz))
port_outer=Part.makeLoft([port_rect(12,18.8,14+2*WALL),port_rect(iz,18.8,20+2*WALL)],True,True)
# Blend the full elbow footprint into the near leg instead of ending a
# trapezoidal reducer against the side of a circular bend. Both ends of
# the Bezier are tangent to the straight near-side walls. The far-side
# circular return is tangent to the elbow and longitudinal feed stem.
radius=P.get('blend_radius_mm',8.0)
return_radius=radius+WALL
return_cx,return_cy=57.5+return_radius,sy+7+return_radius
front=Part.BezierCurve()
front.setPoles([V(61,sy-7,0),V(57,sy-7,0),V(53,-19.5,0),V(47,-19.5,0)])
blend_edges=[front.toShape()]
points=[(47,-19.5),(47,-12.5),(50.5,-9),(50.5,return_cy+2),(57.5,return_cy+2),(57.5,return_cy)]
for a,b in zip(points,points[1:]):
    blend_edges.append(Part.makeLine(V(a[0],a[1],0),V(b[0],b[1],0)))
blend_edges.append(Part.Arc(V(57.5,return_cy,0),
    V(return_cx-return_radius/math.sqrt(2),return_cy-return_radius/math.sqrt(2),0),
    V(return_cx,sy+7,0)).toShape())
end_x=max(69,return_cx+1.9)
points=[(return_cx,sy+7),(end_x,sy+7),(end_x,sy-7),(61,sy-7)]
for a,b in zip(points,points[1:]):
    blend_edges.append(Part.makeLine(V(a[0],a[1],0),V(b[0],b[1],0)))
blend_face=Part.Face(Part.Wire(blend_edges))
blend_outer_face=blend_face.makeOffset2D(WALL,join=0,fill=False)
# OCC's exact OffsetCurve extrusion loses closed-solid topology on STEP
# export. Convert its boundary to ordinary NURBS before making the planar
# face, preserving the offset and tangent end conditions.
blend_outer_face=Part.Face(blend_outer_face.OuterWire.toNurbs())
assert blend_face.isValid() and blend_outer_face.isValid()
blend_wall=blend_face.OuterWire.distToShape(blend_outer_face.OuterWire)[0]
assert blend_wall>=WALL-1e-4,'Blend offset thins the sidewall beyond NURBS conversion tolerance'
blend_air=blend_face.extrude(V(0,0,ROOF-FLOOR))
blend_air.translate(V(0,0,FLOOR))
blend_outer=blend_outer_face.extrude(V(0,0,TOP-BASE))
blend_outer.translate(V(0,0,BASE))
# Retain the staged closure of the feed stem and corner panels.
blend_air=blend_air.cut(box(7,20.6,.4,50.5,-9,ROOF-.4))
for ya,yb in [(-30,-8.95),(11.55,30)]:
    blend_air=blend_air.cut(box(10.6,yb-ya,.2,46.95,ya,ROOF-.2))
adapter_air=union([elbow_air,port_air,blend_air])
air=union([air,adapter_air])
# A short rounded guide vane supports the broad blend roof. It follows
# the X flow direction and leaves the two sides connected around both ends.
guide_vane = extrude_plan(stroke([(57.5,-12),(61.5,-12)],.6),FLOOR,ROOF-FLOOR)
air = air.cut(guide_vane).removeSplitter()
outer=union([outer,elbow_outer,port_outer,blend_outer])

# Two accessible vertical duct bolts into captive nuts in the underside bracket.
duct_mounts = [(44.4, -7.0), (44.4, 9.6)]
for x, y in duct_mounts:
    outer = outer.fuse(box(12.2, 11, TOP-BASE, 38.3, y-5.5, BASE))
    outer = outer.fuse(box(9, 11, DUCT_MOUNT_TOP-TOP, x-3.5, y-5.5, TOP))
duct = outer.cut(air)
for x, y in duct_mounts:
    duct = duct.cut(cyl(1.65, 30, (x, y, 0)))
    duct = duct.cut(cyl(3.8, TOP, (x, y, 0)))
duct = duct.removeSplitter()
rounding=[]
# Round the two base corners and four flared inlet corners as one connected
# operation. Keep bed-facing horizontal edges sharp to preserve bed contact.
selected=[]
for edge in duct.Edges:
    bb=edge.BoundBox
    outboard=abs(bb.XMin-(pr+WALL))<1e-5 and bb.XLength<1e-5
    inlet_side=outboard or (abs(bb.XMin-(pl-WALL))<1e-5 and bb.XLength<1e-5)
    base_corner=(outboard and bb.YLength<1e-5 and abs(bb.ZMin-BASE)<1e-5
                 and abs(bb.ZMax-12)<1e-5 and min(abs(bb.YMin-(sy-7-WALL)),abs(bb.YMin-(sy+7+WALL)))<1e-5)
    flare_corner=(inlet_side and bb.YLength>1 and bb.ZLength>1 and abs(bb.ZMax-iz)<1e-5)
    if base_corner or flare_corner:
        selected.append(edge)
assert len(selected)==6,'Missing or ambiguous inlet corner edges'
unrounded=duct.copy()
duct=duct.makeFillet(P.get('inlet_corner_radius_mm',1.2),selected).removeSplitter()
assert duct.isValid() and len(duct.Solids)==1,'Invalid inlet corner fillet'
removed=unrounded.cut(duct)
corner_gap=removed.distToShape(air)[0]
# The existing flared port has approximately 1.28 mm normal wall thickness.
# These corner cuts must not thin it below that existing minimum.
assert corner_gap>=1.28-1e-4,'Inlet rounding thins the flared port wall'
outer=outer.cut(removed).removeSplitter()
rounding=[{'inlet_corner_radius_mm':P.get('inlet_corner_radius_mm',1.2),
           'rounded_edges':len(selected),'cut_to_air_clearance_mm':corner_gap,
           'blend_outer_radius_mm':P.get('blend_radius_mm',8.0),
           'blend_sidewall_mm':blend_wall}]

# Underside fan support: two H2 M3 fixings, a clear motor-connector notch and
# an open circular intake window. Nothing bears on the heater or stock fan.
mount_x = P['bottom_mount_x_mm']
mount_ys = P['bottom_mount_y_mm']
plate = box(19, 34, 4, 31.4, -17, 18.2)
front_arm = (box(FRAME_X-49+2,6,4,49,-16,18.2))
back_y = (20)
back_arm = extrude_plan(stroke([(49,13),(60,back_y),(FRAME_X+2,back_y)],3),18.2,4)
frame = cyl(25, 4, (FRAME_X, rotor.y, rotor.z), (1, 0, 0))

def capsule_yz(a, b, r, x, depth):
    ay, az = a
    by, bz = b
    length = math.hypot(by-ay, bz-az)
    ny, nz = -(bz-az)/length*r, (by-ay)/length*r
    pp = [V(x, y, z) for y, z in [(ay+ny, az+nz), (by+ny, bz+nz),
                                  (by-ny, bz-nz), (ay-ny, az-nz)]]
    return union([Part.Face(Part.makePolygon(pp+pp[:1])).extrude(V(depth, 0, 0)),
                  cyl(r, depth, (x, ay, az), (1, 0, 0)),
                  cyl(r, depth, (x, by, bz), (1, 0, 0))])

frame = frame.fuse(capsule_yz((-13,20.2),(-12,24.5),3,FRAME_X,4))
frame = frame.fuse(capsule_yz((20,20.2),(19,23.8),3,FRAME_X,4))
for ear in ears:
    a,b=(((ear.y,ear.z-1),(ear.y,ear.z+FAN_UP)))
    frame = frame.fuse(capsule_yz(a,b,6,FRAME_X,4))
bracket = union([plate, front_arm, back_arm, frame])
bracket = bracket.common(box(FX+40,200,150,-40,-80,0))
intake_window = cyl(18.5,MOTOR_GAP+.2,(61.8,rotor.y,rotor.z),(1,0,0))
bracket = bracket.cut(intake_window)
for y in mount_ys:
    bracket = bracket.cut(cyl(1.65, 10, (mount_x, y, 16)))

def hex_z(x, y, z, height, af=5.75):
    radius = af/math.sqrt(3)
    pp = [V(x+radius*math.cos(i*math.pi/3), y+radius*math.sin(i*math.pi/3), z) for i in range(6)]
    return Part.Face(Part.makePolygon(pp+pp[:1])).extrude(V(0, 0, height))

def hex_x(y, z, x, depth, af=5.75):
    radius = af/math.sqrt(3)
    pp = [V(x, y+radius*math.cos(math.radians(30+i*60)),
            z+radius*math.sin(math.radians(30+i*60))) for i in range(6)]
    return Part.Face(Part.makePolygon(pp+pp[:1])).extrude(V(depth, 0, 0))

for x, y in duct_mounts:
    bracket = bracket.cut(cyl(1.65, 8, (x, y, 17)))
    bracket = bracket.cut(hex_z(x, y, 19.7, 2.6))
for ear in ears:
    a,b=(((ear.y,ear.z-1),(ear.y,ear.z+FAN_UP)))
    bracket = bracket.cut(capsule_yz(a,b,1.65,FRAME_X-.1,4.2))
    # Sweep the hexagon to retain parallel flats over the entire slot travel.
    rr = 5.75/math.sqrt(3)
    hh = 2.875
    yz=[(ear.y-hh,ear.z-1-rr/2),(ear.y,ear.z-1-rr),(ear.y+hh,ear.z-1-rr/2),
        (ear.y+hh,ear.z+FAN_UP+rr/2),(ear.y,ear.z+FAN_UP+rr),(ear.y-hh,ear.z+FAN_UP+rr/2)]
    # Carry the loading channel through the rear support arm as well as the frame.
    # This clears the lower nut insertion path while retaining the outer floor.
    start_x = (40.0)
    pp = [V(start_x,y,z) for y,z in yz]
    bracket = bracket.cut(Part.Face(Part.makePolygon(pp+pp[:1])).extrude(V(FRAME_X+2.5-start_x,0,0)))
bracket = bracket.removeSplitter()
# Open the underside of the frame around the rising elbow, with 0.3 mm
# clearance at its highest position. The fixed pad/spacer seats stay intact.
bracket = bracket.cut(box(4.3,24,20.3,FRAME_X-.1,-28.25,0))
bracket = bracket.cut(box(.5,24,.6,FX-.4,-28.25,20.3)).removeSplitter()

# Chain plate is generated alongside the stock hardware references.
chain = reference_geometry['chain_plate']

feature('Duct', 'PRINT - closed twin-feed O duct, underside attachment', duct)
feature('UndersideBracket', ('PRINT - underside fan bracket, outward intake'), bracket,
        color=(.13, .51, .69))
feature('ChainPlate', 'PRINT - chain plate', chain,
        color=(.13, .51, .69))
feature('CompleteAir', ('Connected air: downward elbow, near feed leg, ring and jets'), air,
        construction, (.25, .7, .95), False)
feature('FullOuter', 'Outer envelope before air and fixing cuts', outer, construction,
        (.7, .7, .7), False)
feature('IntakeKeepout', 'Unobstructed intake cylinder, 32.5 mm diameter',
        cyl(16.25,(10),((FX+15),rotor.y,rotor.z),(1,0,0)),
        construction, (.2, .8, .9), False)

# The underside threaded holes are represented separately from the simplified
# source body. Nominal pattern follows the supplied carriage SCAD (top/bottom).
body = doc.H2Body.Shape.copy()
for y in mount_ys:
    body = body.cut(cyl(1.5, 5, (mount_x, y, 22.2)))
doc.H2Body.Shape = body

bolts = []
for i, y in enumerate(mount_ys, 1):
    bolt = union([cyl(1.5, 8, (mount_x, y, 17.7)), cyl(2.85, 1.65, (mount_x, y, 16.05))])
    washer = cyl(3.5, .5, (mount_x, y, 17.7)).cut(cyl(1.6, .5, (mount_x, y, 17.7)))
    bolts.append(('h2_'+str(i), union([bolt, washer])))
for i, (x, y) in enumerate(duct_mounts, 1):
    bolt = union([cyl(1.5, 12, (x, y, 10.2)), cyl(2.85, 1.65, (x, y, 8.55))])
    washer = cyl(3.5, 2, (x, y, 10.2)).cut(cyl(1.6, 2, (x, y, 10.2)))
    nut = hex_z(x, y, 19.7, 2.4, 5.5)
    bolts.append(('duct_'+str(i), union([bolt, washer, nut])))
for i, ear in enumerate(ears, 1):
    bolt = union([cyl(1.5, 20, (FX-3.5, ear.y, ear.z), (1, 0, 0)),
                  cyl(2.85, 1.65, (FX+16.5, ear.y, ear.z), (1, 0, 0))])
    washer = cyl(3.5, 1.5, (FX+15, ear.y, ear.z), (1, 0, 0)).cut(
        cyl(1.6, 1.5, (FX+15, ear.y, ear.z), (1, 0, 0)))
    bolts.append(('fan_'+str(i), union([bolt, washer, hex_x(ear.y, ear.z, FRAME_X+.05, 2.4, 5.5)])))
for name, shape in bolts:
    feature('Hardware_'+name, name+' - reference hardware', shape, hardware, (.65, .67, .7))

def bounds(s):
    b = s.BoundBox
    return [b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax]

print('BUILT GEOMETRY', {n: {'valid':s.isValid(), 'solids':len(s.Solids), 'bounds':bounds(s)}
                        for n, s in [('duct',duct),('bracket',bracket),('chain',chain)]})
# Save a reviewable assembly even if a subsequent validation rejects exports.
doc.recompute()
construction.Visibility = False
layouts.Visibility = False
Gui.activeDocument().activeView().viewAxonometric()
Gui.activeDocument().activeView().fitAll()
doc.saveAs(os.path.join(OUT, NAME+'.FCStd').replace(chr(92), '/'))

reference_names = ['H2Body', 'Stock3510', 'HeaterSock', 'Nozzle', 'Heatbreak',
                   'MotorConnector', 'Blower5015', 'CarriageEnvelope', 'RodKeepouts']
report = {'design':('underside O duct; outward intake 5015 with tangent downward elbow'),
          'parameters':P, 'input_sha256':input_hashes, 'physical_print_tested':False,
          'elbow_blending':rounding,
          'hardware_checks_after_screw_membrane_removal':True,
          'airflow_tested':False, 'parts':{}, 'collisions_mm3':{}, 'hardware_collisions_mm3':{},
          'air_valid':air.isValid(), 'air_solids':len(air.Solids),
          'air_openings':[{'volume':s.Volume,'bounds':bounds(s)} for s in air.cut(outer).Solids],
          'heater_clearance_mm':duct.distToShape(doc.HeaterSock.Shape)[0],
          'blower_rod_clearance_mm':fan.distToShape(doc.RodKeepouts.Shape)[0],
          'bracket_rod_clearance_mm':bracket.distToShape(doc.RodKeepouts.Shape)[0],
          'intake_clearance_mm':(None),
          'fan_back_to_motor_mm':MOTOR_GAP,
          'outward_intake_check_depth_mm':(10),
          'frame_relief_window_mm':37.0,
          'fan_adjustment_axis':('Z'),'fan_adjustment_mm':[-1,FAN_UP],
          'vertical_leg_air_height_mm':7.6,'roof_stagger_mm':.4,
          'nozzle_outlet_x_mm':[TIP_X,28-TIP_X], 'nozzle_outlet_y_mm':YC,
          'nozzle_outlet_center_z_mm':(tip_bottom[1]+end_level)/2,
          'nozzle_angle_deg':15, 'jet_area_mm2_each':TIP_W*(end_level-tip_bottom[1])*co,
          'mount_pattern_note':'Underside M3 at X=37.4, Y=+/-7.5 follows supplied carriage SCAD; verify actual hole depths and wiring before fitting.'}
manufacturing = [('duct', duct), ('fan_bracket', bracket), ('chain_plate', chain)]
for name, shape in manufacturing:
    report['parts'][name] = {'valid':shape.isValid(), 'solids':len(shape.Solids),
                            'volume_mm3':shape.Volume, 'bounds_mm':bounds(shape)}
    report['collisions_mm3'][name] = {n:shape.common(doc.getObject(n).Shape).Volume for n in reference_names}
report['part_collisions_mm3'] = {a+'_'+b:s.common(t).Volume
    for i,(a,s) in enumerate(manufacturing) for b,t in manufacturing[i+1:]}
for name, shape in bolts:
    report['hardware_collisions_mm3'][name] = {n:shape.common(s).Volume for n,s in manufacturing}
    report['hardware_collisions_mm3'][name]['references'] = shape.common(
        Part.makeCompound([doc.getObject(n).Shape for n in reference_names])).Volume
report['air_blockage_mm3'] = union([duct, bracket]).common(air).Volume
report['fixing_bore_air_clearance_mm'] = [cyl(3.8,TOP,(x,y,0)).distToShape(air)[0] for x,y in duct_mounts]
report['fixing_bore_air_overlap_mm3'] = [cyl(3.8,TOP,(x,y,0)).common(air).Volume for x,y in duct_mounts]
report['intake_blockage_mm3'] = union([duct, bracket, chain]).common(doc.IntakeKeepout.Shape).Volume
report['slot_checks'] = []
for i in range(9):
    delta = -1+i*(FAN_UP+1)/8
    for ear in ears:
        yy,zz=((ear.y,ear.z+delta))
        shank = cyl(1.5,4.2,(FRAME_X-.1,yy,zz),(1,0,0))
        nut = hex_x(yy,zz,FRAME_X+.05,2.4,5.5)
        report['slot_checks'].append({'offset_mm':delta,'ear_y_mm':ear.y,
            'shank_overlap_mm3':shank.common(bracket).Volume,'nut_overlap_mm3':nut.common(bracket).Volume})
report['fan_travel_checks'] = []
for delta in [-1,FAN_UP]:
    moved = fan.copy()
    moved.translate((V(0,0,delta)))
    collisions = {n:moved.common(doc.getObject(n).Shape).Volume for n in
        ['H2Body','MotorConnector','Stock3510','CarriageEnvelope','RodKeepouts']}
    collisions['fan_bracket'] = moved.common(bracket).Volume
    report['fan_travel_checks'].append({'offset_mm':delta,'collisions_mm3':collisions,
                                       'rod_clearance_mm':moved.distToShape(doc.RodKeepouts.Shape)[0]})
report['fan_adjustment_note'] = (('Raise the duct with 4/2/0 mm spacers and the fan by 0/2/4 mm; see adjustable_mount_checks.json.'))
printed_envelope = Part.makeCompound([s for _, s in manufacturing]+[fan]+[s for _,s in bolts])
report['assembly_bounds_mm'] = bounds(printed_envelope)
report['added_mount_side_mm'] = max(0, -17.5-printed_envelope.BoundBox.YMin)
report['added_right_mm'] = printed_envelope.BoundBox.XMax-61.9
with open(os.path.join(OUT, 'validation.json'), 'w') as f:
    json.dump(report, f, indent=2)
print('VALIDATION', json.dumps(report, indent=2))
assert all(s.isValid() and len(s.Solids)==1 for _,s in manufacturing), 'Invalid/disconnected print'
assert air.isValid() and len(air.Solids)==1 and len(report['air_openings'])==3, 'Air route/openings'
assert report['air_blockage_mm3'] < 1e-5 and report['intake_blockage_mm3'] < 1e-5, 'Blocked air'
assert min(report['fixing_bore_air_clearance_mm'])>=1.59 and max(report['fixing_bore_air_overlap_mm3'])<1e-5, 'Fixing bore leaks or thins air wall'
assert all(v < 1e-5 for row in report['collisions_mm3'].values() for v in row.values()), 'Reference collision'
assert max(report['part_collisions_mm3'].values()) < 1e-5, 'Printed parts overlap'
assert all(v < 1e-5 for row in report['hardware_collisions_mm3'].values() for v in row.values()), 'Hardware collision'
assert all(max(r['shank_overlap_mm3'],r['nut_overlap_mm3'])<1e-5 for r in report['slot_checks']), 'Slot/nut travel'
assert all(max(r['collisions_mm3'].values())<1e-5 and r['rod_clearance_mm']>=2 for r in report['fan_travel_checks']), 'Fan travel clearance'
assert report['heater_clearance_mm'] >= 2 and duct.BoundBox.ZMin >= .99
assert report['blower_rod_clearance_mm'] >= 2 and report['bracket_rod_clearance_mm'] >= 2
assert all(hashlib.sha256(open(os.path.join(ROOT,n),'rb').read()).hexdigest()==h for n,h in input_hashes.items()), 'Build input changed'

checks = {}
import runpy
adjustment = runpy.run_path(os.path.join(ROOT, 'verify_underside_down_adjustment.py'))
height_report, spacer_shapes = adjustment['verify_and_add_spacers'](doc, P)
with open(os.path.join(OUT, 'adjustable_mount_checks.json'), 'w') as f:
    json.dump(height_report, f, indent=2)
manufacturing += list(spacer_shapes.items())
export_shapes = []
for name, shape in manufacturing:
    # A single sacrificial layer across each duct screw hole makes the first
    # counterbore ceiling a continuous short bridge. Pierce these films before
    # assembly; fit/hardware checks above use the prepared, open screw holes.
    if name == 'duct':
        shape = union([shape]+[cyl(1.65,.2,(x,y,TOP)) for x,y in duct_mounts])
    if name != 'spacer_2mm':
        export_shapes.append(shape)
    if name == 'spacer_4mm':
        rear = shape.copy()
        rear.translate(V(0,16.6,0))
        export_shapes.append(rear)
    step = os.path.join(OUT, name+'_assembled.step')
    shape.exportStep(step)
    pr = shape.copy()
    # Fan-facing plane on the bed; supports under the projecting H2 mounting pad.
    if name == 'fan_bracket':
        pr.rotate(V(), V(0,1,0), 90)
    elif name == 'chain_plate':
        pr.rotate(V(), V(1,0,0), 90)
    bb = pr.optimalBoundingBox()
    pr.translate(V(-bb.XMin,-bb.YMin,-bb.ZMin))
    feature('Print_'+name, 'Print orientation - '+name, pr, layouts, visible=False)
    target = os.path.join(OUT, name+'_print.stl')
    # Resolve the small inlet corner blends without skinny coarse facets that
    # misrepresent the supported curved surface as a steeper overhang.
    mesh_deflection=.02 if name=='duct' else .04
    mesh = MeshPart.meshFromShape(Shape=pr, LinearDeflection=mesh_deflection, AngularDeflection=.1, Relative=False)
    mesh.write(target)
    saved = Mesh.Mesh(target)
    _, facets = saved.Topology
    edges = Counter(tuple(sorted((f[i],f[(i+1)%3]))) for f in facets for i in range(3))
    reopened = Part.read(step)
    bed = sum(f.Area for f in pr.Faces if abs(f.CenterOfMass.z)<1e-6 and f.normalAt(0,0).z<-.99)
    steep = sum(f.Area for f in saved.Facets if -.9999<f.Normal.z<-.7072 and max(p[2] for p in f.Points)>.01)
    checks[name] = {'stl_watertight':saved.isSolid(), 'nonmanifold_edges':sum(v!=2 for v in edges.values()),
                    'step_valid':reopened.isValid(), 'step_solids':len(reopened.Solids),
                    'bed_area_mm2':bed, 'steep_nonbridge_area_mm2':steep,
                    'print_bounds_mm':[pr.BoundBox.XLength,pr.BoundBox.YLength,pr.BoundBox.ZLength],
                    'screw_hole_breakout_membrane_mm':.2 if name=='duct' else 0,
                    'mesh_linear_deflection_mm':mesh_deflection,
                    'stl_sha256':hashlib.sha256(open(target,'rb').read()).hexdigest(),
                    'supports':name=='fan_bracket'}
    assert saved.isSolid() and all(v==2 for v in edges.values()) and reopened.isValid() and len(reopened.Solids)==1
    assert bed>20, 'Insufficient bed face'
with open(os.path.join(OUT,'export_checks.json'),'w') as f:
    json.dump(checks,f,indent=2)
assert checks['duct']['steep_nonbridge_area_mm2']<1e-4, 'Duct exterior needs supports'
Part.makeCompound(export_shapes).exportStep(os.path.join(OUT,'printed_assembly.step'))
refs.Visibility = True
for n in reference_names:
    doc.getObject(n).Visibility = True
doc.H2Body.ViewObject.Transparency = 65
doc.CarriageEnvelope.ViewObject.Transparency = 80
doc.recompute()
doc.save()
print('EXPORTED', json.dumps(checks,indent=2))
