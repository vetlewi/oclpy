"""
Two dimintional histogram

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

from __future__ import annotations
import logging
import copy
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib import ticker
from pathlib import Path
from matplotlib.colors import LogNorm, Normalize
from typing import (Dict, Iterable, Any, Union, Tuple,
                    Sequence, Optional, Iterator, Callable)
from .abstractarray import AbstractArray
from .matrix import Matrix
from .vector import Vector


LOG = logging.getLogger(__name__)
logging.captureWarnings(True)

class Data2D(AbstractArray):
    """Stores 2D histograms.
    It is constructed from a pandas dataframe with two columns, Ex and Eg.
    """

    def __init__(self,
        x : np.ndarray,
        y : np.ndarray,
        xcal : Optional[np.poly1d] = None,
        ycal : Optional[np.poly1d] = None):
        """
        Initialize the histogram from a dataframe. The dataframe should have two columns
        and are expected to have titles x and y. Both axis can be calibrated sepratly.

        Args:
            data - Tuple with raw correlated events for x-axis and y-axis.
            xcal - Optional, calibration polynomial for x-axis
            ycal - Optional, calibration polynomial for y-axis
        """

        # If tuple of two arrays:
        if x.ndim != 1 or y.ndim != 1:
            raise ValueError(f"Expected arrays with dimintionality 1, got (x.ndim,y.ndim)={x.ndim,y.ndim}")
        if x.shape != y.shape:
            raise ValueError(f"Expected arrays with same length, got (len(x),len(y))={len(x),len(y)}")
        self.raw = np.array([x,y]).T
        self.size = len(x)

        if xcal is None:
            self.xcal = np.poly1d([1,0])
        else:
            self.xcal = xcal
        if ycal is None:
            self.ycal = np.poly1d([1,0])
        else:
            self.ycal = ycal

        self.cal = self.Calibrate()

    def Calibrate(self) -> np.ndarray:
        """
        Calibrates both axis and return array
        """
        return np.array([self.xcal(self.raw[:,0]), self.ycal(self.raw[:,1])]).T

    def SetCalX(self, xcal : np.poly1d) -> None:
        """
        Set calibration for xaxis
        """
        self.xcal = xcal
        self.cal[:,0] = self.xcal(self.raw[:,0])
    def SetCalY(self, ycal : np.poly1d) -> None:
        """
        Set calibration for yaxis
        """
        self.ycal = ycal
        self.cal[:,1] = self.ycal(self.raw[:,1])

    def __len__(self):
        return len(self.raw)

    def __getitem__(self, key):
        return self.cal[key]

    def Tranform1D(self,
                   Transformation : Callable[[np.ndarray], Tuple[np.ndarray,np.ndarray]]) -> Vector:
        """
        Takes a function that takes an array with shape (n,2) and returns a tuple of two (n,1) arrays.
        """
        E, values = Transformation(self.cal)
        return Vector(values=values, E=E)


    def Matrix(self,
               bins : Optional[int] = 100,
               xrange : Optional[Tuple[float,float]] = None,
               yrange : Optional[Tuple[float,float]] = None) -> Matrix:
        """
        Plot as a 2D histogram.
        """

        # Use the Histogram2D to get bins and stuff
        if xrange is not None and yrange is not None:
            counts, xedges, yedges = np.histogram2d(self.cal[:,1], self.cal[:,0], bins=bins, range=[[xrange[0],xrange[1]],[yrange[0],yrange[1]]])
            return Matrix(values=counts,
                          Eg=np.array([0.5*(xedges[i+1]+xedges[i]) for i in range(len(xedges)-1)]),
                          Ex=np.array([0.5*(yedges[i+1]+yedges[i]) for i in range(len(yedges)-1)]))