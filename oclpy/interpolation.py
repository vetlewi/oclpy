"""
Interpolation class

---

This file is part of the oclpy - a library for nuclear physics at the University of Oslo

Copyright (C) 2020 Vetle Wegner Ingeberg
Oslo Cyclotron Laboratory
vetlewi@fys.uio.no

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
import pandas as pd
import numpy as np
from scipy.interpolate import interp1d
from pathlib import Path
from typing import (Dict, Iterable, Any, Union, Tuple,
                    Sequence, Optional, Iterator, Callable)

class Interpolation(object):
    """Encapsulates the scipy interpolation function.

    """

    def __init__(self,
                 x : Optional[Iterable[float]] = None,
                 y : Optional[Iterable[float]] = None,
                 frame : Optional[pd.DataFrame] = None,
                 **kwargs):
        """
        Initialize the interpolation with x and y values.
        """
        if frame is None:
            if x is None or y is None:
                raise ValueError("Provied at least two arrays")
            self.x = x
            self.y = y
        else:

            if x is not None or y is not None:
                raise ValueError("Provide either two arrays or a path")
            self.x = frame['x']
            self.y = frame['y']
        self.interp = interp1d(self.x, self.y, **kwargs)

    def __call__(self, arg):
        return self.interp(arg)

