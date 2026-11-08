"""Hardware envelopes and the retained chain plate for the underside/down duct.

Dimensions follow the manufacturer drawings and carriage/chain SCAD files in
reference/. These are simplified fit references, not manufacturing models.
The blower is returned at the drawing datum before the assembly offset.
"""
import math
import Part
from FreeCAD import Vector as V


def create_references(doc, App):
    refs=doc.addObject('App::DocumentObjectGroup','References')
    refs.Label='REFERENCE ONLY - H2, blower and carriage'
    def box(dx,dy,dz,x,y,z): return Part.makeBox(dx,dy,dz,V(x,y,z))
    def cy(r,h,x,y,z): return Part.makeCylinder(r,h,V(x,y,z),V(0,1,0))
    def cx(r,h,x,y,z): return Part.makeCylinder(r,h,V(x,y,z),V(1,0,0))
    def fuse(parts):
        s=parts[0]
        for p in parts[1:]: s=s.fuse(p)
        return s.removeSplitter()
    def feature(name,label,s,color,group=None,visible=True):
        o=doc.addObject('Part::Feature',name); o.Label=label; o.Shape=s
        if App.GuiUp:
            o.ViewObject.ShapeColor=color; o.ViewObject.LineColor=(0.13,0.16,0.19)
            o.ViewObject.Deviation=0.1
        if group: group.addObject(o)
        o.Visibility=visible
        return o
    def capsule(a,b,r,y,depth):
        ax,az=a; bx,bz=b; l=math.hypot(bx-ax,bz-az); nx,nz=-(bz-az)/l*r,(bx-ax)/l*r
        pts=[V(x,y,z) for x,z in [(ax+nx,az+nz),(bx+nx,bz+nz),(bx-nx,bz-nz),(ax-nx,az-nz)]]
        return fuse([Part.Face(Part.makePolygon(pts+[pts[0]])).extrude(V(0,depth,0)),cy(r,depth,ax,y,az),cy(r,depth,bx,y,bz)])
    # Measured/drawn reference envelopes, not printable components.
    body=box(61.9,35,35,0,-17.5,22.2)
    for z in [32.2,47.2]: body=body.cut(cy(1.5,5,37.4,-18,z))
    o=feature('H2Body','H2 body and motor envelope',body,(0.30,0.32,0.35),refs)
    if App.GuiUp: o.ViewObject.Transparency=65
    stock=box(10,35,35,-14.9,-17.5,22.2).cut(cx(14,12,-15.9,0,39.7))
    feature('Stock3510','KEEP - stock 3510 heatsink cooling fan',stock,(0.23,0.25,0.28),refs)
    heater=box(24,20,12,2,-8.7,9)
    feature('HeaterSock','Heater / sock keepout - approximate',heater,(0.90,0.29,0.09),refs)
    nozzle=fuse([Part.makeCone(0.4,3.5,4.5,V(14,1.3,0)),Part.makeCylinder(3.5,4.5,V(14,1.3,4.5))])
    feature('Nozzle','Nozzle tip datum Z=0',nozzle,(0.87,0.67,0.24),refs)
    feature('Heatbreak','Heatbreak simplified',Part.makeCylinder(3,5,V(14,1.3,21)),(0.7,0.7,0.72),refs)
    connector=box(8,14,6,53.9,-7,16.2)
    feature('MotorConnector','Motor connector keepout - verify actual plug / wires',connector,(0.40,0.41,0.43),refs)
    # Carriage/rod dimensions from reference/croxy_carriage_h2_touch_less_offset.scad.
    crossrod=Part.makeCylinder(4,140,V(-20,29,59.2),V(1,0,0))
    toprod=Part.makeCylinder(4,110,V(50.4,-40,82.2),V(0,1,0))
    topbearing=Part.makeCylinder(11.5,45,V(50.4,-17.5,82.2),V(0,1,0)).cut(toprod)
    backbearing=Part.makeCylinder(11.5,45,V(14.9,29,59.2),V(1,0,0)).cut(crossrod)
    carriage=fuse([topbearing,backbearing])
    o=feature('CarriageEnvelope','Carriage bearing envelopes - verify installed variant',carriage,(0.48,0.51,0.55),refs)
    if App.GuiUp: o.ViewObject.Transparency=80
    o=feature('RodKeepouts','8 mm rods inferred from bearing positions',Part.makeCompound([crossrod,toprod]),(0.67,0.70,0.74),refs,False)

    fc,fz,fx,ft=-3.0,28.0,65.9,15.0
    zc=fz+25.8
    fanholes=[(fc-22.2,zc+21.6),(fc+19.3,zc-17.4)]
    # Standard 5015 silhouette: BeCool 5015-1 dimensioned hole coordinates.
    parts=[cx(24.5,ft,fx,fc,zc),box(ft,19.3,26,fx,fc-27.2,fz)]
    for y,z in fanholes:
        s=capsule((fc+(y-fc)*0.7,zc+(z-zc)*0.7),(y,z),4.3,0,ft)
        s.rotate(V(0,0,0),V(0,0,1),90); s.translate(V(fx+ft,0,0)); parts.append(s)
    blower=fuse(parts).cut(cx(16.25,2,fx+ft-1.9,fc,zc))
    for y,z in fanholes: blower=blower.cut(cx(2.35,ft+2,fx-1,y,z))
    # Retain the current chain plate outline and five SCAD fixing positions.
    chain=fuse([box(10,3,80,32.4,-20.5,26.7),box(17,3,20,28.9,-20.5,97.7),
                box(17,3,10,28.9,-20.5,91.7)])
    side_tab=capsule((37.4,47.2),(59.4,48),5,-20.5,3)
    chain=chain.fuse(side_tab).common(box(14,3,80,28.9,-20.5,26.7)).fuse(
        chain.common(box(17,3,26,28.9,-20.5,91.7))).removeSplitter()
    for x,z in [(37.4,32.2),(37.4,47.2),(40.9,108.7),(33.4,105.2),(33.4,112.2)]:
        chain=chain.cut(cy(1.65,3.2,x,-20.6,z))
    chain=chain.removeSplitter()
    return {'blower':blower,'chain_plate':chain}
