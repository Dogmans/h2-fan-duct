"""Build a flat tray/cover and two accessible adapter halves via FreeCAD MCP.
Uses the saved right-face H2 layout; does not alter its source document.
"""
import os, math, json
import Part, MeshPart, Mesh
from FreeCAD import Vector as V

ROOT=r'D:\Documents\git\biqu-h2-duct'
OUT=os.path.join(ROOT,'output','printable')
os.makedirs(OUT,exist_ok=True)
src=App.getDocument('H2_5015_Right') if 'H2_5015_Right' in App.listDocuments() else App.openDocument(os.path.join(ROOT,'output','right_face','H2_5015_Right.FCStd'))
if 'H2_5015_Printable' in App.listDocuments(): App.closeDocument('H2_5015_Printable')
doc=App.newDocument('H2_5015_Printable')
doc.copyObject(src.References,True)
doc.copyObject(src.CombinedBracket,True)
build=doc.addObject('App::DocumentObjectGroup','Construction'); build.Label='Duct profiles and air - hidden'
parts=doc.addObject('App::DocumentObjectGroup','PrintedDuct'); parts.Label='PRINT - four duct sections'
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
left_air=xz_solid([(-3.3,FLOOR),corner_bottom,tipbottom,tiptop,corner_top,(-3.3,ROOF)],YC-TIP_W/2,TIP_W)
# Continue each air cut through the outlet face without changing the upstream profile.
endwire=Part.makePolygon([V(tipbottom[0],YC-TIP_W/2,tipbottom[1]),V(tipbottom[0],YC+TIP_W/2,tipbottom[1]),V(tiptop[0],YC+TIP_W/2,tiptop[1]),V(tiptop[0],YC-TIP_W/2,tiptop[1]),V(tipbottom[0],YC-TIP_W/2,tipbottom[1])])
left_air=left_air.fuse(Part.Face(endwire).extrude(V(0.6,0,0)))
left_cap=xz_solid(roof+list(reversed(outerroof)),YC-TIP_W/2-WALL,TIP_W+2*WALL)
# Trim the main roof where it meets the two descending nozzle roofs.
trim_left=box(16.7,TIP_W+2*WALL,30,-3.3,YC-TIP_W/2-WALL,BASE)
trim_right=mirror_x(trim_left)
mainouter=mainouter.cut(trim_left).cut(trim_right)
outer=union([mainouter,left_outer,mirror_x(left_outer)])
air=union([mainair,left_air,mirror_x(left_air)])
cap_main=mainouter.common(box(150,100,20,-30,-50,ROOF))
cap=union([cap_main,left_cap,mirror_x(left_cap)])

# Four accessible lid screws, outside the air passages.
lid_screws=[(50,-14.5),(18,-14.5),(-8.3,-30),(43.8,-10)]
bosses=union([cyl(3,TOP-BASE,(x,y,BASE)) for x,y in lid_screws])
outer=outer.fuse(bosses).removeSplitter()
cap=cap.fuse(bosses.common(box(150,100,10,-30,-50,ROOF))).removeSplitter()

# The flat 4 mm cover accepts a blind collar screw above the air roof.
collar_pilot=cyl(0.85,2.7,(62,-23.5,13.4))
cap=cap.cut(collar_pilot); outer=outer.cut(collar_pilot)

tray=outer.cut(air).cut(cap).removeSplitter()
for x,y in lid_screws:
    tray=tray.cut(cyl(0.85,5.1,(x,y,7)))
    cap=cap.cut(cyl(1.15,TOP-11.9+0.2,(x,y,11.9)))
tray=tray.removeSplitter(); cap=cap.removeSplitter()

# Blower adapter: fixed Y width direction gives an untwisted elbow section.
def rect(center,t,width,height):
    t=V(*t); t.normalize(); u=V(0,1,0); v=t.cross(u); v.normalize(); c=V(*center)
    ps=[c+u*a*width/2+v*b*height/2 for a,b in [(-1,-1),(1,-1),(1,1),(-1,1)]]
    return Part.makePolygon(ps+[ps[0]])
stations=[((SX,SY,27.5),(0,0,-1),20,15.6),((SX,SY,22),(0,0,-1),16,13),
          ((SX-2,-22.5,15),(-0.707,0,-0.707),14,8),((64,-23.5,8),(-1,0,0),14,8)]
