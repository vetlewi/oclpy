# -*- coding: utf-8 -*-
"""
Library of utility classes and functions for the Oslo method.

---

This file is part of oslo_method_python, a python implementation of the
Oslo method.

Copyright (C) 2018 Jørgen Eriksson Midtbø
Oslo Cyclotron Laboratory
jorgenem [0] gmail.com

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
from scipy.interpolate import interp1d, RectBivariateSpline
import matplotlib
from itertools import product
from typing import Optional, Tuple, Iterator, Any
import inspect
import re
import multiprocessing

def div0(a, b):
    """ division function designed to ignore / 0, i.e. div0([-1, 0, 1], 0 ) -> [0, 0, 0] """
    # Check whether a or b (or both) are numpy arrays. If not, we don't
    # use the fancy function.
    if isinstance(a, np.ndarray) or isinstance(b, np.ndarray):
        with np.errstate(divide='ignore', invalid='ignore'):
            c = np.true_divide(a, b )
            c[ ~ np.isfinite(c )] = 0  # -inf inf NaN
    else:
        if b == 0:
            c = 0
        else:
            c = a / b
    return c


def i_from_E(E, E_array):
    # Returns index of the E_array value closest to given E
    assert(E_array.ndim == 1), "E_array has more then one dimension"
    return np.argmin(np.abs(E_array - E))


def line(x, points):
    """ Returns a line through coordinates [x1,y1,x2,y2]=points
    """
    a = (points[3]-points[1])/float(points[2]-points[0])
    b = points[1] - a*points[0]
    return a*x + b


def make_mask(Ex_array, Eg_array, Ex1, Eg1, Ex2, Eg2):
    # Make masking array to cut away noise below Eg=Ex+dEg diagonal
    # Define cut   x1    y1    x2    y2
    cut_points = [i_from_E(Eg1, Eg_array), i_from_E(Ex1, Ex_array),
                  i_from_E(Eg2, Eg_array), i_from_E(Ex2, Ex_array)]
    i_array = np.linspace(0,len(Ex_array)-1,len(Ex_array)).astype(int) # Ex axis
    j_array = np.linspace(0,len(Eg_array)-1,len(Eg_array)).astype(int) # Eg axis
    i_mesh, j_mesh = np.meshgrid(i_array, j_array, indexing='ij')
    return np.where(i_mesh > line(j_mesh, cut_points), 1, 0)


def E_array_from_calibration(a0: float, a1: float, *,
                             N: Optional[int] = None,
                             E_max: Optional[float] = None) -> np.ndarray:
    """
    Return an array of mid-bin energy values corresponding to the
    specified calibration.

    Args:
        a0, a1: Calibration coefficients; E = a0 + a1*i
        either
            N: Number of bins
        or
            E_max: Max energy. Array is constructed to ensure last bin
                 covers E_max. In other words,
                 E_array[-1] >= E_max - a1
    Returns:
        E: Array of mid-bin energy values
    """
    if E_max is not None and N is not None:
        raise ValueError("Cannot give both N and E_max -- must choose one")

    if N is not None:
        return np.linspace(a0, a0+a1*(N-1), N)
    elif E_max is not None:
        N = int(np.round((E_max - a0)/a1)) + 1
        return np.linspace(a0, a0+a1*(N-1), N)
    else:
        raise ValueError("Either N or E_max must be given")


def fill_negative(matrix, window_size: int):
    """
    Fill negative channels with positive counts from neighbouring channels

    The MAMA routine for this is very complicated. It seems to basically
    use a sliding window along the Eg axis, given by the FWHM, to look for
    neighbouring bins with lots of counts and then take some counts from there.
    Can we do something similar in an easy way?
    """
    matrix_out = np.copy(matrix)
    # Loop over rows:
    for i_Ex in range(matrix.shape[0]):
        for i_Eg in np.where(matrix[i_Ex, :] < 0)[0]:
            # print("i_Ex = ", i_Ex, "i_Eg =", i_Eg)
            # window_size = 4  # Start with a constant window size.
            # TODO relate it to FWHM by energy arrays
            i_Eg_low = max(0, i_Eg - window_size)
            i_Eg_high = min(matrix.shape[1], i_Eg + window_size)
            # Fill from the channel with the larges positive count
            # in the neighbourhood
            i_max = np.argmax(matrix[i_Ex, i_Eg_low:i_Eg_high])
            # print("i_max =", i_max)
            if matrix[i_Ex, i_max] <= 0:
                pass
            else:
                positive = matrix[i_Ex, i_max]
                negative = matrix[i_Ex, i_Eg]
                fill = min(0, positive + negative)  # Don't fill more than to 0
                rest = positive
                # print("fill =", fill, "rest =", rest)
                matrix_out[i_Ex, i_Eg] = fill
                # matrix_out[i_Ex, i_max] = rest
    return matrix_out


def cut_diagonal(matrix, Ex_array, Eg_array, E1, E2):
        """
        Cut away counts to the right of a diagonal line defined by indices

        Args:
            matrix (np.ndarray): The matrix of counts
            Ex_array: Energy calibration along Ex
            Eg_array: Energy calibration along Eg
            E1 (list of two floats): First point of intercept, ordered as Ex,Eg
            E2 (list of two floats): Second point of intercept
        Returns:
            The matrix with counts above diagonal removed
        """
        Ex1, Eg1 = E1
        Ex2, Eg2 = E2
        mask = make_mask(Ex_array, Eg_array, Ex1, Eg1, Ex2, Eg2)
        matrix_out = np.where(mask, matrix, 0)
        return matrix_out


def interpolate_matrix_1D(matrix_in, E_array_in, E_array_out, axis=1):
    """ Does a one-dimensional interpolation of the given matrix_in along axis
    """
    if axis not in [0, 1]:
        raise IndexError("Axis out of bounds. Must be 0 or 1.")
    if not (matrix_in.shape[axis] == len(E_array_in)):
        raise Exception("Shape mismatch between matrix_in and E_array_in")

    if axis == 1:
        N_otherax = matrix_in.shape[0]
        matrix_out = np.zeros((N_otherax, len(E_array_out)))
        f = interp1d(E_array_in, matrix_in, axis=1,
                     kind="linear",
                     bounds_error=False, fill_value=0)
        matrix_out = f(E_array_out)
    elif axis == 0:
        N_otherax = matrix_in.shape[1]
        matrix_out = np.zeros((N_otherax, len(E_array_out)))
        f = interp1d(E_array_in, matrix_in, axis=0,
                     kind="linear",
                     bounds_error=False, fill_value=0)
        matrix_out = f(E_array_out)
    else:
        raise IndexError("Axis out of bounds. Must be 0 or 1.")

    return matrix_out


def interpolate_matrix_2D(matrix_in, E0_array_in, E1_array_in,
                          E0_array_out, E1_array_out):
    """Does a two-dimensional interpolation of the given matrix to the _out
    axes
    """
    if not (matrix_in.shape[0] == len(E0_array_in)
            and matrix_in.shape[1] == len(E1_array_in)):
        raise Exception("Shape mismatch between matrix_in and energy arrays")

    # Do the interpolation using splines of degree 1 (linear):
    f = RectBivariateSpline(E0_array_in, E1_array_in, matrix_in,
                            kx=1, ky=1)
    matrix_out = f(E0_array_out, E1_array_out)

    # Make a rectangular mask to set values outside original bounds to zero
    mask = np.ones(matrix_out.shape, dtype=bool)
    mask[E0_array_out <= E0_array_in[0], :] = 0
    mask[E0_array_out >= E0_array_in[-1], :] = 0
    mask[:, E1_array_out <= E1_array_in[0]] = 0
    mask[:, E1_array_out >= E1_array_in[-1]] = 0
    matrix_out = np.where(mask,
                          matrix_out,
                          0
                          )

    return matrix_out


def log_interp1d(xx, yy, **kwargs):
    """ Interpolate a 1-D function.logarithmically """
    logy = np.log(yy)
    lin_interp = interp1d(xx, logy, kind='linear', **kwargs)
    log_interp = lambda zz: np.exp(lin_interp(zz))  # noqa
    return log_interp


def call_model(fun,pars,pars_req):
    """ Call `fun` and check if all required parameters are provided """

    # Check if required parameters are a subset of all pars given
    if pars_req <= set(pars):
        pcall = {p: pars[p] for p in pars_req}
        return fun(**pcall)
    else:
        raise TypeError("Error: Need following arguments for this method:"
                        " {0}".format(pars_req))


def annotate_heatmap(im, matrix, valfmt="{x:.2f}",
                     textcolors=["black", "white"],
                     threshold=None, **textkw):
    """
    A function to annotate a heatmap.
    Parameters
    ----------
    im
        The AxesImage to be labeled.
    data
        Data used to annotate.  If None, the image's data is used.  Optional.
    valfmt
        The format of the annotations inside the heatmap.  This should either
        use the string format method, e.g. "$ {x:.2f}", or be a
        `matplotlib.ticker.Formatter`.  Optional.
    textcolors
        A list or array of two color specifications.  The first is used for
        values below a threshold, the second for those above.  Optional.
    threshold
        Value in data units according to which the colors from textcolors are
        applied.  If None (the default) uses the middle of the colormap as
        separation.  Optional.
    **kwargs
        All other arguments are forwarded to each call to `text` used to create
        the text labels.
    """

    # Normalize the threshold to the images color range.
    if threshold is not None:
        threshold = im.norm(threshold)
    else:
        threshold = im.norm(matrix.values.max())/2.

    # Set default alignment to center, but allow it to be
    # overwritten by textkw.
    kw = dict(horizontalalignment="center",
              verticalalignment="center")
    kw.update(textkw)

    # Get the formatter in case a string is supplied
    if isinstance(valfmt, str):
        valfmt = matplotlib.ticker.StrMethodFormatter(valfmt)

    # Loop over the data and create a `Text` for each "pixel".
    # Change the text's color depending on the data.
    texts = []
    for j, i in product(*map(range, matrix.shape)):
        x = matrix.Eg[i]
        y = matrix.Ex[j]
        kw.update(color=textcolors[int(im.norm(matrix.values[i, j]) > threshold)])
        text = im.axes.text(y, x, valfmt(matrix.values[i, j], None), **kw)
        texts.append(text)

    return texts

def parallelize_dataframe(df, func, n_cores=multiprocessing.cpu_count()):
    """
    A helper function to parallelizing functions applied to dataframes.
    Parameters
    ----------
        df: Dataframe that the function is applied on
        func: Function applied to the dataframe
        n_cores: Number of processes used
    """

    df_split = np.array_split(df, n_cores)
    pool = multiprocessing.Pool(n_cores)
    df = pd.concat(pool.map(func, df_split))
    pool.close()
    pool.join()
    return df


def diagonal_elements(matrix: np.ndarray) -> Iterator[Tuple[int, int]]:
    """ Iterates over the last non-zero elements

    Args:
        mat: The matrix to iterate over
    Yields:
        Indicies (i, j) over the last non-zero (=diagonal)
        elements.
    """
    Ny = matrix.shape[1]
    for i, row in enumerate(matrix):
        for j, col in enumerate(reversed(row)):
            if col != 0.0:
                yield i, Ny-j
                break


def self_if_none(instance: Any, variable: Any, nonable: bool = False) -> Any:
    """ Sets `variable` from instance if variable is None.

    Note: Has to be imported as in the normalizer class due to class stack
          name retrieval

    Args:
        instance: instance
        variable: The variable to check
        nonable: Does not raise ValueError if
            variable is None.
    Returns:
        The value of variable or instance.variable
    Raises:
        ValueError if both variable and
        self.variable are None.
    """
    name = _retrieve_name(variable)
    if variable is None:
        self_variable = getattr(instance, name)
        if not nonable and self_variable is None:
            raise ValueError(f"`{name}` must be set")
        return self_variable
    return variable


def _retrieve_name(var: Any) -> str:
    """ Finds the source-code name of `var`

        NOTE: Only call from self.reset.

     Args:
        var: The variable to retrieve the name of.
    Returns:
        The variable's name.
    """
    # Retrieve the line of the source code of the third frame.
    # The 0th frame is the current function, the 1st frame is the
    # calling function and the second is the calling function's caller.
    line = inspect.stack()[3].code_context[0].strip()
    match = re.search(r".*\((\w+).*\).*", line)
    assert match is not None, "Retrieving of name failed"
    name = match.group(1)
    return name
