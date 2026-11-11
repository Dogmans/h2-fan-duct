"""Render a cutaway of the elevated duct and geometric jet aim (not CFD)."""
import os, json
import Part
from FreeCAD import Vector as V
ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, 'output', 'underside_down')
P = json.load(open(os.path.join(ROOT, 'underside_down_parameters.json')))
doc = App.listDocuments().get('H2_5015_Underside_Down') or App.openDocument(os.path.join(OUT,'H2_5015_Underside_Down.FCStd'))
App.setActiveDocument(doc.Name)
view = Gui.activeDocument().activeView()
view.stopAnimating(); view.setAnimationEnabled(False)
view.setCameraType('Orthographic')
saved = {o.Name:o.Visibility for o in doc.Objects if hasattr(o,'Visibility')}
for o in doc.Objects:
    if hasattr(o,'Group'): o.Visibility = True
for o in doc.Objects:
    if hasattr(o,'Visibility') and not hasattr(o,'Group'): o.Visibility = False
names = []
def show(name, shape, color, lines=False):
    ob = doc.addObject('Part::Feature',name)
    names.append(ob.Name)
    ob.Shape = shape
    ob.ViewObject.ShapeColor = color
    ob.ViewObject.LineColor = color if lines else (.15,.16,.18)
    ob.ViewObject.LineWidth = 3 if lines else 1.5
    return ob
try:
    # Take a thin section at the jet center so the internal slopes are visible.
    cut = Part.makeBox(52,.1,35,V(-12,1.3,-1))
    show('ReviewDuctSection',doc.Duct.Shape.common(cut),(.95,.46,.12))
    show('ReviewSock',doc.HeaterSock.Shape,(.27,.29,.32))
    show('ReviewNozzle',doc.Nozzle.Shape,(.85,.65,.2))
    for x in [0,28]:
        show('ReviewJetAxis',Part.makeLine(V(x,1.15,P['jet_center_z_mm']),V(14,1.15,P['jet_target_z_mm'])),(.1,.6,.8),True)
    show('ReviewBed',Part.makeLine(V(-16,1.1,0),V(44,1.1,0)),(.3,.33,.36),True)
    show('ReviewClearance',Part.makeLine(V(-14,1.1,0),V(-14,1.1,P['duct_base_z_mm'])),(.2,.6,.4),True)
    for z in [0,P['duct_base_z_mm']]:
        show('ReviewDimensionTick',Part.makeLine(V(-15,1.1,z),V(-13,1.1,z)),(.2,.6,.4),True)
    view.viewFront(); view.fitAll(); Gui.updateGui()
    view.saveImage(os.path.join(OUT,'jet_clearance_section.png'),1600,900,'White')
finally:
    for name in names: doc.removeObject(name)
    for o in doc.Objects:
        if hasattr(o,'Group') and o.Name in saved: o.Visibility = saved[o.Name]
    for o in doc.Objects:
        if not hasattr(o,'Group') and o.Name in saved: o.Visibility = saved[o.Name]
    view.viewAxonometric(); view.fitAll(); doc.recompute()
print('Rendered jet_clearance_section.png: cyan aim lines and green 5 mm dimension')
