# /Users/christianbaker/PycharmProjects/pynaneye/src/pynaneye/__init__.py

# This is a workaround for PyCharm's static analysis.
# These symbols are actually provided by the pythonnet binding at runtime.
try:
    from .naneye import Camera, NanEyeSensorType  # noqa
except ImportError:
    # This block will be executed if naneye.py (the actual implementation)
    # is not found, which is expected if it's purely a pythonnet binding.
    pass

# You can optionally add __all__ if you want to control what's imported with `from pynaneye import *`
# __all__ = ['Camera', 'NanEyeSensorType']
