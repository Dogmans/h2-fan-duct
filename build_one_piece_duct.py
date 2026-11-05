"""Build a one-piece bridged lower duct and two M3-bolted adapter halves.
Uses the saved right-face H2 layout; does not alter its source document.
"""
import os, math, json
import Part, MeshPart, Mesh
from FreeCAD import Vector as V

ROOT=os.path.dirname(os.path.abspath(__file__))
OUT=os.path.join(ROOT,'output','one_piece')
os.makedirs(OUT,exist_ok=True)
src=App.getDocument('H2_5015_Right') if 'H2_5015_Right' in App.listDocuments() else App.openDocument(os.path.join(ROOT,'output','right_face','H2_5015_Right.FCStd'))
if 'H2_5015_OnePiece' in App.listDocuments(): App.closeDocument('H2_5015_OnePiece')
doc=App.newDocument('H2_5015_OnePiece')
doc.copyObject(src.References,True)
doc.copyObject(src.CombinedBracket,True)
build=doc.addObject('App::DocumentObjectGroup','Construction'); build.Label='Duct profiles and air - hidden'
parts=doc.addObject('App::DocumentObjectGroup','PrintedDuct'); parts.Label='PRINT - one-piece lower duct and bolted adapter'
layouts=doc.addObject('App::DocumentObjectGroup','PrintLayout'); layouts.Label='Print orientations - hidden, STLs use these placements'
layouts.Visibility=False

WALL=1.6; BASE=1.0; FLOOR=4.0; ROOF=12.0; TOP=16.0
YC=1.3; TIP_X=1.5; TIP_Z=3.65; ANGLE=math.radians(15); TIP_W=10.; TIP_H=3.2
SPLIT_Y=-23.5
P=json.load(open(os.path.join(ROOT,'right_face_parameters.json')))
FX=61.9+P['right_frame_thickness']; SX=FX+P['fan_thickness']/2; SY=P['fan_center_y']-17.55

def box(dx,dy,dz,x,y,z): return Part.makeBox(dx,dy,dz,V(x,y,z))
def cyl(r,h,p,axis=(0,0,1)): return Part.makeCylinder(r,h,V(*p),V(*axis))
def union(shapes):
    s=shapes[0]
    for a in shapes[1:]: s=s.fuse(a)
    refined=s.removeSplitter()
    return refined if refined.isValid() else s
def obj(name,label,s,color=(0.94,0.46,0.12),group=None,visible=True):
    o=doc.addObject('Part::Feature',name); o.Label=label; o.Shape=s
    o.ViewObject.ShapeColor=color; o.ViewObject.LineColor=(0.15,0.17,0.2)
    o.ViewObject.Deviation=0.08
    if group: group.addObject(o)
    o.Visibility=visible; return o
def xz_face(points,y):
    pp=[V(x,y,z) for x,z in points]
    return Part.Face(Part.makePolygon(pp+[pp[0]]))
def xz_solid(points,y,width): return xz_face(points,y).extrude(V(0,width,0))
def mirror_x(s):
    return s.mirror(V(14,0,0),V(1,0,0))
def quarter(cx,cy,r,inner,xsign,ysign):
    s=cyl(r,1,(cx,cy,0))
    if inner>0: s=s.cut(cyl(inner,1,(cx,cy,0)))
    return s.common(box(r+0.1,r+0.1,1,cx if xsign>0 else cx-r-0.1,cy if ysign>0 else cy-r-0.1,0))
def plan(extra):
    hm=7+extra; hb=5+extra; radius=5+hb; inner=max(0,5-hb)
    return union([
        box(67.3,2*hm,1,-3.3,-23.5-hm,0),
        quarter(-3.3,-18.5,radius,inner,-1,-1),
        box(2*hb,14.8,1,-8.3-hb,-18.5,0),
        quarter(-3.3,-3.7,radius,inner,-1,1),
        box(2*hb,19.8,1,36.3-hb,-23.5,0),
        quarter(31.3,-3.7,radius,inner,1,1)])
