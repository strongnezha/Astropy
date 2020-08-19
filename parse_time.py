""" Example of wrapping a C library function that accepts a C double array as
    input using the numpy.ctypeslib. """

import numpy as np
import numpy.ctypeslib as npct
from ctypes import c_int

# input type for the parse_iso_time function
# must be a double array, with single dimension that is contiguous
array_1d_char = npct.ndpointer(dtype=np.uint8, ndim=1, flags='C_CONTIGUOUS')
array_1d_double = npct.ndpointer(dtype=np.double, ndim=1, flags='C_CONTIGUOUS')
array_1d_int = npct.ndpointer(dtype=np.intc, ndim=1, flags='C_CONTIGUOUS')

# load the library, using numpy mechanisms
libpt = npct.load_library("libparse_time.so", ".")

# setup the return types and argument types
libpt.parse_iso_time.restype = c_int
libpt.parse_iso_time.argtypes = [array_1d_char, c_int,
                             array_1d_int, array_1d_int, array_1d_int,
                             array_1d_int, array_1d_int, array_1d_double]


val1 = np.array('2020-01-01 12:13:14.4324')
val1_str_len = int(val1.dtype.itemsize // (4 if val1.dtype.kind == 'U' else 1))
chars = val1.ravel().view(np.uint8)
if val1.dtype.kind == 'U':
    chars.shape = (-1, 4)
    assert np.all(chars[:, 1:4] == 0)
    chars = chars[:, 0]

chars = np.array(chars, dtype=np.uint8, order='C')
year = np.zeros(1, dtype=np.intc)
month = np.zeros(1, dtype=np.intc)
day = np.zeros(1, dtype=np.intc)
hour = np.zeros(1, dtype=np.intc)
minute = np.zeros(1, dtype=np.intc)
second = np.zeros(1, dtype=np.double)

print(chars)
print(val1_str_len)
status = libpt.parse_iso_time(chars, val1_str_len,
                          year, month, day, hour, minute, second)
