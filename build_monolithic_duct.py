"""Build a single continuous blower-to-nozzle duct with mounting fasteners only.
Uses the saved right-face H2 layout; does not alter its source document.
"""
import os, math, json
import Part, MeshPart, Mesh
from FreeCAD import Vector as V

ROOT=os.path.dirname(os.path.abspath(__file__))
OUT=os.path.join(ROOT,'output','monolithic')
os.makedirs(OUT,exist_ok=True)
src=App.getDocument('H2_5015_Right') if 'H2_5015_Right' in App.listDocuments() else App.openDocument(os.path.join(ROOT,'output','right_face','H2_5015_Right.FCStd'))
if 'H2_5015_Monolithic' in App.listDocuments(): App.closeDocument('H2_5015_Monolithic')
doc=App.newDocument('H2_5015_Monolithic')
doc.copyObject(src.References,True)
doc.copyObject(src.CombinedBracket,True)
build=doc.addObject('App::DocumentObjectGroup','Construction'); build.Label='Duct profiles and air - hidden'
parts=doc.addObject('App::DocumentObjectGroup','PrintedDuct'); parts.Label='PRINT - single continuous blower-to-nozzle duct'
layouts=doc.addObject('App::DocumentObjectGroup','PrintLayout'); layouts.Label='Print orientations - hidden, STLs use these placements'
layouts.Visibility=False

WALL=1.6; BASE=1.0
# A monolithic duct needs only the same 1.6 mm floor/roof as its side walls.
# Keep the 8 mm air height; lower the inlet datum to remove the former thick lid.
FLOOR=BASE+WALL; ROOF=FLOOR+8.0; TOP=ROOF+WALL
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
        # Tangent to the transverse rear edge: -20.5-(10+extra)=-30.5-extra.
        # The former -18.5 center left a redundant 2 mm square shoulder here.
        quarter(-3.3,-20.5,radius,inner,-1,-1),
        box(2*hb,16.8,1,-8.3-hb,-20.5,0),
        quarter(-3.3,-3.7,radius,inner,-1,1),
        box(2*hb,19.8,1,36.3-hb,-23.5,0),
        quarter(31.3,-3.7,radius,inner,1,1)])
def extrude_plan(s,z,height):
    face=max([f for f in s.Faces if f.normalAt(0,0).z>0.99],key=lambda f:f.Area)
    result=face.extrude(V(0,0,height)); result.translate(V(0,0,z-1)); return result

# Planar U manifold with a flat bed face and thin integral roof.
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
# Blower adapter: fixed Y width direction gives an untwisted elbow section.
def rect(center,t,width,height):
    t=V(*t); t.normalize(); u=V(0,1,0); v=t.cross(u); v.normalize(); c=V(*center)
    ps=[c+u*a*width/2+v*b*height/2 for a,b in [(-1,-1),(1,-1),(1,1),(-1,1)]]
    return Part.makePolygon(ps+[ps[0]])
stations=[((SX,SY,27.5),(0,0,-1),20,15.6),((SX,SY,22),(0,0,-1),16,13),
          ((SX-2,-22.5,15),(-0.707,0,-0.707),14,8),((64,-23.5,(FLOOR+ROOF)/2),(-1,0,0),14,8)]
def adapter_loft(w): return Part.makeLoft([rect(c,t,a+2*w,b+2*w) for c,t,a,b in stations],True,True)
# Constant-depth XZ profiles make the internal closures flat bridges rather than
# shallow, unsupported loft ceilings. Inlet and outlet mating dimensions stay fixed.
def constant_depth(s,ymin,ymax):
    profile=Part.makeFace(s.slice(V(0,1,0),SPLIT_Y),'Part::FaceMakerBullseye')
    profile.translate(V(0,ymin-SPLIT_Y,0))
    return profile.extrude(V(0,ymax-ymin,0))
adapter_air=constant_depth(adapter_loft(0),-30.5,-16.5).fuse(box(15.6,20,10,SX-7.8,SY-10,24.9))

def yz_solid(points,x,depth):
    vv=[V(x,y,z) for y,z in points]
    return Part.Face(Part.makePolygon(vv+[vv[0]])).extrude(V(depth,0,0))