def extrude_plan(s,z,height):
    face=max([f for f in s.Faces if f.normalAt(0,0).z>0.99],key=lambda f:f.Area)
    result=face.extrude(V(0,0,height)); result.translate(V(0,0,z-1)); return result

# Planar U manifold: one flat floor, vertical sides, no roof until the cover is fitted.
airplan=plan(0); outerplan=plan(WALL)
mainair=extrude_plan(airplan,FLOOR,ROOF-FLOOR)
# Close the side arms two layers before the transverse manifold. This gives
# the slicer separate bridge regions with perpendicular short-span directions,
# rather than one U-shaped region bridged along the full length of an arm.
SIDE_ROOF=ROOF-0.4
mainair=mainair.cut(box(150,100,0.4,-30,-16.5,SIDE_ROOF)).removeSplitter()
mainouter=extrude_plan(outerplan,BASE,TOP-BASE)

# Nozzle profile is an explicit 2D section extruded across Y. No twisting lofts.
sin=math.sin(ANGLE); cos=math.cos(ANGLE); tan=math.tan(ANGLE)
# Vertical mouth faces print without a projecting lip. The last straight channel
# still slopes 15 degrees, so the jet direction is set by the walls, not a tilted cut.
tipbottom=(TIP_X,TIP_Z-TIP_H/2/cos)
tiptop=(TIP_X,TIP_Z+TIP_H/2/cos)
corner_x=-2.0
corner_center_z=TIP_Z+(TIP_X-corner_x)*tan
corner_bottom=(corner_x,corner_center_z-TIP_H/2/cos)
corner_top=(corner_x,corner_center_z+TIP_H/2/cos)
roof=[(-4.9,ROOF),(-3.3,ROOF),corner_top,tiptop]

def offset_roof(points,distance):
    lines=[]
    for i,(a,b) in enumerate(zip(points,points[1:])):
        distance=TOP-ROOF if i==0 else WALL
        dx,dz=b[0]-a[0],b[1]-a[1]; ll=math.hypot(dx,dz)
        nx,nz=-dz/ll*distance,dx/ll*distance
        lines.append(((a[0]+nx,a[1]+nz),(b[0]+nx,b[1]+nz)))
    out=[lines[0][0]]
    for i in range(1,len(lines)):
        a,b=lines[i-1]; c,d=lines[i]
        ux,uz=b[0]-a[0],b[1]-a[1]; vx,vz=d[0]-c[0],d[1]-c[1]
        k=((c[0]-a[0])*vz-(c[1]-a[1])*vx)/(ux*vz-uz*vx)
        out.append((a[0]+k*ux,a[1]+k*uz))
    out.append(lines[-1][1]); return out

outerroof=offset_roof(roof,WALL)
outerroof[-1]=(TIP_X,TIP_Z+(TIP_H/2+WALL)/cos)
tipbase=(TIP_X,BASE)
left_outer=xz_solid([(-4.9,BASE),tipbase]+list(reversed(outerroof)),YC-TIP_W/2-WALL,TIP_W+2*WALL)
# Small horizontal roof treads give the slicer explicit 10 mm bridge panels.
# They follow the same 15-degree mean slope within 0.1 mm, leaving >=1.5 mm roof.
level=round(corner_top[1]/0.2)*0.2
end_level=round(tiptop[1]/0.2)*0.2
stepped_roof=[(corner_x,level)]
while level>end_level+0.01:
    transition=TIP_X+(tiptop[1]-(level-0.1))/tan
    stepped_roof.extend([(transition,level),(transition,level-0.2)])
    level-=0.2
