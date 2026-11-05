"""Run with the FreeCAD MCP bridge (App and Gui supplied by FreeCAD).
Units mm. X = photo left to right, Y = away from camera, Z = up.
The standard nozzle tip is (14, 1.3, 0). See README.md for provenance.
"""
import os, json, math
import Part, Sketcher, MeshPart
from FreeCAD import Vector as V

ROOT = r'D:\Documents\git\biqu-h2-duct'
OUT = os.path.join(ROOT, 'output')
os.makedirs(OUT, exist_ok=True)
P = dict(mount_x=37.4, mount_z_low=32.2, mount_pitch=15.0,
         near_face_y=-17.5, chain_thickness=3.0, bracket_thickness=4.0,
         fan_cx=34.7, fan_cz=78.0, fan_back_y=-24.5, fan_thickness=15.0,
         socket_width=20.0, socket_depth=15.6, wall=1.6,
         outlet_width=10.0, outlet_height=3.4, outlet_z=3.8,
         nozzle_side_distance=9.5)
custom = os.path.join(ROOT, 'parameters.json')
if os.path.exists(custom):
    P.update({k:v for k,v in json.load(open(custom)).items() if k in P})
name = 'H2_5015_Compact'
if name in App.listDocuments():
    App.closeDocument(name)
doc = App.newDocument(name)
refs = doc.addObject('App::DocumentObjectGroup','References')
refs.Label = 'REFERENCE ONLY - H2, chain and 5015'
stages = doc.addObject('App::DocumentObjectGroup','DuctConstruction')
stages.Label = 'Duct construction - outer / air passage'
params = doc.addObject('Spreadsheet::Sheet','Dimensions')
params.set('A1','Parameter'); params.set('B1','mm'); params.set('C1','Edit parameters.json and rerun build_h2_5015.py')
for row,(key,val) in enumerate(P.items(),2):
    params.set('A'+str(row),key); params.set('B'+str(row),str(val))
params.setColumnWidth('A',190); params.setColumnWidth('C',400)

def obj(name,label,shape,color,group=None,visible=True):
    o=doc.addObject('Part::Feature',name); o.Label=label; o.Shape=shape
    o.ViewObject.ShapeColor=color; o.ViewObject.LineColor=(0.15,0.17,0.20)
    if group: group.addObject(o)
    o.Visibility=visible
    return o

def box(dx,dy,dz,x,y,z): return Part.makeBox(dx,dy,dz,V(x,y,z))
def cy(r,h,x,y,z): return Part.makeCylinder(r,h,V(x,y,z),V(0,1,0))
def fuse_all(shapes):
    s=shapes[0]
    for other in shapes[1:]: s=s.fuse(other)
    return s.removeSplitter()

def xz_wire(points,y):
    vs=[V(x,y,z) for x,z in points]
    return Part.makePolygon(vs+[vs[0]])

def capsule(a,b,r,y,depth):
    ax,az=a; bx,bz=b; d=math.hypot(bx-ax,bz-az)
    nx,nz=-(bz-az)/d*r,(bx-ax)/d*r
    poly=xz_wire([(ax+nx,az+nz),(bx+nx,bz+nz),(bx-nx,bz-nz),(ax-nx,az-nz)],y)
    return fuse_all([Part.Face(poly).extrude(V(0,depth,0)),cy(r,depth,ax,y,az),cy(r,depth,bx,y,bz)])

# H2 reference: dimensions from original H2 drawing and user's carriage SCAD.
body=box(61.9,35,35,0,-17.5,22.2)
for z in [32.2,47.2]: body=body.cut(cy(1.5,5,37.4,-18,z))
h2=obj('H2Body','H2 body / motor simplified envelope',body,(0.26,0.28,0.31),refs)
h2.ViewObject.Transparency=65
fan3510=box(10,35,35,-14.9,-17.5,22.2).cut(Part.makeCylinder(14,12,V(-15.9,0,39.7),V(1,0,0)))
obj('StockHeatsinkFan','KEEP - original 3510 hotend cooling fan',fan3510,(0.18,0.19,0.21),refs)
heater=box(24,20,12,2,-8.7,9)
obj('HeaterSock','Heater/sock keepout - approximate 24 x 20 x 12',heater,(0.88,0.29,0.10),refs)
nozzle=fuse_all([Part.makeCone(0.4,3.5,4.5,V(14,1.3,0)),Part.makeCylinder(3.5,4.5,V(14,1.3,4.5))])
obj('Nozzle','Standard nozzle - tip datum Z=0',nozzle,(0.86,0.66,0.24),refs)
obj('Heatbreak','Heatbreak simplified',Part.makeCylinder(3,5,V(14,1.3,21)),(0.7,0.7,0.72),refs)

