"""Render the compact assembly, intake gap, O channels and print orientations."""
import os
import Part
from pivy import coin  # Load the camera wrapper used to frame the below view.
from FreeCAD import Vector as V

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT,'output',('underside_down'))
NAME = ('H2_5015_Underside_Down')
doc = App.listDocuments().get(NAME) or App.openDocument(os.path.join(OUT,NAME+'.FCStd'))
App.setActiveDocument(doc.Name)
view = Gui.activeDocument().activeView()
view.stopAnimating()
view.setAnimationEnabled(False)
view.setCameraType('Orthographic')


def hide_all():
    # Group visibility propagates to children: enable groups before hiding leaves.
    for ob in doc.Objects:
        if hasattr(ob,'Group'):
            ob.Visibility = True
    for ob in doc.Objects:
        if hasattr(ob,'Visibility') and not hasattr(ob,'Group'):
            ob.Visibility = False


def show_group(group):
    group.Visibility = True
    for ob in group.Group:
        ob.Visibility = True


def save(name, orientation=None):
    if orientation:
        view.setCameraOrientation(orientation.Q)
    Gui.updateGui()
    view.fitAll()
    if name == 'readme_below':
        camera = view.getCameraNode()
        camera.height.setValue(camera.height.getValue()*1.45)
    Gui.updateGui()
    view.saveImage(os.path.join(OUT,name+'.png'),1600,1200,'White')


def installed():
    hide_all()
    show_group(doc.References)
    show_group(doc.PrintedParts)
    show_group(doc.Hardware)


installed()
angle = App.Rotation(V(1,1,0),V(-1,1,2),V(1,-1,1),'ZXY')
save('assembled',angle)

view.viewBottom()
save('underside')

# Review the outward intake and motor gap with the body translucent.
save('intake_gap',App.Rotation(V(-1,1,0),V(-1,-1,2),V(1,1,1),'ZXY'))

hide_all()
doc.Duct.Visibility = True
view.viewTop()
save('duct_top')
view.viewBottom()
save('duct_bottom')
view.viewAxonometric()
save('duct')

hide_all()
doc.CompleteAir.Visibility = True
view.viewTop()
save('air_path')

for name in ((['duct','fan_bracket','chain_plate','spacer_2mm','spacer_4mm'])):
    hide_all()
    doc.getObject('Print_'+name).Visibility = True
    view.viewAxonometric()
    save(name+'_print_orientation')

hide_all()
doc.UndersideBracket.Visibility = True
doc.HeightSpacer1.Visibility = True
doc.HeightSpacer2.Visibility = True
save('rear_nut_access', App.Rotation(V(0,-1,0),V(1,0,2),V(-2,0,1),'ZXY'))
installed()
saved = {}
for name in ['Duct','Blower5015','Hardware_fan_1','Hardware_fan_2']:
    ob = doc.getObject(name)
    saved[name] = ob.Placement
    placement = ob.Placement
    placement.Base += V(0,0,4)
    ob.Placement = placement
for name in ['HeightSpacer1','HeightSpacer2','Hardware_duct_1','Hardware_duct_2']:
    doc.getObject(name).Visibility = False
# Use the correctly shortened screws in the raised review view.
temporary = []
for y in [-7,9.6]:
    shank = Part.makeCylinder(1.5,8,V(44.4,y,14.2))
    head = Part.makeCylinder(2.85,1.65,V(44.4,y,12.55))
    washer = Part.makeCylinder(3.5,2,V(44.4,y,14.2)).cut(Part.makeCylinder(1.6,2,V(44.4,y,14.2)))
    ob = doc.addObject('Part::Feature','RaisedReviewScrew')
    ob.Shape = shank.fuse(head).fuse(washer)
    ob.ViewObject.ShapeColor = (.65,.67,.7)
    temporary.append(ob.Name)
save('raised_4mm', angle)
for name, placement in saved.items():
    doc.getObject(name).Placement = placement
for name in temporary:
    doc.removeObject(name)
# Public README views omit printer-specific chain/carriage/rod references.
def readme_components():
    hide_all()
    for name in ['H2Body','Stock3510','HeaterSock','Nozzle','Heatbreak',
                 'Blower5015','Duct','UndersideBracket','HeightSpacer1','HeightSpacer2',
                 'Hardware_h2_1','Hardware_h2_2','Hardware_fan_1','Hardware_fan_2',
                 'Hardware_duct_1','Hardware_duct_2']:
        doc.getObject(name).Visibility = True

readme_components()
save('readme_assembled', angle)
save('readme_below', App.Rotation(V(1,1,0),V(1,-1,2),V(1,-1,-1),'ZXY'))
installed()
save('assembled',angle)
doc.save()
print('Rendered installed, underside, intake, air path and print orientation views')