stepped_roof.append((TIP_X,end_level))
air_tiptop=(TIP_X,end_level)
left_air=xz_solid([(-3.3,FLOOR),corner_bottom,tipbottom]+list(reversed(stepped_roof))+[(-3.3,ROOF)],YC-TIP_W/2,TIP_W)
# Continue each air cut through the outlet face without changing the upstream profile.
endwire=Part.makePolygon([V(tipbottom[0],YC-TIP_W/2,tipbottom[1]),V(tipbottom[0],YC+TIP_W/2,tipbottom[1]),V(air_tiptop[0],YC+TIP_W/2,air_tiptop[1]),V(air_tiptop[0],YC-TIP_W/2,air_tiptop[1]),V(tipbottom[0],YC-TIP_W/2,tipbottom[1])])
left_air=left_air.fuse(Part.Face(endwire).extrude(V(0.6,0,0)))
# Trim the main roof where it meets the two descending nozzle roofs.
trim_left=box(16.7,TIP_W+2*WALL,30,-3.3,YC-TIP_W/2-WALL,BASE)
trim_right=mirror_x(trim_left)
mainouter=mainouter.cut(trim_left).cut(trim_right)
outer=union([mainouter,left_outer,mirror_x(left_outer)])
air=union([mainair,left_air,mirror_x(left_air)])

# The lower duct is closed in one print. Its roof bridges 14 mm across the
# manifold and approximately 10 mm across the stepped nozzle passages.
lower=outer.cut(air).removeSplitter()
# Closed side pockets accept the adapter halves' retaining teeth. They remain
# outside the air passage; closing the two adapter halves captures the duct.
for ymin in [-32.2,-15.6]:
    lower=lower.cut(box(3.5,0.8,5,60,ymin,5.5))
lower=lower.removeSplitter()

# Blower adapter: fixed Y width direction gives an untwisted elbow section.
def rect(center,t,width,height):
    t=V(*t); t.normalize(); u=V(0,1,0); v=t.cross(u); v.normalize(); c=V(*center)
    ps=[c+u*a*width/2+v*b*height/2 for a,b in [(-1,-1),(1,-1),(1,1),(-1,1)]]
    return Part.makePolygon(ps+[ps[0]])
stations=[((SX,SY,27.5),(0,0,-1),20,15.6),((SX,SY,22),(0,0,-1),16,13),
          ((SX-2,-22.5,15),(-0.707,0,-0.707),14,8),((64,-23.5,8),(-1,0,0),14,8)]
def adapter_loft(w): return Part.makeLoft([rect(c,t,a+2*w,b+2*w) for c,t,a,b in stations],True,True)
# Constant-depth XZ profiles make the internal closures flat bridges rather than
# shallow, unsupported loft ceilings. Inlet and outlet mating dimensions stay fixed.
def constant_depth(s,ymin,ymax):
    profile=Part.makeFace(s.slice(V(0,1,0),SPLIT_Y),'Part::FaceMakerBullseye')
    profile.translate(V(0,ymin-SPLIT_Y,0))
    return profile.extrude(V(0,ymax-ymin,0))
adapter_outer=union([constant_depth(adapter_loft(WALL),-32.15,-14.9),
                     box(18.8,17.25,9,SX-9.4,-32.15,19),
                     box(18.8,23.2,3,SX-9.4,SY-11.6,25)])
adapter_air=constant_depth(adapter_loft(0),-30.5,-16.5).fuse(box(15.6,20,10,SX-7.8,SY-10,24.9))
def yz_solid(points,x,depth):
    vv=[V(x,y,z) for y,z in points]
    return Part.Face(Part.makePolygon(vv+[vv[0]])).extrude(V(depth,0,0))
# 45-degree external ramp into the wider inlet collar, on the rear half.
adapter_outer=adapter_outer.fuse(yz_solid([(-14.9,19.05),(-14.9,25),(-8.95,25)],SX-9.4,18.8))
# Roof strap and positive end stop replace the collar's unsupported closing lips.
# The two bolted halves capture side keys; the roof strap needs no screw.
collar=union([box(4,20,1.6,61,-33.5,16.2),box(1,20,15.4,64,-33.5,2.4)])
cc=[V(61,-13.5,0),V(64.8,-13.5,0),V(61,-17.3,0)]
collar=collar.cut(Part.Face(Part.makePolygon(cc+[cc[0]])).extrude(V(0,0,30)))
collar=collar.cut(yz_solid([(-14.9,2.4),(-13.5,2.4),(-13.5,3.8)],63.9,1.2))
adapter_outer=adapter_outer.fuse(collar)
# Existing two M3 fixing positions, still on the right motor-end frame.
def capsule_yz(a,b,r,x,depth):
    ay,az=a; by,bz=b; length=math.hypot(by-ay,bz-az); ny,nz=-(bz-az)/length*r,(by-ay)/length*r
    vs=[V(x,y,z) for y,z in [(ay+ny,az+nz),(by+ny,bz+nz),(by-ny,bz-nz),(ay-ny,az-nz)]]
    return union([Part.Face(Part.makePolygon(vs+[vs[0]])).extrude(V(depth,0,0)),cyl(r,depth,(x,ay,az),(1,0,0)),cyl(r,depth,(x,by,bz),(1,0,0))])
