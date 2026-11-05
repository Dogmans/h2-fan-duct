"""Check support for every continuous extrusion run in the verification G-code.

This is a preceding-toolpath anchor check, not a simulation of sag or adhesion.
Run with ordinary Python after verify_monolithic.ps1. Only absolute XYZ/E
G-code is accepted; the verification profile explicitly emits G90 and M82.
"""
import hashlib, json, math, re
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'output'/'monolithic'/'slice_checks'
target=OUT/'duct_verification.gcode'
lines=target.read_text().splitlines()
layers=defaultdict(list)
x=y=z=e=0.0
feature=''; run=[]
def finish():
    if run:
        layers[round(z,4)].append((feature,list(run)))
        run.clear()

for line in lines:
    if line.startswith(';TYPE:'): feature=line[6:]
    cmd=line.split(';',1)[0].strip()
    assert cmd not in ['G91','M83'],'Only absolute verification G-code is supported'
    values={k:float(v) for k,v in re.findall(r'([XYZE])(-?[0-9.]+)',cmd)}
    if cmd.startswith('G92'):
        e=values.get('E',e)
        continue
    if not re.match(r'G[01]\s',cmd): continue
    nx,ny,nz=values.get('X',x),values.get('Y',y),values.get('Z',z)
    if values.get('E',e)-e>0 and math.hypot(nx-x,ny-y)>.001 and nz==z:
        run.append(((x,y),(nx,ny)))
    else: finish()
    x,y,z=nx,ny,nz; e=values.get('E',e)
finish()

previous=[]; unanchored=[]; checked=0; cell=2.0
for height,runs in sorted(layers.items()):
    grid=defaultdict(list)
    for a,b in previous:
        for ix in range(math.floor(min(a[0],b[0])/cell)-1,math.floor(max(a[0],b[0])/cell)+2):
            for iy in range(math.floor(min(a[1],b[1])/cell)-1,math.floor(max(a[1],b[1])/cell)+2):
                grid[ix,iy].append((a,b))
    if previous:
        for feature,path in runs:
            checked+=1; supported=False
            for a,b in path:
                count=max(1,math.ceil(math.dist(a,b)))
                for i in range(count+1):
                    p=(a[0]+(b[0]-a[0])*i/count,a[1]+(b[1]-a[1])*i/count)
                    for c,d in grid[math.floor(p[0]/cell),math.floor(p[1]/cell)]:
                        dx,dy=d[0]-c[0],d[1]-c[1]; ll=dx*dx+dy*dy
                        t=max(0,min(1,((p[0]-c[0])*dx+(p[1]-c[1])*dy)/ll)) if ll else 0
                        if math.hypot(p[0]-c[0]-t*dx,p[1]-c[1]-t*dy)<.48:
                            supported=True; break
                    if supported: break
                if supported: break
            if not supported:
                unanchored.append({'print_z_mm':height,'feature':feature,
                    'length_mm':sum(math.dist(a,b) for a,b in path)})
    previous=[segment for _,path in runs for segment in path]

report={'method':'continuous extrusion runs sampled at <=1 mm, seeking prior-layer extrusion centerline within 0.48 mm',
    'note':'a nearby anchor does not prove adequate support for the whole path or predict PETG sag',
    'physical_print_tested':False,'layers':len(layers),'runs_checked':checked,
    'unanchored_runs':unanchored,'gcode_sha256':hashlib.sha256(target.read_bytes()).hexdigest()}
(OUT/'toolpath_anchor_audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
assert checked and not unanchored,'Extrusion run lacks a preceding-layer anchor'
