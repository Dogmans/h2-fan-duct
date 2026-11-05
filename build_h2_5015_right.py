"""FreeCAD MCP build: right motor-end mounted 5015 and twin nozzle ducts.
Run in FreeCAD GUI with App / Gui prebound. Millimetres.
X: photo left->right, Y: away from camera, Z: up; nozzle=(14,1.3,0).
"""
import os, json, math
import Part, Sketcher, MeshPart
from FreeCAD import Vector as V

ROOT=r'D:\Documents\git\biqu-h2-duct'
OUT=os.path.join(ROOT,'output','right_face')
os.makedirs(OUT,exist_ok=True)
P=dict(fan_center_y=-3.0,fan_outlet_z=28.0,fan_thickness=15.0,
       right_frame_thickness=4.0,socket_x=15.6,socket_y=20.0,
       main_wall=1.6,branch_wall=1.2,outlet_width=10.0,
       outlet_height=3.4,outlet_z=3.8,nozzle_side_distance=9.5)
cfg=os.path.join(ROOT,'right_face_parameters.json')
if os.path.exists(cfg): P.update({k:v for k,v in json.load(open(cfg)).items() if k in P})
name='H2_5015_Right'
if name in App.listDocuments(): App.closeDocument(name)
doc=App.newDocument(name)
refs=doc.addObject('App::DocumentObjectGroup','References'); refs.Label='REFERENCE ONLY - H2, blower and carriage'
construction=doc.addObject('App::DocumentObjectGroup','DuctConstruction'); construction.Label='Duct outer and air volume - hidden'
sheet=doc.addObject('Spreadsheet::Sheet','Dimensions')
sheet.set('A1','Parameter'); sheet.set('B1','mm'); sheet.set('C1','Edit right_face_parameters.json and rerun script')
for i,(k,v) in enumerate(P.items(),2): sheet.set('A'+str(i),k); sheet.set('B'+str(i),str(v))
sheet.setColumnWidth('A',200); sheet.setColumnWidth('C',380)

def box(dx,dy,dz,x,y,z): return Part.makeBox(dx,dy,dz,V(x,y,z))
def cy(r,h,x,y,z): return Part.makeCylinder(r,h,V(x,y,z),V(0,1,0))
def cx(r,h,x,y,z): return Part.makeCylinder(r,h,V(x,y,z),V(1,0,0))
def fuse(parts):
    s=parts[0]
    for p in parts[1:]: s=s.fuse(p)
    return s.removeSplitter()
def feature(name,label,s,color,group=None,visible=True):
    o=doc.addObject('Part::Feature',name); o.Label=label; o.Shape=s
    o.ViewObject.ShapeColor=color; o.ViewObject.LineColor=(0.13,0.16,0.19)
    o.ViewObject.Deviation=0.1
    if group: group.addObject(o)
    o.Visibility=visible
    return o
def capsule(a,b,r,y,depth):
    ax,az=a; bx,bz=b; l=math.hypot(bx-ax,bz-az); nx,nz=-(bz-az)/l*r,(bx-ax)/l*r
    pts=[V(x,y,z) for x,z in [(ax+nx,az+nz),(bx+nx,bz+nz),(bx-nx,bz-nz),(ax-nx,az-nz)]]
    return fuse([Part.Face(Part.makePolygon(pts+[pts[0]])).extrude(V(0,depth,0)),cy(r,depth,ax,y,az),cy(r,depth,bx,y,bz)])
def yz_rail(a,b,r):
    # Original capsule coords (u,v) become (Y,Z); original extrusion becomes +X.
    s=capsule(a,b,r,0,P['right_frame_thickness'])
    s.rotate(V(0,0,0),V(0,0,1),90)
    s.translate(V(61.9+P['right_frame_thickness'],0,0)); return s

