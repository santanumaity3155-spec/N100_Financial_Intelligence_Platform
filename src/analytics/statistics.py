"""
src/analytics/statistics.py

Analytics statistics module and standard library compatibility proxy.
"""

import sys
import os
import importlib.util
import importlib.machinery

_current_file = os.path.abspath(__file__)
_current_dir = os.path.dirname(_current_file)

# Proxy standard library statistics to prevent shadowing when third-party packages import `statistics`
_filtered_path = [
    p
    for p in sys.path
    if os.path.abspath(p) not in (_current_dir, os.path.dirname(_current_dir))
]

for _p in _filtered_path:
    try:
        _spec = importlib.machinery.PathFinder.find_spec("statistics", [_p])
        if _spec and _spec.origin and os.path.abspath(_spec.origin) != _current_file:
            _mod = importlib.util.module_from_spec(_spec)
            _spec.loader.exec_module(_mod)
            for _attr in dir(_mod):
                if not _attr.startswith("__"):
                    globals()[_attr] = getattr(_mod, _attr)
            break
    except Exception:
        continue
