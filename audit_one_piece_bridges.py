"""Run in FreeCAD after verify_one_piece.ps1 to inspect actual lower-duct bridges.

Measures straight extrusion segments tagged as bridges against the solid at the
preceding 0.2 mm layer. Sampling measures CAD support, not deposited infill or
physical PETG sag. The generated G-code is geometry verification only.
"""
import json, math, os, re
from FreeCAD import Vector as V

ROOT=os.path.dirname(os.path.abspath(__file__))
OUT=os.path.join(ROOT,'output','one_piece','slice_checks')
d=App.getDocument('H2_5015_OnePiece') if 'H2_5015_OnePiece' in App.listDocuments() else App.openDocument(os.path.join(ROOT,'output','one_piece','H2_5015_OnePiece.FCStd'))
solid=d.Print_lower_duct.Shape
lines=open(os.path.join(OUT,'lower_duct_verification.gcode')).readlines()
meta=json.loads(next(line[len('; object:'):] for line in lines if line.startswith('; object:')))
offset=[meta['boundingbox_center'][i]-meta['boundingbox_size'][i]/2 for i in [0,1]]
x=y=z=e=0.0
relative_e=False
feature=''
rows=[]
for line in lines:
    if line.startswith(';TYPE:'): feature=line.strip()[6:]
    if line.startswith('M83'): relative_e=True
    if line.startswith('M82'): relative_e=False
    cmd=line.split(';',1)[0].strip()
    values={k:float(v) for k,v in re.findall(r'([XYZE])(-?[0-9.]+)',cmd)}
    if cmd.startswith('G92'):
        e=values.get('E',e)
        continue
    if not re.match(r'G[01]\s',cmd): continue
    nx,ny,nz=values.get('X',x),values.get('Y',y),values.get('Z',z)
    de=values.get('E',0) if relative_e else values.get('E',e)-e
    length=math.hypot(nx-x,ny-y)
    if de>0 and length>1 and 'bridge' in feature.lower():
        n=max(2,math.ceil(length/0.15))
        support=[]
        for i in range(n+1):
            t=i/n
            point=V(x+(nx-x)*t-offset[0],y+(ny-y)*t-offset[1],z-0.25)
            support.append(solid.isInside(point,1e-6,True))
        run=longest=0
        for supported in support:
            run=0 if supported else run+1
            longest=max(longest,run)
        rows.append({'print_z_mm':z,'feature':feature,'path_length_mm':length,
            'max_unsupported_run_mm':min(length,longest*length/n),
            'ends_on_previous_layer':[support[0],support[-1]],
            'start_print_xy_mm':[x-offset[0],y-offset[1]],
            'end_print_xy_mm':[nx-offset[0],ny-offset[1]]})
    x,y,z=nx,ny,nz
    e=e+values.get('E',0) if relative_e else values.get('E',e)

roof=[r for r in rows if 10.6<r['print_z_mm']<11.3 and r['feature']=='Bridge infill']
report={'method':'0.15 mm CAD support sampling 0.05 mm below previous layer top; 0.2 mm layers',
    'physical_print_tested':False,'bridge_segments':len(rows),'manifold_roof_segments':len(roof),
    'roof_layers_print_z_mm':sorted(set(r['print_z_mm'] for r in roof)),
    'max_roof_unsupported_run_mm':max(r['max_unsupported_run_mm'] for r in roof),
    'max_roof_path_length_mm':max(r['path_length_mm'] for r in roof),
    'roof_segments_with_both_ends_on_cad':sum(all(r['ends_on_previous_layer']) for r in roof),
    'longest_roof_runs':sorted(roof,key=lambda r:r['max_unsupported_run_mm'],reverse=True)[:12],
    'all_bridge_segments':rows}
json.dump(report,open(os.path.join(OUT,'lower_duct_bridge_audit.json'),'w'),indent=2)
print(json.dumps({k:v for k,v in report.items() if k not in ['all_bridge_segments','longest_roof_runs']},indent=2))
assert roof and report['max_roof_unsupported_run_mm']<16,'Long manifold bridge remains'