# Measured/drawn reference envelopes, not printable components.
body=box(61.9,35,35,0,-17.5,22.2)
for z in [32.2,47.2]: body=body.cut(cy(1.5,5,37.4,-18,z))
o=feature('H2Body','H2 original body and motor envelope',body,(0.30,0.32,0.35),refs); o.ViewObject.Transparency=65
stock=box(10,35,35,-14.9,-17.5,22.2).cut(cx(14,12,-15.9,0,39.7))
feature('Stock3510','KEEP - stock 3510 heatsink cooling fan',stock,(0.23,0.25,0.28),refs)
heater=box(24,20,12,2,-8.7,9)
feature('HeaterSock','Heater / sock keepout - approximate',heater,(0.90,0.29,0.09),refs)
nozzle=fuse([Part.makeCone(0.4,3.5,4.5,V(14,1.3,0)),Part.makeCylinder(3.5,4.5,V(14,1.3,4.5))])
feature('Nozzle','Nozzle tip datum Z=0',nozzle,(0.87,0.67,0.24),refs)
feature('Heatbreak','Heatbreak simplified',Part.makeCylinder(3,5,V(14,1.3,21)),(0.7,0.7,0.72),refs)
connector=box(8,14,6,53.9,-7,16.2)
feature('MotorConnector','Motor connector keepout - verify actual plug / wires',connector,(0.40,0.41,0.43),refs)
# Carriage/rod dimensions from adjacent croxy_carriage_h2_touch_less_offset.scad.
crossrod=Part.makeCylinder(4,140,V(-20,29,59.2),V(1,0,0))
toprod=Part.makeCylinder(4,110,V(50.4,-40,82.2),V(0,1,0))
topbearing=Part.makeCylinder(11.5,45,V(50.4,-17.5,82.2),V(0,1,0)).cut(toprod)
backbearing=Part.makeCylinder(11.5,45,V(14.9,29,59.2),V(1,0,0)).cut(crossrod)
carriage=fuse([topbearing,backbearing])
o=feature('CarriageEnvelope','Carriage bearing envelopes - verify installed variant',carriage,(0.48,0.51,0.55),refs); o.ViewObject.Transparency=80
o=feature('RodKeepouts','8 mm rods inferred from bearing positions',Part.makeCompound([crossrod,toprod]),(0.67,0.70,0.74),refs,False)

# Combined chain and fan bracket replaces the original 3 mm chain plate.
# Original SCAD mapping: (x,y,z)->(37.4+z,-19+y,81.7-x).
chain=fuse([box(10,0.2,80,32.4,-17.5,26.7),box(17,0.2,20,28.9,-17.5,97.7),box(17,0.2,10,28.9,-17.5,91.7)])
arm=capsule((37.4,47.2),(59.4,48),5,-17.5,0.2)
front_profile=chain.fuse(arm).removeSplitter()
bracket=doc.addObject('PartDesign::Body','CombinedBracket'); bracket.Label='PRINT 1 - combined chain / right blower bracket'

def outline_sketch(name,shape,axis,plane,body_obj):
    sk=body_obj.newObject('Sketcher::SketchObject',name)
    if axis=='Y':
        sk.Placement=App.Placement(V(0,plane,0),App.Rotation(V(1,0,0),90)); proj=lambda p:V(p.x,p.z,0)
        faces=[f for f in shape.Faces if abs(f.normalAt(0,0).y)>0.99]
    else:
        sk.Placement=App.Placement(V(plane,0,0),App.Rotation(V(0,1,0),V(0,0,1),V(1,0,0),'ZXY')); proj=lambda p:V(p.y,p.z,0)
        faces=[f for f in shape.Faces if abs(f.normalAt(0,0).x)>0.99]
    face=max(faces,key=lambda f:f.Area)
    for e in face.Edges:
        if isinstance(e.Curve,Part.Line): sk.addGeometry(Part.LineSegment(proj(e.Vertexes[0].Point),proj(e.Vertexes[-1].Point)),False)
        elif isinstance(e.Curve,Part.Circle):
            sk.addGeometry(Part.Arc(proj(e.valueAt(e.FirstParameter)),proj(e.valueAt((e.FirstParameter+e.LastParameter)/2)),proj(e.valueAt(e.LastParameter))),False)
    doc.recompute(); return sk

sk=outline_sketch('ChainAndArmOutline',front_profile,'Y',-17.5,bracket)
pad=bracket.newObject('PartDesign::Pad','ChainAndArmPad'); pad.Profile=sk; pad.Length=3
doc.recompute(); sk.Visibility=False
holes=bracket.newObject('Sketcher::SketchObject','H2AndChainHoles')
holes.Placement=App.Placement(V(0,-20.5,0),App.Rotation(V(1,0,0),90))
for x,z in [(37.4,32.2),(37.4,47.2),(40.9,108.7),(33.4,105.2),(33.4,112.2)]:
    holes.addGeometry(Part.Circle(V(x,z,0),V(0,0,1),1.65),False)
