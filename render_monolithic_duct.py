"""Render the continuous duct installed, on its print base and in section."""
import os
import Part
from FreeCAD import Vector as V

ROOT=os.path.dirname(os.path.abspath(__file__))
OUT=os.path.join(ROOT,'output','monolithic')
d=App.getDocument('H2_5015_Monolithic') if 'H2_5015_Monolithic' in App.listDocuments() else App.openDocument(os.path.join(OUT,'H2_5015_Monolithic.FCStd'))
App.setActiveDocument(d.Name)
v=Gui.activeDocument().activeView()
animation_enabled=v.isAnimationEnabled()
section=d.getObject('Cutaway') or d.addObject('Part::Feature','Cutaway')
section.Label='ILLUSTRATION ONLY - front wall removed to show the closed elbow'
section.Shape=d.Duct.Shape.cut(Part.makeBox(140,40,50,V(-30,-63.5,0)))
section.ViewObject.ShapeColor=(0.95,0.46,0.12)
section.Visibility=False
objects=[o for o in d.Objects if hasattr(o,'Visibility')]
visibility={o.Name:o.Visibility for o in objects}

def frame():
    v.stopAnimating(); v.setAnimationEnabled(False)
    Gui.updateGui()
    if d.References.Visibility: d.RodKeepouts.Visibility=False
    d.CombinedBracket.ViewObject.ShapeColor=(0.18,0.48,0.64)
    d.CombinedBracket.Tip.ViewObject.ShapeColor=(0.18,0.48,0.64)
    orientation=App.Rotation(V(1,1,0),V(-1,1,2),V(1,-1,1),'ZXY')
    v.setCameraType('Orthographic'); v.setCameraOrientation(orientation.Q)
    Gui.updateGui(); v.fitAll(); Gui.updateGui()

try:
    d.PrintLayout.Visibility=False; d.Construction.Visibility=False
    d.References.Visibility=True; d.CombinedBracket.Visibility=True
    d.PrintedDuct.Visibility=True; d.Duct.Visibility=True
    d.MountHardware.Visibility=True; section.Visibility=False
    frame(); v.saveImage(os.path.join(OUT,'assembled.png'),1600,1200,'White')

    d.References.Visibility=False; d.CombinedBracket.Visibility=False
    d.MountHardware.Visibility=False; d.PrintedDuct.Visibility=False
    d.PrintLayout.Visibility=True; d.Print_duct.Visibility=True
    d.Print_duct.ViewObject.ShapeColor=(0.95,0.46,0.12)
    frame(); v.saveImage(os.path.join(OUT,'print_orientation.png'),1600,1000,'White')

    d.PrintLayout.Visibility=False; section.Visibility=True
    frame(); v.saveImage(os.path.join(OUT,'cutaway.png'),1600,1000,'White')
finally:
    for o in objects: o.Visibility=visibility[o.Name]
    d.recompute(); frame(); d.save(); v.setAnimationEnabled(animation_enabled)
print('Saved installed, upright print orientation and illustrative cutaway views')