def adapter_loft(w): return Part.makeLoft([rect(c,t,a+2*w,b+2*w) for c,t,a,b in stations],True,True)
adapter_outer=adapter_loft(WALL).fuse(box(18.8,23.2,3,SX-9.4,SY-11.6,25))
adapter_air=adapter_loft(0).fuse(box(15.6,20,10,SX-7.8,SY-10,24.9))
# Open-bottom locating collar: 0.2 mm clearance around tray sides; lid boss supports top.
collar=box(4,20,16.8,61,-33.5,1).cut(box(3.1,17.6,15.3,60.9,-32.3,0.9))
collar=collar.cut(cyl(1.15,3,(62,-23.5,15.9)))
adapter_outer=adapter_outer.fuse(collar)
# Existing two M3 fixing positions, still on the right motor-end frame.
def capsule_yz(a,b,r,x,depth):
    ay,az=a; by,bz=b; length=math.hypot(by-ay,bz-az); ny,nz=-(bz-az)/length*r,(by-ay)/length*r
    vs=[V(x,y,z) for y,z in [(ay+ny,az+nz),(by+ny,bz+nz),(by-ny,bz-nz),(ay-ny,az-nz)]]
    return union([Part.Face(Part.makePolygon(vs+[vs[0]])).extrude(V(depth,0,0)),cyl(r,depth,(x,ay,az),(1,0,0)),cyl(r,depth,(x,by,bz),(1,0,0))])
mount=box(4,21,8,FX+2,-8,14.5).fuse(capsule_yz((SY,24),(2.5,18.5),3,FX+2,4))
for y in [-3,8]: mount=mount.cut(cyl(1.65,6,(FX+1,y,18.5),(1,0,0)))
adapter_outer=adapter_outer.fuse(mount)
# The two split-joint lugs accept through M2 screws and captive nuts.
adapter_screws=[(63.5,24),(72,8)]
for x,z in adapter_screws: adapter_outer=adapter_outer.fuse(cyl(3,7,(x,SPLIT_Y-3.5,z),(0,1,0)))
adapter=adapter_outer.cut(adapter_air).removeSplitter()
for x,z in adapter_screws:
    adapter=adapter.cut(cyl(1.15,10,(x,SPLIT_Y-4,z),(0,1,0)))
    rr=2.48; pp=[V(x+rr*math.cos(i*math.pi/3),SPLIT_Y+3.5,z+rr*math.sin(i*math.pi/3)) for i in range(6)]
    nut=Part.Face(Part.makePolygon(pp+[pp[0]])).extrude(V(0,-1.8,0))
    adapter=adapter.cut(nut)
adapter=adapter.removeSplitter()
front=adapter.common(box(160,80,80,-30,SPLIT_Y-80,0)).removeSplitter()
back=adapter.common(box(160,80,80,-30,SPLIT_Y,0)).removeSplitter()

obj('Tray','PRINT A - flat-bottom open channel tray',tray,group=parts)
obj('Cover','PRINT B - channel cover, outer roof to bed',cap,(1.0,0.65,0.22),parts)
obj('AdapterFront','PRINT C - blower adapter front half',front,(0.95,0.43,0.11),parts)
obj('AdapterBack','PRINT D - blower adapter back half + mounting foot',back,(0.87,0.35,0.10),parts)
obj('TrayAir','Main channel and nozzle air volume',air,(0.25,0.7,0.95),build,False)
obj('AdapterAir','Blower adapter air volume',adapter_air,(0.25,0.7,0.95),build,False)
obj('PlanProfile','Main planar channel outline',airplan,(0.5,0.5,0.5),build,False)
obj('NozzleProfile','Explicit untwisted left nozzle air profile',left_air,(0.25,0.7,0.95),build,False)

allparts=[tray,cap,front,back]
assembly=union(allparts)
allair=air.fuse(adapter_air).removeSplitter()
fullouter=outer.fuse(adapter_outer).removeSplitter()
obj('FullOuter','Outer envelopes - leak check',fullouter,(0.7,0.7,0.7),build,False)
report={'design':'flat open tray + cover + two accessible blower adapter halves','parts':{},'collisions_mm3':{},'outlet_center_z':TIP_Z,'outlet_angle_deg':15,'outlet_x':[TIP_X,28-TIP_X],'nominal_wall_mm':WALL}
for key,s in zip(['tray','cover','adapter_front','adapter_back'],allparts):
    bb=s.BoundBox; report['parts'][key]={'valid':s.isValid(),'solids':len(s.Solids),'volume_mm3':s.Volume,'bounds':[bb.XMin,bb.XMax,bb.YMin,bb.YMax,bb.ZMin,bb.ZMax]}
report['assembly_valid']=assembly.isValid(); report['assembly_solids']=len(assembly.Solids)
report['air_valid']=allair.isValid(); report['air_solids']=len(allair.Solids)
report['air_blockage_mm3']=assembly.common(allair).Volume
report['air_openings']=[{'volume':s.Volume,'bounds':str(s.BoundBox)} for s in allair.cut(fullouter).Solids]
for name in ['H2Body','Stock3510','HeaterSock','Nozzle','Heatbreak','MotorConnector','Blower5015','CarriageEnvelope','RodKeepouts','CombinedBracket']:
    reference=doc.getObject(name).Shape
    report['collisions_mm3'][name]=assembly.common(reference).Volume