mount=box(4,21,8,FX+2,-8,14.5).fuse(capsule_yz((SY,24),(2.5,18.5),3,FX+2,4))
mount=mount.fuse(yz_solid([(-12.5,19),(-12.5,22.5),(-8,22.5),(-8,14.5)],FX+2,4))
adapter_outer=adapter_outer.fuse(mount)
# Print the adapters cavity-up. The front has a full, flat outer back. The rear
# grows from a wider foot along taper slopes <=45 degrees, retaining the air route.
adapter_outer=adapter_outer.fuse(constant_depth(adapter_outer,-33.5,SPLIT_Y))
def keel_wire(y,xmin,xmax,zmin,zmax):
    vv=[V(xmin,y,zmin),V(xmax,y,zmin),V(xmax,y,zmax),V(xmin,y,zmax)]
    return Part.makePolygon(vv+[vv[0]])
growth=(13-(-8))/(13-(-14.9))
keel=Part.makeLoft([
    keel_wire(13,FX+2,80.9,14.5,22.5),
    keel_wire(-8,FX+2,80.9+1.9*growth,14.5-12.1*growth,22.5+5.5*growth),
    keel_wire(-14.9,64,82.8,2.4,28),
    keel_wire(-16.1,64,82.8,2.4,28),
    keel_wire(-20,60.5,82.8,2.4,28),
    keel_wire(SPLIT_Y,60.5,82.8,2.4,28)],True,True)
# Preserve the integral lower roof's envelope and its 0.2 mm strap clearance.
keel=keel.cut(box(120,100,30,-56,-50,-13.8))
adapter_outer=adapter_outer.fuse(keel)
# An upper shoulder supports the full inlet collar before it appears in the build.
shoulder=Part.makeLoft([keel_wire(2,FX+2,80.9,22.5,23),
                         keel_wire(-8.95,64,82.8,23,28),
                         keel_wire(SPLIT_Y,64,82.8,23,28)],True,True)
adapter_outer=adapter_outer.fuse(shoulder)
adapter=adapter_outer.cut(adapter_air).removeSplitter()
# Horizontal M3 holes close with a 45-degree peak in the cavity-up orientation.
def teardrop_x(y,z,r,x,depth):
    a=V(x,y-r/math.sqrt(2),z-r/math.sqrt(2))
    b=V(x,y-r/math.sqrt(2),z+r/math.sqrt(2))
    peak=V(x,y-r*math.sqrt(2),z)
    arc=Part.Arc(a,V(x,y+r,z),b).toShape()
    wire=Part.Wire([Part.makeLine(peak,a),arc,Part.makeLine(b,peak)])
    return Part.Face(wire).extrude(V(depth,0,0))
for y in [-3,8]:
    adapter=adapter.cut(teardrop_x(y,18.5,1.65,FX+1,6))
    # Recessed heads keep the original M3x10 fastener seat despite the wider foot.
    adapter=adapter.cut(teardrop_x(y,18.5,3.6,FX+6,14))
# Two M3x10 socket-head bolts and ordinary M3 hex nuts replace every M2
# joint. The upper ear ramps out at 45 degrees in the rear print orientation.
upper_ear=Part.makeLoft([
    keel_wire(-33.5,57,65,19,29),
    keel_wire(-22.8,57,65,19,29),
    keel_wire(-17.7,62.1,65,19,29)],True,True)