doc.recompute(); pocket=bracket.newObject('PartDesign::Pocket','H2AndChainFixings'); pocket.Profile=holes; pocket.Length=3.1
doc.recompute(); holes.Visibility=False; pad.Visibility=False

fc=P['fan_center_y']; fz=P['fan_outlet_z']; zc=fz+25.8; fx=61.9+P['right_frame_thickness']; ft=P['fan_thickness']
fanholes=[(fc-22.2,zc+21.6),(fc+19.3,zc-17.4)]
frame=fuse([yz_rail((-17.5,48),fanholes[0],6),yz_rail((-17.5,48),fanholes[1],6),
            yz_rail(fanholes[0],fanholes[1],6),yz_rail(fanholes[1],(2.5,18.5),5)])
frame=frame.fuse(box(P['right_frame_thickness'],21,8,61.9,-8,14.5)).removeSplitter()
fs=outline_sketch('MotorEndFrameOutline',frame,'X',61.9,bracket)
fp=bracket.newObject('PartDesign::Pad','MotorEndFramePad'); fp.Profile=fs; fp.Length=P['right_frame_thickness']
doc.recompute(); fs.Visibility=False; pocket.Visibility=False
ns=bracket.newObject('Sketcher::SketchObject','DuctNutBossOutline')
ns.Placement=App.Placement(V(fx,0,0),App.Rotation(V(0,1,0),V(0,0,1),V(1,0,0),'ZXY'))
pts=[V(-8,14.5,0),V(13,14.5,0),V(13,22.5,0),V(-8,22.5,0)]
for a,b in zip(pts,pts[1:]+pts[:1]): ns.addGeometry(Part.LineSegment(a,b),False)
doc.recompute(); np=bracket.newObject('PartDesign::Pad','DuctNutBossPad'); np.Profile=ns; np.Length=2
doc.recompute(); ns.Visibility=False; fp.Visibility=False
fh=bracket.newObject('Sketcher::SketchObject','FanAndDuctHoles')
fh.Placement=App.Placement(V(fx+2,0,0),App.Rotation(V(0,1,0),V(0,0,1),V(1,0,0),'ZXY'))
for y,z in fanholes:
    # M3 slots, +/-1.5 mm in Y; large washers span 5015 housing holes.
    a=y-1.5; b=y+1.5; r=1.65
    fh.addGeometry(Part.LineSegment(V(a,z+r,0),V(b,z+r,0)),False)
    fh.addGeometry(Part.Arc(V(b,z+r,0),V(b+r,z,0),V(b,z-r,0)),False)
    fh.addGeometry(Part.LineSegment(V(b,z-r,0),V(a,z-r,0)),False)
    fh.addGeometry(Part.Arc(V(a,z-r,0),V(a-r,z,0),V(a,z+r,0)),False)
for y in [-3,8]: fh.addGeometry(Part.Circle(V(y,18.5,0),V(0,0,1),1.65),False)
doc.recompute(); fix=bracket.newObject('PartDesign::Pocket','FanAndDuctFixings'); fix.Profile=fh; fix.Length=P['right_frame_thickness']+2.1
doc.recompute(); fh.Visibility=False; np.Visibility=False
fn=bracket.newObject('Sketcher::SketchObject','FanNutTrapSketch')
fn.Placement=App.Placement(V(61.9,0,0),App.Rotation(V(0,1,0),V(0,0,1),V(1,0,0),'ZXY'))
for y,z in fanholes:
    vs=[V(y+a,z+b,0) for a,b in [(-4.82,0),(-3.16,-2.875),(3.16,-2.875),(4.82,0),(3.16,2.875),(-3.16,2.875)]]
    for a,b in zip(vs,vs[1:]+vs[:1]): fn.addGeometry(Part.LineSegment(a,b),False)
doc.recompute(); fnp=bracket.newObject('PartDesign::Pocket','FanCaptiveNuts'); fnp.Profile=fn; fnp.Length=2.5; fnp.Reversed=True
doc.recompute(); fn.Visibility=False; fix.Visibility=False
nh=bracket.newObject('Sketcher::SketchObject','M3NutTrapSketch')
nh.Placement=fn.Placement
for y in [-3,8]:
    vs=[V(y+3.32*math.cos(i*math.pi/3),18.5+3.32*math.sin(i*math.pi/3),0) for i in range(6)]
    for a,b in zip(vs,vs[1:]+vs[:1]): nh.addGeometry(Part.LineSegment(a,b),False)