report['heater_clearance_mm']=assembly.distToShape(doc.HeaterSock.Shape)[0]
report['lowest_point_mm']=assembly.BoundBox.ZMin
report['part_interference_mm3']={str((i,j)):allparts[i].common(allparts[j]).Volume for i in range(4) for j in range(i+1,4)}
report['tray_base_area_mm2']=sum(f.Area for f in tray.Faces if abs(f.CenterOfMass.z-BASE)<1e-6 and f.normalAt(0,0).z<-0.99)
report['cover_flat_outer_area_mm2']=sum(f.Area for f in cap.Faces if abs(f.CenterOfMass.z-TOP)<1e-6 and f.normalAt(0,0).z>0.99)
report['main_channel_mm']=[14,8]
report['jet_area_mm2_each']=TIP_W*TIP_H
report['jet_target_z_mm']=TIP_Z-(14-TIP_X)*tan
report['added_near_mm']=-assembly.BoundBox.YMin-17.5
report['added_right_mm']=assembly.BoundBox.XMax-61.9
report['lid_pilot_air_clearance_mm']=[cyl(0.85,5.1,(x,y,7)).distToShape(allair)[0] for x,y in lid_screws]
json.dump(report,open(os.path.join(OUT,'validation.json'),'w'),indent=2)
print(json.dumps(report,indent=2))
# Do not export an invalid manufacturing revision.
assert all(row['valid'] and row['solids']==1 for row in report['parts'].values()),'Invalid / disconnected print section'
assert report['air_valid'] and report['air_solids']==1,'Disconnected air route'
assert report['assembly_valid'] and report['assembly_solids']==1,'Disconnected assembled duct'
assert all(v<1e-5 for v in report['collisions_mm3'].values()),'Reference interference'
assert all(v<1e-5 for v in report['part_interference_mm3'].values()),'Overlapping mating parts'
assert report['air_blockage_mm3']<1e-5
assert len(report['air_openings'])==3,'Unintended air opening'
assert report['heater_clearance_mm']>=2.0
assert report['lowest_point_mm']>=0.99
assert min(report['lid_pilot_air_clearance_mm'])>=1.0

# Export each section already oriented for printing, individually on Z=0.
orient=[App.Rotation(),App.Rotation(V(1,0,0),180),App.Rotation(V(1,0,0),-90),App.Rotation(V(1,0,0),90)]
checks={}
for key,s,rot in zip(['tray','cover','adapter_front','adapter_back'],allparts,orient):
    s.exportStep(os.path.join(OUT,key+'_assembled.step'))
    pr=s.copy(); pr.Placement=App.Placement(V(0,0,0),rot).multiply(pr.Placement)
    # OCC's conservative BoundBox can include untrimmed loft surfaces after rotation.
    # The optimal box follows the trimmed solid and seats the actual seam on the bed.
    bb=pr.optimalBoundingBox(); pr.translate(V(-bb.XMin,-bb.YMin,-bb.ZMin))
    pobj=obj('Print_'+key,'Bed orientation - '+key,pr,(0.8,0.8,0.8),layouts,False)
    mesh=MeshPart.meshFromShape(Shape=pr,LinearDeflection=0.04,AngularDeflection=0.1,Relative=False)
    target=os.path.join(OUT,key+'_print.stl'); mesh.write(target)
    saved=Mesh.Mesh(target); vv,ff=saved.Topology; edges={}
    for f in ff:
        for a,b in [(f[0],f[1]),(f[1],f[2]),(f[2],f[0])]:
            edge=(min(a,b),max(a,b)); edges[edge]=edges.get(edge,0)+1
    imported=Part.read(os.path.join(OUT,key+'_assembled.step'))
    bed_area=sum(f.Area for f in pr.Faces if abs(f.CenterOfMass.z)<1e-6 and f.normalAt(0,0).z<-0.99)
    checks[key]={'stl_solid':saved.isSolid(),'nonmanifold_edges':sum(v!=2 for v in edges.values()),'step_valid':imported.isValid(),'step_solids':len(imported.Solids),'flat_bed_area_mm2':bed_area,'print_bounds_mm':[pr.BoundBox.XLength,pr.BoundBox.YLength,pr.BoundBox.ZLength]}
    assert bed_area>20,'Missing flat mating face at print bed'
    assert saved.isSolid() and all(v==2 for v in edges.values()) and imported.isValid() and len(imported.Solids)==1,key
json.dump(checks,open(os.path.join(OUT,'export_checks.json'),'w'),indent=2)
Part.makeCompound(allparts).exportStep(os.path.join(OUT,'duct_assembled.step'))
doc.recompute(); Gui.activeDocument().activeView().viewAxonometric(); Gui.activeDocument().activeView().fitAll()
doc.saveAs(os.path.join(OUT,'H2_5015_Printable.FCStd'))
print('Exported four printable duct sections:',checks)