lower_ear=box(8.0,12.5,9.5,74.8,-33.5,1.0)
front_web=box(8.0,1.6,19.0,74.8,-33.5,1.0)
adapter=union([adapter,upper_ear,lower_ear,front_web])
# Outside stems wrap around the duct wall; short teeth enter its closed pockets.
keys=union([
    box(4.75,0.9,4.5,60.25,-33.3,5.75),
    box(3.0,0.95,4.5,60.25,-32.6,5.75),
    box(4.75,0.9,4.5,60.25,-14.6,5.75),
    box(3.0,0.95,4.5,60.25,-15.35,5.75)])
adapter=adapter.fuse(keys)
bolt_centers=[(61,24),(78.8,5.6)]
bolt_voids=[]
nut_across_flats=5.8
for x,z in bolt_centers:
    shaft=cyl(1.7,15,(x,-35,z),(0,1,0))
    # Head bears at Y=-22; a 3 mm high M3 socket head ends at Y=-19.
    head=cyl(3.1,40,(x,-22,z),(0,1,0))
    radius=nut_across_flats/math.sqrt(3)
    vv=[V(x+radius*math.cos(math.radians(30+60*i)),-33.6,
          z+radius*math.sin(math.radians(30+60*i))) for i in range(6)]
    nut=Part.Face(Part.makePolygon(vv+[vv[0]])).extrude(V(0,4.6,0))
    cut=union([shaft,head,nut]); bolt_voids.append(cut)
    adapter=adapter.cut(cut)
adapter=adapter.removeSplitter()
front=adapter.common(box(160,80,80,-30,SPLIT_Y-80,0)).removeSplitter()
back=adapter.common(box(160,80,80,-30,SPLIT_Y,0)).removeSplitter()

obj('LowerDuct','PRINT A - one-piece lower duct, flat bottom DOWN',lower,group=parts)
obj('AdapterFront','PRINT B - flat back DOWN, cavity UP',front,(0.95,0.43,0.11),parts)
obj('AdapterBack','PRINT C - mounting foot DOWN, cavity UP',back,(0.87,0.35,0.10),parts)
obj('TrayAir','Main channel and nozzle air volume',air,(0.25,0.7,0.95),build,False)
obj('AdapterAir','Blower adapter air volume',adapter_air,(0.25,0.7,0.95),build,False)

names=['lower_duct','adapter_front','adapter_back']
allparts=[lower,front,back]
assembly=union(allparts)
allair=air.fuse(adapter_air).removeSplitter()
fullouter=outer.fuse(adapter_outer).fuse(upper_ear).fuse(lower_ear).fuse(front_web).fuse(keys).removeSplitter()
report={
    'design':'one-piece bridged lower duct; captured side keys; two M3-bolted adapter halves',
    'parts':{}, 'collisions_mm3':{},
    'internal_fasteners':{'bolts':2,'type':'M3x10 socket-head','nuts':2,'nut_type':'M3 hex, nominal 5.5 mm AF / 2.4 mm thick','plastic_tapped_holes':0},
    'existing_mount_fasteners':'two M3x10 adapter-to-bracket fasteners retained; fan and H2 mounting hardware retained',
    'bolt_centers_xz_mm':bolt_centers,
    'bolt_head_seat_y_mm':-22,'nut_seat_y_mm':-29,
    'bolt_hole_diameter_mm':3.4,'nut_pocket_across_flats_mm':nut_across_flats,
    'key_clearance_mm':0.25,'main_manifold_bridge_span_mm':14,
    'side_arm_roof_step_mm':0.4,'side_arm_channel_height_mm':SIDE_ROOF-FLOOR,
    'nozzle_bridge_span_mm':10,'nozzle_roof_step_mm':0.2,
    'nominal_wall_mm':WALL,'outlet_angle_deg':15,
}
for key,s in zip(names,allparts):
    bb=s.BoundBox
    report['parts'][key]={'valid':s.isValid(),'solids':len(s.Solids),'volume_mm3':s.Volume,
        'bounds':[bb.XMin,bb.XMax,bb.YMin,bb.YMax,bb.ZMin,bb.ZMax]}
