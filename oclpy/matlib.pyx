cimport cython
cimport numpy as np
import numpy as np

IF OPENMP:
    from cython.parallel import prange
ELSE:
    pass

ctypedef np.float64_t DTYPE_t
DTYPE=np.float64

@cython.boundscheck(False)
@cython.wraparound(False)
@cython.embedsignature(True)
cdef int _index(double[:] array, double element) nogil:
    """ Finds the index of the closest element in the array

    Unsafe.
    9 times faster than np.abs(array - element).argmin()

    Args:
        array: The array to index
        element: The element to find
    Returns:
        The index (int) to the closest element in the array.
    """
    cdef:
        int i = 0
        double distance
        double prev_distance = (array[0] - element)**2

    for i in range(1, len(array)):
        distance = (array[i] - element)**2
        if distance > prev_distance:
            return i - 1
        else:
            prev_distance = distance
    return i

@cython.boundscheck(False)
@cython.wraparound(False)
@cython.embedsignature(True)
def index(double[:] array, double element):
    """ Finds the index of the closest element in the array

    Unsafe.
    9 times faster than np.abs(array - element).argmin()

    Args:
        array: The array to index
        element: The element to find
    Returns:
        The index (int) to the closest element in the array.
    """
    cdef:
        int i = 0
        double distance
        double prev_distance = (array[0] - element)**2

    for i in range(1, len(array)):
        distance = (array[i] - element)**2
        if distance > prev_distance:
            return i - 1
        else:
            prev_distance = distance
    return i