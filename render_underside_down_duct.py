"""Render the outward-facing, downward-discharge underside revision."""
import os
import runpy

runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'render_underside_duct.py'),
              init_globals={'App': App, 'Gui': Gui, 'UNDERSIDE_VARIANT': 'outward_down'})
