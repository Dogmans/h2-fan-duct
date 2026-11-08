"""Build the outward-facing, downward-discharge underside revision in FreeCAD."""
import os
import runpy

runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'build_underside_duct.py'),
              init_globals={'App': App, 'Gui': Gui, 'UNDERSIDE_VARIANT': 'outward_down'})