def capsule_yz(a,b,r,x,depth):
    ay,az=a; by,bz=b; length=math.hypot(by-ay,bz-az)
    ny,nz=-(bz-az)/length*r,(by-ay)/length*r
    vs=[V(x,y,z) for y,z in [(ay+ny,az+nz),(by+ny,bz+nz),(by-ny,bz-nz),(ay-ny,az-nz)]]
    return union([Part.Face(Part.makePolygon(vs+[vs[0]])).extrude(V(depth,0,0)),
        cyl(r,depth,(x,ay,az),(1,0,0)),cyl(r,depth,(x,by,bz),(1,0,0))])

# Upright shell: a flat base under the elbow and a 45-degree underside under
# the original narrow mounting foot. No split seam, strap, keys or bolt ears.
adapter_outer=union([
    constant_depth(adapter_loft(WALL),-32.15,-14.9),
    box(18.8,17.25,18,64,-32.15,BASE),
    box(18.8,17.25,9,SX-9.4,-32.15,19),
    box(18.8,23.2,3,SX-9.4,SY-11.6,25),
    yz_solid([(-14.9,19.05),(-14.9,25),(-8.95,25)],SX-9.4,18.8),
    box(4,21,8,FX+2,-8,14.5),
    capsule_yz((SY,24),(2.5,18.5),3,FX+2,4),
    box(4,17.25,21.5,FX+2,-32.15,BASE),
    yz_solid([(-14.9,BASE),(-.5,BASE),(13,14.5),(13,22.5),(-14.9,22.5)],FX+2,4)])

# The native elbow ceiling already rises steeply enough to support itself in
# this upright orientation. Retain the smooth section instead of adding narrow
# artificial treads, which can be too thin for the slicer to anchor reliably.
allair=air.fuse(adapter_air).removeSplitter()
fullouter=outer.fuse(adapter_outer).removeSplitter()
duct=fullouter.cut(allair).removeSplitter()

def teardrop_x_up(y,z,r,x,depth):
    a=V(x,y-r/math.sqrt(2),z+r/math.sqrt(2))
    b=V(x,y+r/math.sqrt(2),z+r/math.sqrt(2))
    peak=V(x,y,z+r*math.sqrt(2))
    arc=Part.Arc(a,V(x,y,z-r),b).toShape()
    return Part.Face(Part.Wire([Part.makeLine(peak,a),arc,Part.makeLine(b,peak)])).extrude(V(depth,0,0))
for y in [-3,8]:
    duct=duct.cut(teardrop_x_up(y,18.5,1.65,FX+1,6))
    duct=duct.cut(teardrop_x_up(y,18.5,3.6,FX+6,14))
duct=duct.removeSplitter()

# Round the perimeter in plan, along vertical edges. This leaves the bed face
# flat; a fillet around the bottom horizontal edge would introduce an overhang.
# Select by position rather than transient OCC edge numbers.
corner_radii=[
    ('left inner vent turn',-1.7,-14.9,4.0),
    ('right inner vent turn',29.7,-14.9,4.0),
    ('vent-to-elbow branch',42.9,-14.9,4.0),
    ('mount foot root left',67.9,-14.9,3.0),
    ('mount foot root right',71.9,-14.9,3.0),
    ('left nozzle shoulder',-1.7,-5.3,0.8),
    ('right nozzle shoulder',29.7,-5.3,0.8),
    ('elbow outer front',82.8,-32.15,1.5),
    ('elbow outer rear',82.8,-14.9,1.5),
]
rounding=[]
unrounded=duct.copy()
for label,x,y,radius in corner_radii:
    selected=[]
    for edge in duct.Edges:
        bounds=edge.BoundBox
        if (bounds.XLength<1e-5 and bounds.YLength<1e-5
            and abs(bounds.XMin-x)<1e-4 and abs(bounds.YMin-y)<1e-4
            and abs(bounds.ZMin-BASE)<1e-4 and bounds.ZLength>0.5):
            selected.append(edge)
    assert len(selected)==1,'Missing or ambiguous corner: '+label
    rounded=duct.makeFillet(radius,selected)
    assert rounded.isValid() and len(rounded.Solids)==1,'Invalid radius: '+label
    removed=duct.cut(rounded)
    gap=removed.distToShape(allair)[0] if removed.Volume>1e-5 else None
    assert gap is None or gap>=1.59,'Radius would thin an air-passage wall: '+label
    rounding.append({'corner':label,'xy_mm':[x,y],'radius_mm':radius,
                     'removed_material_to_air_clearance_mm':gap})
    duct=rounded
