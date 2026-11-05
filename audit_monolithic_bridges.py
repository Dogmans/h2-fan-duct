"""Run in FreeCAD after verify_monolithic.ps1 to inspect actual manifold and elbow bridges.

Measures straight extrusion segments tagged as bridges against the solid at the
preceding 0.2 mm layer. Sampling measures CAD support, not deposited infill or
physical PETG sag. The generated G-code is geometry verification only.
"""
import hashlib, json, math, os, re
from FreeCAD import Vector as V

ROOT=os.path.dirname(os.path.abspath(__file__))
OUT=os.path.join(ROOT,'output','monolithic','slice_checks')
d=App.getDocument('H2_5015_Monolithic') if 'H2_5015_Monolithic' in App.listDocuments() else App.openDocument(os.path.join(ROOT,'output','monolithic','H2_5015_Monolithic.FCStd'))
solid=d.Print_duct.Shape
validation=json.load(open(os.path.join(ROOT,'output','monolithic','validation.json')))
base=validation['parts']['duct']['bounds'][4]
roof_z=validation['inlet_center_z_mm']+validation['manifold_channel_mm'][1]/2
roof_layers=[round(roof_z-base+0.2-validation['side_arm_roof_step_mm'],6),round(roof_z-base+0.2,6)]
slices={}
def cad_support(x,y,height):
    # Cache planar sections instead of repeatedly classifying the entire BREP.
    # Even-odd polygon inclusion handles both material islands and air holes.
    if height<0: return True  # The first layer is supported by the print bed.
    key=round(height,6)
    if key not in slices:
        slices[key]=[[(p.x,p.y) for p in w.discretize(Deflection=0.02)]
                     for w in solid.slice(V(0,0,1),key)]
    inside=False
    for polygon in slices[key]:
        for a,b in zip(polygon,polygon[1:]+polygon[:1]):
            if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:
                inside=not inside
    return inside
lines=open(os.path.join(OUT,'duct_verification.gcode')).readlines()
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
    in_adapter=min(x-offset[0],nx-offset[0])>78.85
    if de>0 and length>1 and ('bridge' in feature.lower() or feature=='Overhang perimeter'
                            or (in_adapter and feature in ['Perimeter','External perimeter'])):
        n=max(2,math.ceil(length/0.15))
        support=[]
        for i in range(n+1):
            t=i/n
            support.append(cad_support(x+(nx-x)*t-offset[0],y+(ny-y)*t-offset[1],z-0.25))
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

roof=[r for r in rows if any(abs(r['print_z_mm']-h)<1e-5 for h in roof_layers) and r['feature']=='Bridge infill']
adapter=[r for r in rows if min(r['start_print_xy_mm'][0],r['end_print_xy_mm'][0])>78.85
         and r['feature'] in ['Bridge infill','Overhang perimeter','Perimeter','External perimeter']]
bridge_rows=[r for r in rows if 'bridge' in r['feature'].lower() or r['feature']=='Overhang perimeter']
report={'method':'0.15 mm samples on CAD sections discretized to 0.02 mm; 0.05 mm below previous layer top; 0.2 mm layers; first layer supported by bed',
    'physical_print_tested':False,'analysed_extrusion_segments':len(rows),
    'bridge_segments':len(bridge_rows),'manifold_roof_segments':len(roof),
    'roof_layers_print_z_mm':sorted(set(r['print_z_mm'] for r in roof)),
    'max_roof_unsupported_run_mm':max(r['max_unsupported_run_mm'] for r in roof),
    'max_roof_path_length_mm':max(r['path_length_mm'] for r in roof),
    'roof_segments_with_both_ends_on_cad':sum(all(r['ends_on_previous_layer']) for r in roof),
    'longest_roof_runs':sorted(roof,key=lambda r:r['max_unsupported_run_mm'],reverse=True)[:12],
    'all_bridge_segments':bridge_rows}
report['adapter_perimeter_and_bridge_segments']=len(adapter)
report['max_adapter_unsupported_run_mm']=max((r['max_unsupported_run_mm'] for r in adapter),default=0)
report['adapter_segments_with_both_ends_on_cad']=sum(all(r['ends_on_previous_layer']) for r in adapter)
report['longest_adapter_runs']=sorted(adapter,key=lambda r:r['max_unsupported_run_mm'],reverse=True)[:12]
report['source_sha256']={name:hashlib.sha256(open(os.path.join(ROOT,'output','monolithic',name),'rb').read()).hexdigest()
                         for name in ['duct_print.stl','slice_checks/duct_verification.gcode']}
# Independently confirm all roof anchors against the exact BREP, without the
# section-polyline approximation used for the much denser span sampling.
endpoints=[solid.isInside(V(p[0],p[1],r['print_z_mm']-0.25),1e-6,True)
           for r in roof for p in [r['start_print_xy_mm'],r['end_print_xy_mm']]]
report['exact_brep_roof_endpoints']={'checked':len(endpoints),'supported':sum(endpoints)}
json.dump(report,open(os.path.join(OUT,'duct_bridge_audit.json'),'w'),indent=2)
print(json.dumps({k:v for k,v in report.items() if k not in ['all_bridge_segments','longest_roof_runs','longest_adapter_runs']},indent=2))
assert roof and report['max_roof_unsupported_run_mm']<16,'Long manifold bridge remains'
assert all(endpoints),'Roof bridge endpoint lacks previous-layer CAD support'
assert adapter and report['max_adapter_unsupported_run_mm']<16,'Long unsupported elbow span'
