"""
Gate class

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
import pandas as pd
from typing import (Dict, Iterable, Any, Union, Tuple,
                    Sequence, Optional, Iterator, Callable)
from .interpolation import Interpolation


class Gate(object):
    """
    A class that stores several gates
    """

    def __init__(self,
                 dataframe : pd.DataFrame,
                 default : bool = True):
        """
        Setup the gates.
        ---
        Args:
            dataframe: A pandas dataframe with parameters for each gate.
        """

        self.df = dataframe
        self.gates_low = {}
        self.gates_high = {}

        self.Default_return = default

        for quad in self.df['quad'].unique():
            for ring in self.df['ring'].unique():
                for kind in self.df['kind'].unique():
                    df_qr = self.df.loc[(self.df.quad == quad) & (self.df.ring == ring) & (self.df.kind == kind)]
                    df_qr_low = df_qr.loc[df_qr['lim'] == 'min']
                    df_qr_max = df_qr.loc[df_qr['lim'] == 'max']
                
                    if df_qr_low['x'].count() > 0:
                        self.gates_low[(quad,ring,kind)] = Interpolation(df_qr_low['x'], df_qr_low['y'], kind='cubic', bounds_error=False, fill_value=(max(df_qr_low['y']), min(df_qr_low['y'])))
                
                    if df_qr_max['x'].count() > 0:
                        self.gates_high[(quad,ring,kind)] = Interpolation(df_qr_max['x'], df_qr_max['y'], kind='cubic', bounds_error=False, fill_value=(max(df_qr_max['y']), min(df_qr_max['y'])))

    def defaultMax(self, x):
        """
        Function returning the default result.
        """
        if isinstance(x, np.ndarray):
            return np.full(x.shape, 1e99 if self.Default_return else 0)
        else:
            return 1e99 if self.Default_return else 0

    def defaultMin(self, x):
        if isinstance(x, np.ndarray):
            return np.full(x.shape, 0 if self.Default_return else 1e99)
        else:
            return 0 if self.Default_return else 1e99


    def __call__(self, x, y, quad, ring, kind):
        """
        Searches up the (quad,ring) comibination and check if x,y is within
        """
        max_gate = self.gates_high.get((quad,ring,kind), self.defaultMax)
        min_gate = self.gates_low.get((quad,ring,kind), self.defaultMin)
        return np.logical_and(y < max_gate(x), y > min_gate(x))

class ActGate(object):

    def __init__(self,
                 Max : Interpolation = None,
                 Min : Interpolation = None,
                 Default : bool = True):
        self.max = Max
        self.min = Min
        self.default = Default

    def __call__(self, x, y):
        if self.max is None or self.min is None:
            if isinstance(x, np.ndarray):
                return np.full(x.shape, self.default)
        else:
            return np.logical_and(y < self.max(x), y > self.min(x))



class GateSector(object):

    def __init__(self,
                 dataframe : pd.DataFrame,
                 default : bool = True):
        """
        Setup the gates.
        ---
        Args:
            dataframe: A pandas dataframe with parameters for each gate.
        """

        self.df = dataframe
        self.gates = {}

        self.Default_return = default
        self.default_gate = ActGate(Default=self.Default_return)

        for kind in self.df['kind'].unique():
            df_qr = self.df.loc[self.df.kind == kind]
            df_qr_low = df_qr.loc[df_qr['lim'] == 'min']
            df_qr_max = df_qr.loc[df_qr['lim'] == 'max']
                
            if df_qr_low['x'].count() > 0 and df_qr_max['x'].count():
                self.gates[kind] = ActGate(Interpolation(df_qr_max['x'], df_qr_max['y'], kind='cubic', bounds_error=False, fill_value=(max(df_qr_max['y']), min(df_qr_max['y']))),
                                           Interpolation(df_qr_low['x'], df_qr_low['y'], kind='cubic', bounds_error=False, fill_value=(max(df_qr_low['y']), min(df_qr_low['y']))))
            else:
                self.gates[kind] = ActGate(Default=self.Default_return)

    def __call__(self, x, y, kind):
        """
        Searches up the (quad,ring) comibination and check if x,y is within
        """
        return self.gates.get(kind, self.default_gate)(x, y)
