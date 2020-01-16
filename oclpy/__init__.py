# Version control taken from numpy
# We first need to detect if we're being called as part of the ompy setup
# procedure itself in a reliable manner.
try:
    __OCLPY_SETUP__
except NameError:
    __OCLPY_SETUP__ = False

if __OCLPY_SETUP__:
    import sys
    sys.stderr.write('Running from oclpy source directory.\n')
else:
    try:
        from ompy.rebin import *
    except ImportError:
        msg = """Error importing oclpy: you should not try to import oclpy from
        its source directory; please exit the oclpy source tree, and relaunch
        your python interpreter from there."""
        raise ImportError(msg)
    from .version import git_revision as __git_revision__
    from .version import version as __version__
    from .version import full_version as __full_version__


# Simply import all functions and classes from all files to make them available
# at the package level
from .library import div0, fill_negative
from .abstractarray import AbstractArray
from .matrix import Matrix
from .vector import Vector
from .gauss_smoothing import *
from .action import Action
from .introspection import logging, hooks
from .histogram2d import Data2D
from .range import *
from .gate import Gate, GateSector
from .interpolation import Interpolation
from .histogram import Histogram1D, Histogram2D
