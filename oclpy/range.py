"""
Range function

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

import numpy as np
from typing import (Dict, Iterable, Any, Union, Tuple,
                    Sequence, Optional, Iterator, Callable)
from pathlib import Path
from .interpolation import Interpolation
from .filehandling import load_range

class Range(Interpolation):

	def __init__(self,
				 path: Union[str, Path]):

		values, _, E = load_range(path)
		super().__init__(E*1e3, values, kind='cubic', bounds_error=False, fill_value=(0,max(values)))

class RangeTransform:
	def __init__(self,
				 path: Union[str, Path]):
		self.range = Range(path)

	def __call__(self,
				 de,
				 e):
		"""
		Expect the shape (n,2), returns (n,1)
		"""
		return self.range(de+e) - self.range(e)