# Reconstruct supplied SCAD in its installed orientation; no change to source.
# Original (scad x,y,z) -> (37.4+z, -19+y, 81.7-x).
chain=fuse_all([box(10,3,80,32.4,-20.5,26.7),box(17,3,20,28.9,-20.5,97.7),box(17,3,10,28.9,-20.5,91.7)])
for x,z in [(37.4,32.2),(37.4,47.2),(40.9,108.7),(33.4,105.2),(33.4,112.2)]:
    chain=chain.cut(cy(1.65,5,x,-21.5,z))
chain_obj=obj('ExistingChain','Existing chain mount - SCAD envelope (round blend omitted)',chain,(0.39,0.43,0.48),refs)
chain_obj.ViewObject.Transparency=45

# Native editable PartDesign bracket: pad of open triangular frame, pockets.
bracket=doc.addObject('PartDesign::Body','MountBracket')
bracket.Label='PRINT 1 - chain-sharing fan bracket'
mount=(P['mount_x'],P['mount_z_low']+P['mount_pitch'])
fanholes=[(P['fan_cx']-22.2,P['fan_cz']+21.6),(P['fan_cx']+19.3,P['fan_cz']-17.4)]
rear=P['near_face_y']-P['chain_thickness']
# Profiles are generated from fused planar rails, retained as a sketch.
profile=fuse_all([box(10,0.2,16,41,rear,24),capsule((37.4,31.2),mount,5.0,rear,0.2),
                  capsule(mount,fanholes[0],4.5,rear,0.2),
                  capsule(mount,fanholes[1],6.0,rear,0.2),
                  capsule(fanholes[0],fanholes[1],4.5,rear,0.2)])
sk=doc.addObject('Sketcher::SketchObject','BracketOutline'); bracket.addObject(sk)
sk.Label='Bracket frame outline (XZ)'
sk.Placement=App.Placement(V(0,rear,0),App.Rotation(V(1,0,0),90))
# Convert the top face wires into exact line/arc sketch geometry.
face=min([f for f in profile.Faces if abs(f.normalAt(0,0).y)>0.99],key=lambda f:f.CenterOfMass.y)
for edge in face.Edges:
    c=edge.Curve
    if isinstance(c,Part.Line):
        a,b=edge.Vertexes[0].Point,edge.Vertexes[-1].Point
        sk.addGeometry(Part.LineSegment(V(a.x,a.z,0),V(b.x,b.z,0)),False)
    elif isinstance(c,Part.Circle):
        a=edge.valueAt(edge.FirstParameter); b=edge.valueAt(edge.LastParameter); m=edge.valueAt((edge.FirstParameter+edge.LastParameter)/2)
        sk.addGeometry(Part.Arc(V(a.x,a.z,0),V(m.x,m.z,0),V(b.x,b.z,0)),False)
doc.recompute()
pad=bracket.newObject('PartDesign::Pad','BracketPad'); pad.Profile=sk; pad.Length=P['bracket_thickness']; sk.Visibility=False
doc.recompute()
holes=bracket.newObject('Sketcher::SketchObject','BracketHoles')
holes.Label='H2 M3 clearance + blower M4 adjustment slots'
holes.Placement=App.Placement(V(0,rear-P['bracket_thickness'],0),App.Rotation(V(1,0,0),90))
for z in [P['mount_z_low'],P['mount_z_low']+P['mount_pitch']]:
    holes.addGeometry(Part.Circle(V(P['mount_x'],z,0),V(0,0,1),1.65),False)