doc.recompute(); final=bracket.newObject('PartDesign::Pocket','M3CaptiveNuts'); final.Profile=nh; final.Length=2.5; final.Reversed=True
doc.recompute(); nh.Visibility=False; fnp.Visibility=False; final.ViewObject.ShapeColor=(0.13,0.51,0.69)

# Standard 5015 silhouette: BeCool 5015-1 dimensioned hole coordinates.
parts=[cx(24.5,ft,fx,fc,zc),box(ft,19.3,26,fx,fc-27.2,fz)]
for y,z in fanholes:
    s=capsule((fc+(y-fc)*0.7,zc+(z-zc)*0.7),(y,z),4.3,0,ft)
    s.rotate(V(0,0,0),V(0,0,1),90); s.translate(V(fx+ft,0,0)); parts.append(s)
blower=fuse(parts).cut(cx(16.25,2,fx+ft-1.9,fc,zc))
for y,z in fanholes: blower=blower.cut(cx(2.35,ft+2,fx-1,y,z))
feature('Blower5015','BUY - 5015 right face, intake outward',blower,(0.18,0.20,0.23),refs)

def wire(c,t,w,h,flip=False):
    t=V(*t); t.normalize()
    if abs(t.x)+abs(t.y)<0.01: u=V(1,0,0)
    else: u=V(-t.y,t.x,0); u.normalize()
    if flip: u=-u
    v=t.cross(u); v.normalize(); c=V(*c)
    pts=[c+u*a*w/2+v*b*h/2 for a,b in [(-1,-1),(1,-1),(1,1),(-1,1)]]
    return Part.makePolygon(pts+[pts[0]])
def loft(spec,wall=0):
    return Part.makeLoft([wire(c,t,w+2*wall,h+2*wall) for c,t,w,h in spec],True,True)
def open_end(spec):
    c,t,w,h=spec[-1]; tvec=V(*t); tvec.normalize()
    return loft(spec).fuse(Part.Face(wire(c,t,w,h)).extrude(tvec*0.6))
sx=fx+ft/2; sy=fc-17.55; w=P['main_wall']
socket=box(P['socket_x']+2*w,P['socket_y']+2*w,3,sx-P['socket_x']/2-w,sy-P['socket_y']/2-w,fz-3)
socketair=box(P['socket_x'],P['socket_y'],10,sx-P['socket_x']/2,sy-P['socket_y']/2,fz-3.1)
# Drop around the motor end, then cross ahead of the cold body.
main=[((sx,sy,fz-1),(0,0,-1),P['socket_x'],P['socket_y']),
      ((sx,sy,fz-6),(0,0,-1),14,14),
      ((sx-3,-23,15),(-0.7,-0.1,-0.7),14,8),
      ((60,-23.5,12),(-1,0,0),14,8),((28,-23.5,12),(-1,0,0),14,8)]
ow,oh,oz=P['outlet_width'],P['outlet_height'],P['outlet_z']; dist=P['nozzle_side_distance']
left=[((30,-23.5,12),(-1,0,0),12,8),((9,-23.5,12),(-1,0,-0.1),10,8),
      ((-7,-20,12),(-0.6,0.5,-0.3),10,7),((-7,-7,8),(0,0.95,-0.3),10,6),
      ((-2,1.3,oz+0.6),(0.9,0.2,-0.3),ow,oh),((14-dist,1.3,oz),(0.9397,0,-0.342),ow,oh)]
right=[((34,-23.5,12),(0,0.9,-0.2),12,8),((36,-17,10),(0,0.95,-0.3),10,7),
       ((36,-7,8),(0,0.95,-0.3),10,6),((30,1.3,oz+0.6),(-0.9,0.2,-0.3),ow,oh),
       ((14+dist,1.3,oz),(-0.9397,0,-0.342),ow,oh)]
outer=fuse([socket,loft(main,w),loft(left,P['branch_wall']),loft(right,P['branch_wall'])])
air=fuse([socketair,loft(main),open_end(left),open_end(right)])
for label,s in [('MainAir',loft(main)),('LeftAir',loft(left)),('RightAir',loft(right))]:
    feature(label,label,s,(0.2,0.7,0.95),construction,False)