report['assembly_valid']=assembly.isValid()
report['assembly_solids']=len(assembly.Solids)
report['air_valid']=allair.isValid(); report['air_solids']=len(allair.Solids)
report['air_blockage_mm3']=assembly.common(allair).Volume
report['air_openings']=[{'volume':s.Volume,'bounds':str(s.BoundBox)} for s in allair.cut(fullouter).Solids]
for name in ['H2Body','Stock3510','HeaterSock','Nozzle','Heatbreak','MotorConnector','Blower5015','CarriageEnvelope','RodKeepouts','CombinedBracket']:
    report['collisions_mm3'][name]=assembly.common(doc.getObject(name).Shape).Volume
report['heater_clearance_mm']=assembly.distToShape(doc.HeaterSock.Shape)[0]
report['lowest_point_mm']=assembly.BoundBox.ZMin
report['part_interference_mm3']={str((i,j)):allparts[i].common(allparts[j]).Volume for i in range(3) for j in range(i+1,3)}
report['bolt_pocket_air_clearance_mm']=[s.distToShape(allair)[0] for s in bolt_voids]
report['retaining_key_air_clearance_mm']=keys.distToShape(allair)[0]
report['jet_area_mm2_each']=TIP_W*(air_tiptop[1]-tipbottom[1])*cos
report['outlet_center_z']=(air_tiptop[1]+tipbottom[1])/2
report['jet_target_z_mm']=report['outlet_center_z']-(14-TIP_X)*tan
report['added_near_mm']=-assembly.BoundBox.YMin-17.5
report['added_right_mm']=assembly.BoundBox.XMax-61.9

# Model the two new bolts/nuts for fit checking and assembly views only.
hardware=doc.addObject('App::DocumentObjectGroup','JointHardware')
report['hardware_interference_mm3']=[]
for i,(x,z) in enumerate(bolt_centers,1):
    bolt=cyl(1.5,10,(x,-32,z),(0,1,0)).fuse(cyl(2.75,3,(x,-22,z),(0,1,0)))
    radius=5.5/math.sqrt(3)
    vv=[V(x+radius*math.cos(math.radians(30+60*j)),-31.4,
          z+radius*math.sin(math.radians(30+60*j))) for j in range(6)]
    nut=Part.Face(Part.makePolygon(vv+[vv[0]])).extrude(V(0,2.4,0))
    nut=nut.cut(cyl(1.5,3,(x,-31.5,z),(0,1,0)))
    obj('JointBolt'+str(i),'M3x10 socket-head bolt '+str(i),bolt,(0.65,0.67,0.70),hardware)
    obj('JointNut'+str(i),'M3 hex nut '+str(i),nut,(0.65,0.67,0.70),hardware)
    envelope=bolt.fuse(nut)
    refs=Part.makeCompound([doc.getObject(n).Shape for n in report['collisions_mm3']])
    report['hardware_interference_mm3'].append({'printed_parts':envelope.common(assembly).Volume,
        'references':envelope.common(refs).Volume,'air':envelope.common(allair).Volume})

json.dump(report,open(os.path.join(OUT,'validation.json'),'w'),indent=2)
print(json.dumps(report,indent=2))
assert all(row['valid'] and row['solids']==1 for row in report['parts'].values()),'Invalid / disconnected print section'
assert report['air_valid'] and report['air_solids']==1,'Disconnected air route'
assert report['assembly_valid'] and report['assembly_solids']==1,'Disconnected assembled duct'
assert all(v<1e-5 for v in report['collisions_mm3'].values()),'Reference interference'
assert all(v<1e-5 for v in report['part_interference_mm3'].values()),'Overlapping mating parts'
assert all(v<1e-5 for row in report['hardware_interference_mm3'] for v in row.values()),'Hardware interference'
assert report['air_blockage_mm3']<1e-5
assert len(report['air_openings'])==3,'Unintended air opening'
assert report['heater_clearance_mm']>=2.0
assert report['lowest_point_mm']>=0.99
assert min(report['bolt_pocket_air_clearance_mm'])>=0.8