duct=duct.removeSplitter()
fullouter=fullouter.cut(unrounded.cut(duct)).fuse(duct.cut(unrounded)).removeSplitter()

obj('Duct','PRINT - continuous blower inlet, elbow and opposed jets',duct,group=parts)
obj('LowerAir','Main channel and nozzle air volume',air,(0.25,0.7,0.95),build,False)
obj('AdapterAir','Continuous closed elbow air volume',adapter_air,(0.25,0.7,0.95),build,False)
obj('CompleteAir','Connected air route',allair,(0.25,0.7,0.95),build,False)

bb=duct.BoundBox
report={
    'design':'one continuous blower-to-nozzle print; continuous sloped elbow ceiling; upright support-free exterior',
    'parts':{'duct':{'valid':duct.isValid(),'solids':len(duct.Solids),'volume_mm3':duct.Volume,
        'bounds':[bb.XMin,bb.XMax,bb.YMin,bb.YMax,bb.ZMin,bb.ZMax]}},
    'joining_fasteners':0,'duct_mount_bolts':2,'duct_mount_hardware':'existing M3x10 button-head bolts, 0.5 mm washers, bracket captive nuts',
    'plastic_tapped_holes':0,'nominal_wall_mm':WALL,
    'vertical_corner_radii':rounding,'flat_print_base_preserved':True,
    'lower_duct_height_mm':TOP-BASE,'manifold_channel_mm':[14,ROOF-FLOOR],
    'side_arm_roof_step_mm':0.4,'side_arm_channel_height_mm':SIDE_ROOF-FLOOR,
    'inlet_center_z_mm':(FLOOR+ROOF)/2,'blower_outlet_plane_z_mm':28,
    'adapter_ceiling_step_mm':0,'adapter_air_max_z_quantization_mm':0,
    'nozzle_roof_step_mm':0.2,'nozzle_bridge_span_mm':10,'manifold_bridge_span_mm':14,
    'assembly_valid':duct.isValid(),'assembly_solids':len(duct.Solids),
    'air_valid':allair.isValid(),'air_solids':len(allair.Solids),
    'air_blockage_mm3':duct.common(allair).Volume,
    'air_openings':[{'volume':s.Volume,'bounds':str(s.BoundBox)} for s in allair.cut(fullouter).Solids],
    'collisions_mm3':{},'heater_clearance_mm':duct.distToShape(doc.HeaterSock.Shape)[0],
    'lowest_point_mm':bb.ZMin,'jet_area_mm2_each':TIP_W*(air_tiptop[1]-tipbottom[1])*cos,
    'outlet_center_z':(air_tiptop[1]+tipbottom[1])/2,
    'outlet_angle_deg':15,'added_near_mm':-bb.YMin-17.5,'added_right_mm':bb.XMax-61.9}
for name in ['H2Body','Stock3510','HeaterSock','Nozzle','Heatbreak','MotorConnector','Blower5015','CarriageEnvelope','RodKeepouts','CombinedBracket']:
    report['collisions_mm3'][name]=duct.common(doc.getObject(name).Shape).Volume
report['jet_target_z_mm']=report['outlet_center_z']-(14-TIP_X)*tan

# Reference the two existing mounting bolts only; these are excluded from STL.
hardware=doc.addObject('App::DocumentObjectGroup','MountHardware')
report['mount_hardware_interference_mm3']=[]
refs=Part.makeCompound([doc.getObject(n).Shape for n in report['collisions_mm3']])
for i,y in enumerate([-3,8],1):
    bolt=union([cyl(1.5,10,(FX-3.5,y,18.5),(1,0,0)),
                cyl(2.85,1.65,(FX+6.5,y,18.5),(1,0,0))])
    washer=cyl(3.5,0.5,(FX+6,y,18.5),(1,0,0)).cut(cyl(1.6,0.5,(FX+6,y,18.5),(1,0,0)))
    obj('MountBolt'+str(i),'Existing M3x10 mounting bolt '+str(i),bolt,(0.65,0.67,0.70),hardware)
    obj('MountWasher'+str(i),'Existing 0.5 mm mounting washer '+str(i),washer,(0.65,0.67,0.70),hardware)
    envelope=bolt.fuse(washer)
    report['mount_hardware_interference_mm3'].append({'duct':envelope.common(duct).Volume,
        'references':envelope.common(refs).Volume,'air':envelope.common(allair).Volume})