# Each fan slot allows +/- 1.5 mm along local X; M4 washer required.
for x,z in fanholes:
    a=x-1.5; b=x+1.5; r=2.15
    holes.addGeometry(Part.LineSegment(V(a,z+r,0),V(b,z+r,0)),False)
    holes.addGeometry(Part.Arc(V(b,z+r,0),V(b+r,z,0),V(b,z-r,0)),False)
    holes.addGeometry(Part.LineSegment(V(b,z-r,0),V(a,z-r,0)),False)
    holes.addGeometry(Part.Arc(V(a,z-r,0),V(a-r,z,0),V(a,z+r,0)),False)
doc.recompute()
pocket=bracket.newObject('PartDesign::Pocket','BracketFixings'); pocket.Profile=holes; pocket.Length=4.1
doc.recompute(); holes.Visibility=False; pad.Visibility=False
pocket.ViewObject.ShapeColor=(0.16,0.52,0.69)

# Approximate commercial 5015 reference, based on BeCool 5015-1 drawing.
cx,cz=P['fan_cx'],P['fan_cz']; fy=P['fan_back_y']-P['fan_thickness']
fanparts=[cy(24.5,P['fan_thickness'],cx,fy,cz),box(19.3,P['fan_thickness'],26, cx-27.2,fy,cz-25.8)]
for x,z in fanholes:
    fanparts.append(capsule((cx+(x-cx)*0.7,cz+(z-cz)*0.7),(x,z),4.3,fy,P['fan_thickness']))
blower=fuse_all(fanparts)
blower=blower.cut(cy(16.25,2,cx,fy-0.1,cz))
for x,z in fanholes: blower=blower.cut(cy(2.35,P['fan_thickness']+2,x,fy-1,z))
obj('Blower5015','BUY - nominal 5015; housing is reference only',blower,(0.18,0.20,0.23),refs)

# Hollow dual ducts, formed from separate lofted exterior and air volumes.
def rectwire(center,tangent,width,height):
    t=V(*tangent); t.normalize()
    # Stable frame: wide dimension follows Y on side branches, X on inlet.
    if abs(t.x)+abs(t.y)<0.01: u=V(1,0,0)
    else: u=V(t.y,-t.x,0); u.normalize()
    v=t.cross(u); v.normalize()
    c=V(*center)
    pts=[c+u*a*width/2+v*b*height/2 for a,b in [(-1,-1),(1,-1),(1,1),(-1,1)]]
    return Part.makePolygon(pts+[pts[0]])

def loft_sections(spec,wall=0):
    return Part.makeLoft([rectwire(c,t,w+2*wall,h+2*wall) for c,t,w,h in spec],True,False)

# Butt socket accepts 19.3/19.5 x 15 mm outlet; gasket seals flat fan edge.
sx=cx-17.55; sy=fy+7.5; fz=cz-25.8
wall=P['wall']
outer_socket=box(P['socket_width']+2*wall,P['socket_depth']+2*wall,3,sx-(P['socket_width']+2*wall)/2,sy-(P['socket_depth']+2*wall)/2,fz-3)
socket_air=box(P['socket_width'],P['socket_depth'],10,sx-P['socket_width']/2,sy-P['socket_depth']/2,fz-3.1)
main=[((sx,sy,fz-2),(0,0,-1),P['socket_width'],P['socket_depth']),((sx,sy,39),(0,0,-1),20,13),((16,-31,29),(0,0,-1),23,12)]
main_outer=loft_sections(main,wall); main_air=loft_sections(main,0)
left=[((10,-33,31),(-0.6,0.2,-0.8),12,12),((1,-29,22),(-0.6,0.2,-0.8),11,10),
      ((-7,-20,14),(-0.2,0.6,-0.8),10,8),((-7,-7,9),(0,0.95,-0.3),10,6),
      ((-2,1.3,P['outlet_z']+0.6),(0.9,0.2,-0.3),P['outlet_width'],P['outlet_height']),((14-P['nozzle_side_distance'],1.3,P['outlet_z']),(0.9397,0,-0.342),P['outlet_width'],P['outlet_height'])]
right=[((23,-33,31),(0.6,0.2,-0.8),12,12),((31,-29,22),(0.6,0.2,-0.8),11,10),
       ((36,-20,14),(0.1,0.6,-0.8),10,8),((36,-7,9),(0,0.95,-0.3),10,6),
       ((30,1.3,P['outlet_z']+0.6),(-0.9,0.2,-0.3),P['outlet_width'],P['outlet_height']),((14+P['nozzle_side_distance'],1.3,P['outlet_z']),(-0.9397,0,-0.342),P['outlet_width'],P['outlet_height'])]