# Verify a straight, separated-half assembly path before exporting.
path=[]
for travel in [0.25,0.5,1,2,4,8,12]:
    f=front.copy(); f.translate(V(0,-travel,0))
    b=back.copy(); b.translate(V(0,travel,0))
    path.append({'half_separation_mm':travel,'front_lower_overlap_mm3':f.common(lower).Volume,
                 'back_lower_overlap_mm3':b.common(lower).Volume})
report['assembly_path']=path
assert all(r['front_lower_overlap_mm3']<1e-5 and r['back_lower_overlap_mm3']<1e-5 for r in path),'Blocked assembly path'
# With the halves closed, the keys must stop the lower duct sliding out to the left.
shifted=lower.copy(); shifted.translate(V(-0.6,0,0))
report['retention_check_overlap_mm3']=shifted.common(front.fuse(back)).Volume
assert report['retention_check_overlap_mm3']>0.1,'Duct can slide out of the closed adapter'
json.dump(report,open(os.path.join(OUT,'validation.json'),'w'),indent=2)

orient=[App.Rotation(),App.Rotation(V(1,0,0),90),App.Rotation(V(1,0,0),-90)]
checks={}
for key,s,rot in zip(names,allparts,orient):
    step_path=os.path.join(OUT,key+'_assembled.step')
    s.exportStep(step_path)
    pr=s.copy(); pr.Placement=App.Placement(V(0,0,0),rot).multiply(pr.Placement)
    bb=pr.optimalBoundingBox(); pr.translate(V(-bb.XMin,-bb.YMin,-bb.ZMin))
    obj('Print_'+key,'Bed orientation - '+key,pr,(0.8,0.8,0.8),layouts,False)
    mesh=MeshPart.meshFromShape(Shape=pr,LinearDeflection=0.04,AngularDeflection=0.1,Relative=False)
    target=os.path.join(OUT,key+'_print.stl'); mesh.write(target)
    saved=Mesh.Mesh(target); vv,ff=saved.Topology; edges={}
    for f in ff:
        for a,b in [(f[0],f[1]),(f[1],f[2]),(f[2],f[0])]:
            edge=(min(a,b),max(a,b)); edges[edge]=edges.get(edge,0)+1
    imported=Part.read(step_path)
    steep=[]; flat_bridge=[]
    for f in saved.Facets:
        nz=f.Normal.z
        if nz<-.7072 and max(p[2] for p in f.Points)>.01:
            (steep if nz>-.9999 else flat_bridge).append(f.Area)
    bed_area=sum(f.Area for f in pr.Faces if abs(f.CenterOfMass.z)<1e-6 and f.normalAt(0,0).z<-0.99)
    checks[key]={'stl_solid':saved.isSolid(),'nonmanifold_edges':sum(v!=2 for v in edges.values()),
        'step_valid':imported.isValid(),'step_solids':len(imported.Solids),
        'steep_nonbridge_area_mm2':sum(steep),'flat_bridge_area_mm2':sum(flat_bridge),
        'flat_bed_area_mm2':bed_area,'print_bounds_mm':[pr.BoundBox.XLength,pr.BoundBox.YLength,pr.BoundBox.ZLength]}
    print(key,checks[key])
    assert sum(steep)<1e-4,'Steep unsupported face remains: '+key
    assert bed_area>20,'Missing flat bed face'
    assert saved.isSolid() and all(v==2 for v in edges.values()) and imported.isValid() and len(imported.Solids)==1,key
json.dump(checks,open(os.path.join(OUT,'export_checks.json'),'w'),indent=2)
Part.makeCompound(allparts).exportStep(os.path.join(OUT,'duct_assembled.step'))
doc.recompute()
Gui.activeDocument().activeView().viewAxonometric(); Gui.activeDocument().activeView().fitAll()
doc.saveAs(os.path.join(OUT,'H2_5015_OnePiece.FCStd'))
print('Exported one-piece lower duct and two M3-bolted adapter halves')