feature('OuterDuct','Outer lofts and socket',outer,(0.6,0.65,0.7),construction,False)
feature('AirPassage','Air volume - one inlet, two outlets',air,(0.2,0.7,0.95),construction,False)
# The brace is at the outer side of the frame, with 4 mm depth.
brace=capsule((sy,24),(2.5,18.5),3,0,4); brace.rotate(V(0,0,0),V(0,0,1),90); brace.translate(V(fx+6,0,0))
tabs=box(4,21,8,fx+2,-8,14.5).fuse(brace)
for y in [-3,8]: tabs=tabs.cut(cx(1.65,6,fx+1,y,18.5))
duct=outer.fuse(tabs).cut(air).removeSplitter()
ductobj=feature('TwinDuct','PRINT 2 - right 5015 to opposed nozzle jets',duct,(0.95,0.46,0.11))
ductobj.addProperty('App::PropertyString','DesignStatus').DesignStatus='Prototype: verify fan / sock / carriage dimensions and airflow on printer'
doc.recompute()

report={'layout':'RIGHT motor end; intake points right (+X)','parameters':P,'parts':{},'collisions_mm3':{}}
for key,s in [('bracket',final.Shape),('duct',duct),('air',air)]:
    b=s.BoundBox; report['parts'][key]={'valid':s.isValid(),'solids':len(s.Solids),'volume_mm3':s.Volume,'bounds':[b.XMin,b.XMax,b.YMin,b.YMax,b.ZMin,b.ZMax]}
for key,s in [('body',body),('heater',heater),('nozzle',nozzle),('stock_3510',stock),('connector',connector),('blower',blower),('carriage',carriage),('rods',Part.makeCompound([crossrod,toprod]))]:
    report['collisions_mm3'][key]={'bracket':final.Shape.common(s).Volume,'duct':duct.common(s).Volume,'blower':blower.common(s).Volume if key not in ['blower'] else 0}
report['heater_clearance_mm']=duct.distToShape(heater)[0]
report['air_blockage_mm3']=duct.common(air).Volume
outside=air.cut(outer); report['air_openings']=[s.Volume for s in outside.Solids]
report['mount_air_clearance_mm']=[cx(3.5,4,fx+2,y,18.5).distToShape(air)[0] for y in [-3,8]]
report['fan_to_motor_mm']=P['right_frame_thickness']
report['added_right_mm_fan']=P['right_frame_thickness']+ft
report['added_right_mm_including_socket']=duct.BoundBox.XMax-61.9
report['added_near_mm']=-(min(duct.BoundBox.YMin,final.Shape.BoundBox.YMin,blower.BoundBox.YMin)+17.5)
report['lowest_duct_mm']=duct.BoundBox.ZMin
report['jet_area_mm2_each']=P['outlet_width']*P['outlet_height']
report['jet_target_z_mm']=oz-dist*0.342/0.9397
report['rod_clearance_mm']={'fan':blower.distToShape(crossrod)[0],'bracket':final.Shape.distToShape(crossrod)[0]}
report['bracket_duct_interference_mm3']=final.Shape.common(duct).Volume
# Refuse to overwrite deliverables with failed geometry after a parameter edit.
json.dump(report,open(os.path.join(OUT,'validation.json'),'w'),indent=2)
for key in ['bracket','duct','air']:
    assert report['parts'][key]['valid'] and report['parts'][key]['solids']==1,(key,report['parts'][key])
assert len(report['air_openings'])==3, 'Air volume must exit only at the inlet and two jets'
assert report['air_blockage_mm3']<1e-5
assert report['heater_clearance_mm']>=2.0
assert report['lowest_duct_mm']>=1.0
assert report['bracket_duct_interference_mm3']<1e-5
assert all(v<1e-5 for row in report['collisions_mm3'].values() for v in row.values()),'Reference collision'
for ob,key in [(final,'h2_5015_right_bracket'),(ductobj,'h2_5015_right_twin_duct')]:
    ob.Shape.exportStep(os.path.join(OUT,key+'.step'))
    MeshPart.meshFromShape(Shape=ob.Shape,LinearDeflection=0.06,AngularDeflection=0.12,Relative=False).write(os.path.join(OUT,key+'.stl'))
Part.makeCompound([final.Shape,duct]).exportStep(os.path.join(OUT,'h2_5015_right_printed_assembly.step'))
json.dump(P,open(cfg,'w'),indent=2); json.dump(report,open(os.path.join(OUT,'validation.json'),'w'),indent=2)
Gui.activeDocument().activeView().viewAxonometric(); Gui.activeDocument().activeView().fitAll()
doc.recompute(); doc.saveAs(os.path.join(OUT,'H2_5015_Right.FCStd'))
print(json.dumps(report,indent=2))