json.dump(report,open(os.path.join(OUT,'validation.json'),'w'),indent=2)
print(json.dumps(report,indent=2))
assert duct.isValid() and len(duct.Solids)==1,'Invalid / disconnected duct'
assert allair.isValid() and len(allair.Solids)==1,'Disconnected air route'
assert report['air_blockage_mm3']<1e-5 and len(report['air_openings'])==3,'Blocked or leaking air route'
assert all(v<1e-5 for v in report['collisions_mm3'].values()),'Reference collision'
assert all(v<1e-5 for row in report['mount_hardware_interference_mm3'] for v in row.values()),'Mount hardware interference'
assert report['heater_clearance_mm']>=2 and report['lowest_point_mm']>=0.99

step_path=os.path.join(OUT,'duct_assembled.step')
duct.exportStep(step_path)
pr=duct.copy(); bb=pr.optimalBoundingBox(); pr.translate(V(-bb.XMin,-bb.YMin,-bb.ZMin))
obj('Print_duct','Print orientation - flat base DOWN',pr,(0.95,0.46,0.12),layouts,False)
mesh=MeshPart.meshFromShape(Shape=pr,LinearDeflection=.04,AngularDeflection=.1,Relative=False)
stl_path=os.path.join(OUT,'duct_print.stl'); mesh.write(stl_path)
saved=Mesh.Mesh(stl_path); vv,ff=saved.Topology; edges={}
for f in ff:
    for a,b in [(f[0],f[1]),(f[1],f[2]),(f[2],f[0])]:
        edge=(min(a,b),max(a,b)); edges[edge]=edges.get(edge,0)+1
steep=[]; flat=[]; numeric_45_degree_area=[]
for f in saved.Facets:
    if f.Normal.z<-.7072 and max(p[2] for p in f.Points)>.01:
        # Float32 STL vertices can tilt tiny, skinny triangles on an exact
        # 45-degree plane. Confirm against that BREP plane before correcting
        # only this numerical classification; genuine overhangs still fail.
        if f.Area<0.01 and abs(f.Normal.z+math.sqrt(0.5))<0.001:
            center=sum((V(*p) for p in f.Points),V())/3
            distance,points,info=pr.distToShape(Part.Vertex(center))
            if distance<1e-5 and info[0][0]=='Face':
                face=pr.Faces[info[0][1]]  # distToShape uses zero-based indices.
                normal=face.normalAt(*info[0][2])
                if type(face.Surface).__name__=='Plane' and abs(normal.z+math.sqrt(0.5))<1e-10:
                    numeric_45_degree_area.append(f.Area)
                    continue
        (flat if f.Normal.z<-.9999 else steep).append(f.Area)
imported=Part.read(step_path)
bed_area=sum(f.Area for f in pr.Faces if abs(f.CenterOfMass.z)<1e-6 and f.normalAt(0,0).z<-0.99)
checks={'duct':{'stl_solid':saved.isSolid(),'nonmanifold_edges':sum(v!=2 for v in edges.values()),
    'step_valid':imported.isValid(),'step_solids':len(imported.Solids),
    'steep_nonbridge_area_mm2':sum(steep),'flat_bridge_area_mm2':sum(flat),
    'stl_roundoff_on_exact_45_degree_planes_mm2':sum(numeric_45_degree_area),
    'flat_bed_area_mm2':bed_area,'print_bounds_mm':[pr.BoundBox.XLength,pr.BoundBox.YLength,pr.BoundBox.ZLength]}}
json.dump(checks,open(os.path.join(OUT,'export_checks.json'),'w'),indent=2)
print('Export checks',checks)
assert saved.isSolid() and all(v==2 for v in edges.values()),'Nonmanifold STL'
assert imported.isValid() and len(imported.Solids)==1,'Invalid STEP reimport'
assert sum(steep)<1e-4 and bed_area>20,'Unsupported exterior slope or inadequate bed face'
doc.recompute()
Gui.activeDocument().activeView().viewAxonometric(); Gui.activeDocument().activeView().fitAll()
doc.saveAs(os.path.join(OUT,'H2_5015_Monolithic.FCStd'))
print('Exported one continuous duct with only the existing two M3 mount fixings')
