"""Save assembly, exploded and bed-orientation views through FreeCAD MCP."""
import os
from FreeCAD import Vector as V

ROOT=os.path.dirname(os.path.abspath(__file__))
OUT=os.path.join(ROOT,'output','one_piece')
d=App.getDocument('H2_5015_OnePiece') if 'H2_5015_OnePiece' in App.listDocuments() else App.openDocument(os.path.join(OUT,'H2_5015_OnePiece.FCStd'))
App.setActiveDocument(d.Name)
v=Gui.activeDocument().activeView()
objects=[o for o in d.Objects if hasattr(o,'Visibility')]
visibility={o.Name:o.Visibility for o in objects}
placements={o.Name:App.Placement(o.Placement) for o in objects if hasattr(o,'Placement')}
def frame():
    # Set the camera directly so screenshots cannot catch a view animation.
    Gui.updateGui()
    if d.References.Visibility:
        d.RodKeepouts.Visibility=False
    d.CombinedBracket.ViewObject.ShapeColor=(0.18,0.48,0.64)
    d.CombinedBracket.Tip.ViewObject.ShapeColor=(0.18,0.48,0.64)
    orientation=App.Rotation(V(1,1,0),V(-1,1,2),V(1,-1,1),'ZXY')
    v.setCameraType('Orthographic')
    v.setCameraOrientation(orientation.Q)
    Gui.updateGui(); v.fitAll(); Gui.updateGui()
try:
    d.PrintLayout.Visibility=False
    d.Construction.Visibility=False
    d.References.Visibility=True
    d.CombinedBracket.Visibility=True
    d.PrintedDuct.Visibility=True
    d.JointHardware.Visibility=True
    frame()
    v.saveImage(os.path.join(OUT,'assembled.png'),1600,1200,'White')

    d.References.Visibility=False
    d.CombinedBracket.Visibility=False
    for name,offset in [('AdapterFront',-16),('AdapterBack',16),
                        ('JointNut1',-16),('JointNut2',-16),
                        ('JointBolt1',16),('JointBolt2',16)]:
        d.getObject(name).Placement.Base+=V(0,offset,0)
    d.recompute(); frame()
    v.saveImage(os.path.join(OUT,'exploded.png'),1600,1000,'White')

    d.PrintedDuct.Visibility=False
    d.JointHardware.Visibility=False
    d.PrintLayout.Visibility=True
    for name,x in [('Print_lower_duct',0),('Print_adapter_front',90),('Print_adapter_back',130)]:
        o=d.getObject(name)
        o.Visibility=True
        o.ViewObject.ShapeColor=(0.95,0.46,0.12)
        o.Placement.Base+=V(x,0,0)
    d.recompute(); frame()
    v.saveImage(os.path.join(OUT,'print_layout.png'),1800,900,'White')
finally:
    for name,placement in placements.items(): d.getObject(name).Placement=placement
    for o in objects: o.Visibility=visibility[o.Name]
    d.recompute(); frame()
    d.save()
print('Saved installed assembly, exploded joint and three-part print layout')
