import os, math, json
import Part, MeshPart, Mesh
from collections import Counter
from FreeCAD import Vector as V

ROOT=r'D:\Documents\git\biqu-h2-duct'
OUT=os.path.join(ROOT,'output','bracket_printable')
os.makedirs(OUT,exist_ok=True)
src=App.getDocument('H2_5015_SupportFree')
original=src.getObject('CombinedBracket').Shape.copy()
def box(x,y,z,a,b,c): return Part.makeBox(x,y,z,V(a,b,c))
def clean(s):
    t=s.removeSplitter()
    return t if t.isValid() else s
def poly(points,delta):
    return Part.Face(Part.makePolygon(points+[points[0]])).extrude(delta)
def cyl(x,y,z,length,r=1.65): return Part.makeCylinder(r,length,V(x,y,z),V(1,0,0))
def td(x,y,z,length):
    r=1.65; q=r/math.sqrt(2)
    a=V(x,y-q,z-q); b=V(x,y-q,z+q); p=V(x,y-r*math.sqrt(2),z)
    return Part.Face(Part.Wire([Part.makeLine(p,a),Part.Arc(a,V(x,y+r,z),b).toShape(),Part.makeLine(b,p)])).extrude(V(length,0,0))

# Preserve all original mounting geometry, splitting on the motor-end plane.
a=clean(original.common(box(161.9,200,200,-100,-100,-20)))
b=clean(original.common(box(100,200,200,61.9,-100,-20)))
a=clean(a.fuse(box(6,12,19,55.9,-29.5,38.5)))
b=clean(b.fuse(box(4,16,19,61.9,-29.5,38.5)))
for z in (43.5,52.5):
    a=a.cut(td(55.8,-24.5,z,6.2))
    verts=[V(55.8,-24.5+3.32*math.cos(math.radians(30+i*60)),z+3.32*math.sin(math.radians(30+i*60))) for i in range(6)]
    a=a.cut(poly(verts,V(2.6,0,0)))
    b=b.cut(cyl(61.8,-24.5,z,4.2))
    b=b.cut(Part.makeCone(3.15,1.65,1.5,V(65.9,-24.5,z),V(-1,0,0)))
key=poly([V(61.9,-22.5,46.5),V(63.4,-24,46.5),V(63.4,-26.5,46.5),V(61.9,-26.5,46.5)],V(0,0,3))
a=clean(a.fuse(key))
b=clean(b.cut(box(1.8,4.3,3.3,61.8,-26.65,46.35)))
assert a.isValid() and b.isValid()
assert len(a.Solids)==len(b.Solids)==1
assert a.common(b).Volume<1e-6
name='H2_5015_PrintableBracket'
if name in App.listDocuments(): App.closeDocument(name)
doc=App.newDocument(name)
report={'joint':'Two M3x10 countersunk screws and M3 nuts; locating key','parts':{},'collisions_mm3':{}}
printed=[]
for name,shape,axis,angle,color in [('chain_plate',a,V(1,0,0),-90,(0.2,0.55,0.85)),('fan_frame',b,V(0,1,0),-90,(0.95,0.55,0.15))]:
    ob=doc.addObject('PartDesign::Feature',name+'_assembled');ob.Label=name+' - assembled';ob.Shape=shape;ob.ViewObject.ShapeColor=color;ob.Visibility=False
    shape.exportStep(os.path.join(OUT,name+'_assembled.step'))
    s=shape.copy();s.rotate(V(0,0,0),axis,angle);bb=s.optimalBoundingBox();s.translate(V(-bb.XMin,-bb.YMin,-bb.ZMin))
    pr=doc.addObject('PartDesign::Feature',name+'_print');pr.Label=name+' - PRINT THIS ORIENTATION';pr.Shape=s;pr.ViewObject.ShapeColor=color
    if name=='fan_frame': pr.Placement.Base=V(52,0,0)
    printed.append(pr)
    path=os.path.join(OUT,name+'_print.stl')
    mesh=MeshPart.meshFromShape(Shape=s,LinearDeflection=.04,AngularDeflection=.1,Relative=False);mesh.write(path)
    points,facets=mesh.Topology;edges=Counter(tuple(sorted((f[i],f[(i+1)%3]))) for f in facets for i in range(3))
    steep=0; bridges=0;bed=0
    for f in mesh.Facets:
        nz=f.Normal.z;high=max(p[2] for p in f.Points)
        if nz<-.7072:
            if high<.01: bed+=f.Area
            elif nz<-.9999: bridges+=f.Area
            else: steep+=f.Area
    assert mesh.isSolid() and all(v==2 for v in edges.values())
    report['parts'][name]={'valid':shape.isValid(),'solids':len(shape.Solids),'watertight':mesh.isSolid(),'bed_contact_mm2':bed,'steep_nonbridge_area_mm2':steep,'bridge_area_mm2':bridges,'print_bounds_mm':[s.optimalBoundingBox().XLength,s.optimalBoundingBox().YLength,s.optimalBoundingBox().ZLength]}
for keyname in ['H2Body','Stock3510','HeaterSock','Nozzle','Heatbreak','MotorConnector','Blower5015','CarriageEnvelope','RodKeepouts','Tray','Cover','AdapterFront','AdapterBack']:
    ob=src.getObject(keyname)
    if ob and hasattr(ob,'Shape'):
        report['collisions_mm3'][keyname]=[a.common(ob.Shape).Volume,b.common(ob.Shape).Volume]
assert all(v<1e-5 for row in report['collisions_mm3'].values() for v in row),report['collisions_mm3']
Part.makeCompound([a,b]).exportStep(os.path.join(OUT,'bracket_assembled.step'))
doc.recompute();App.setActiveDocument(doc.Name)
Gui.activeDocument().activeView().viewAxonometric();Gui.activeDocument().activeView().fitAll()
doc.saveAs(os.path.join(OUT,'H2_5015_PrintableBracket.FCStd'))
json.dump(report,open(os.path.join(OUT,'validation.json'),'w'),indent=2)
print(json.dumps(report,indent=2))
