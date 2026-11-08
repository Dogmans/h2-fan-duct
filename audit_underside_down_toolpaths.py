"""Check preceding-layer anchors for the support-free underside/down parts.

This samples actual extrusion paths, including bridge endpoints. It cannot
predict PETG sag, adhesion, airflow, or physical fit. Verification G-code is not
printer-ready. Run using ordinary Python after verify_underside_down.ps1.
"""
import hashlib
import json
import math
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT/'output'/'underside_down'/'slice_checks'


def inspect(part):
    target = OUT/(part+'_verification.gcode')
    layers = defaultdict(list)
    x = y = z = e = 0.0
    feature = ''
    run = []

    def finish():
        if run:
            layers[round(z, 4)].append((feature, list(run)))
            run.clear()

    for line in target.read_text().splitlines():
        if line.startswith(';TYPE:'):
            feature = line[6:]
        cmd = line.split(';', 1)[0].strip()
        assert cmd not in ['G91', 'M83'], 'Only absolute verification G-code supported'
        values = {k:float(v) for k,v in re.findall(r'([XYZE])(-?[0-9.]+)', cmd)}
        if cmd.startswith('G92'):
            e = values.get('E', e)
            continue
        if not re.match(r'G[01]\s', cmd):
            continue
        nx, ny, nz = values.get('X',x), values.get('Y',y), values.get('Z',z)
        if values.get('E',e)-e > 0 and math.hypot(nx-x,ny-y) > .001 and nz == z:
            run.append(((x,y),(nx,ny)))
        else:
            finish()
        x,y,z,e = nx,ny,nz,values.get('E',e)
    finish()

    previous = []
    unanchored = []
    checked = 0
    cell = 2.
    bridge_paths = []
    same_layer_anchors = []
    for height,runs in sorted(layers.items()):
        grid = defaultdict(list)
        current_grid = defaultdict(list)

        def add_to_grid(target,segments):
            for a,b in segments:
                for ix in range(math.floor(min(a[0],b[0])/cell)-1, math.floor(max(a[0],b[0])/cell)+2):
                    for iy in range(math.floor(min(a[1],b[1])/cell)-1, math.floor(max(a[1],b[1])/cell)+2):
                        target[ix,iy].append((a,b))

        add_to_grid(grid,previous)

        def supported(p,target=None):
            target = grid if target is None else target
            for c,d in target[math.floor(p[0]/cell),math.floor(p[1]/cell)]:
                dx,dy = d[0]-c[0],d[1]-c[1]
                ll = dx*dx+dy*dy
                t = max(0,min(1,((p[0]-c[0])*dx+(p[1]-c[1])*dy)/ll)) if ll else 0
                if math.hypot(p[0]-c[0]-t*dx,p[1]-c[1]-t*dy) < .48:
                    return True
            return False

        if previous:
            for feature,path in runs:
                checked += 1
                anchor = False
                longest = current = 0.
                for a,b in path:
                    length = math.dist(a,b)
                    count = max(1, math.ceil(length/.2))
                    for i in range(count+1):
                        p = (a[0]+(b[0]-a[0])*i/count,a[1]+(b[1]-a[1])*i/count)
                        ok = supported(p)
                        anchor = anchor or ok
                        current = 0 if ok else current+length/count
                        longest = max(longest,current)
                if not anchor:
                    row = {'print_z_mm':height,'feature':feature,
                           'length_mm':sum(math.dist(a,b) for a,b in path),
                           'start_xy':path[0][0],'end_xy':path[-1][1]}
                    touching_earlier = False
                    for a,b in path:
                        count = max(1,math.ceil(math.dist(a,b)/.2))
                        for i in range(count+1):
                            p = (a[0]+(b[0]-a[0])*i/count,a[1]+(b[1]-a[1])*i/count)
                            if supported(p,current_grid):
                                touching_earlier = True
                                break
                        if touching_earlier:
                            break
                    (same_layer_anchors if touching_earlier else unanchored).append(row)
                if feature == 'Bridge infill':
                    bridge_paths.append({'z_mm':height,'start_xy':path[0][0],'end_xy':path[-1][1],'max_unsupported_run_mm':longest,
                        'ends_anchored':[supported(path[0][0]),supported(path[-1][1])]})
                add_to_grid(current_grid,path)
        previous = [segment for _,path in runs for segment in path]
    return {'part':part,'physical_print_tested':False,'layers':len(layers),
            'runs_checked':checked,'unanchored_runs':unanchored,
            'runs_touching_only_earlier_same_layer_extrusions':same_layer_anchors,
            'bridge_paths':len(bridge_paths),
            'max_bridge_unsupported_run_mm':max((r['max_unsupported_run_mm'] for r in bridge_paths),default=0),
            'bridge_paths_with_both_ends_anchored':sum(all(r['ends_anchored']) for r in bridge_paths),
            'longest_bridge_paths':sorted(bridge_paths,key=lambda r:r['max_unsupported_run_mm'],reverse=True)[:15],
            'stl_sha256':hashlib.sha256((OUT.parent/(part+'_print.stl')).read_bytes()).hexdigest(),
            'gcode_sha256':hashlib.sha256(target.read_bytes()).hexdigest()}


report = {'method':'0.2 mm samples within 0.48 mm of preceding-layer paths, or already printed paths on the same layer; bridge spans use preceding layer only',
          'note':'A nearby anchor does not prove support along an entire path or predict physical printing.',
          'parts':[inspect(name) for name in ['duct','chain_plate','spacer_2mm','spacer_4mm']]}
(OUT/'toolpath_anchor_audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
assert all(r['runs_checked'] and not r['unanchored_runs'] for r in report['parts']), 'Unanchored extrusion run'
assert report['parts'][0]['bridge_paths'], 'No duct bridges detected'
assert report['parts'][0]['max_bridge_unsupported_run_mm'] < 16, 'Long unsupported bridge'