outer=fuse_all([outer_socket,main_outer,loft_sections(left,1.2),loft_sections(right,1.2)])
# Extend air cuts through both outlet faces; no end caps.
def extend(spec):
    c,t,w,h=spec[-1]; v=V(*t); v.normalize()
    return loft_sections(spec).fuse(Part.Face(rectwire(c,t,w,h)).extrude(v*0.6))
air=fuse_all([socket_air,main_air,extend(left),extend(right)])
obj('OuterDuct','Outer lofts and socket',outer,(0.65,0.65,0.68),stages,False)
obj('AirPassage','Connected air volume - section to inspect',air,(0.25,0.70,0.95),stages,False)
duct=outer.cut(air).removeSplitter()
# Integrated fork secures duct to the same rigid bracket; two M3 cross screws.
tabs=fuse_all([box(11,4,16,40,-28.5,24),capsule((sx,35),(46,32),3,-29,4)])
for z in [28,36]: tabs=tabs.cut(cy(1.65,6,46,-29.5,z))
duct=outer.fuse(tabs).cut(air).removeSplitter()
duct_obj=obj('TwinDuct','PRINT 2 - 5015 socket and opposed nozzle jets',duct,(0.94,0.47,0.12))
duct_obj.addProperty('App::PropertyString','DesignStatus').DesignStatus='Prototype: verify fan port, heater sock and carriage fit before hot test'

# Add matching duct screw holes in bracket foot as a native final pocket.
ds=bracket.newObject('Sketcher::SketchObject','DuctScrewHoles')
ds.Placement=App.Placement(V(0,rear-4,0),App.Rotation(V(1,0,0),90))
for z in [28,36]: ds.addGeometry(Part.Circle(V(46,z,0),V(0,0,1),1.65),False)
doc.recompute()
dp=bracket.newObject('PartDesign::Pocket','DuctFixings'); dp.Profile=ds; dp.Length=4.1
doc.recompute(); ds.Visibility=False; pocket.Visibility=False
dp.ViewObject.ShapeColor=(0.16,0.52,0.69)

doc.recompute()
report={'parameters':P,'parts':{},'collisions_mm3':{}}
for key,ob in [('bracket',dp),('duct',duct_obj),('air',doc.AirPassage)]:
    sh=ob.Shape; bb=sh.BoundBox
    report['parts'][key]={'valid':sh.isValid(),'solids':len(sh.Solids),'volume_mm3':sh.Volume,'bounds':[bb.XMin,bb.XMax,bb.YMin,bb.YMax,bb.ZMin,bb.ZMax]}
for key,shape in [('body',body),('heater',heater),('nozzle',nozzle),('chain',chain),('blower',blower),('stock_3510',fan3510)]:
    report['collisions_mm3'][key]={'duct':duct.common(shape).Volume,'bracket':dp.Shape.common(shape).Volume}
report['heater_clearance_mm']=duct.distToShape(heater)[0]
report['air_blockage_mm3']=duct.common(air).Volume
for ob,key in [(dp,'h2_5015_bracket'),(duct_obj,'h2_5015_twin_duct')]:
    ob.Shape.exportStep(os.path.join(OUT,key+'.step'))
    mesh=MeshPart.meshFromShape(Shape=ob.Shape,LinearDeflection=0.08,AngularDeflection=0.15,Relative=False)
    mesh.write(os.path.join(OUT,key+'.stl'))
Part.makeCompound([dp.Shape,duct]).exportStep(os.path.join(OUT,'h2_5015_printed_assembly.step'))
with open(os.path.join(OUT,'validation.json'),'w') as f: json.dump(report,f,indent=2)
with open(os.path.join(ROOT,'parameters.json'),'w') as f: json.dump(P,f,indent=2)
Gui.activeDocument().activeView().viewAxonometric(); Gui.activeDocument().activeView().fitAll()
doc.recompute()
doc.saveAs(os.path.join(OUT,'H2_5015_Compact.FCStd'))
Gui.activeDocument().activeView().saveImage(os.path.join(OUT,'assembly.png'),1600,1200,'White')
print(json.dumps(report,indent=2))
