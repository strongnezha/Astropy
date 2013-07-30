# Licensed under a 3-clause BSD style license - see LICENSE.rst
import numpy as np

from ....tests.helper import pytest
from ..convolve import convolve, convolve_fft
from ..kernels import *

from numpy.testing import assert_almost_equal

import itertools


widths = [3, 5, 7, 9]
kernel_types = [GaussianKernel, BoxKernel, Tophat2DKernel, MexicanHat1DKernel, AiryDisk2DKernel]


class Test2DConvolutions(object):

    @pytest.mark.parametrize(('kernel_type', 'width'), list(itertools.product(kernel_types, widths)))
    def test_centered_makekernel(self, kernel_type,  width):
        """
        Test smoothing of an image with a single positive pixel
        """
        kernel = kernel_type(width)

        x = np.zeros(kernel.shape)
        xslice = [slice(sh // 2, sh // 2) for sh in kernel.shape]
        x[xslice] = 1.0

        c2 = convolve_fft(x, kernel.mask, boundary='fill')
        c1 = convolve(x, kernel.mask, boundary='fill')

        assert_almost_equal(c1, c2, decimal=12)

    @pytest.mark.parametrize(('kernel_type', 'width'), list(itertools.product(kernel_types, widths)))
    def test_random_makekernel(self, kernel_type, width):
        """
        Test smoothing of an image made of random noise
        """
        kernel = kernel_type(width)

        x = np.zeros(kernel.shape)
        xslice = [slice(sh // 2, sh // 2) for sh in kernel.shape]
        x[xslice] = 1.0

        x = np.random.randn(*kernel.shape)

        c2 = convolve_fft(x, kernel.mask, boundary='fill')
        c1 = convolve(x, kernel.mask, boundary='fill')

        # not clear why, but these differ by a couple ulps...
        assert_almost_equal(c1, c2, decimal=12)

    @pytest.mark.parametrize(('width'), widths)
    def test_uniform_smallkernel(self, width):
        """
        Test smoothing of an image with a single positive pixel

        Instead of using make_kernel, uses a simple, small kernel
        """
        if width % 2 == 0:
            # convolve does not accept odd-shape kernels
            return

        kernel = np.ones([width, width])

        x = np.zeros([width, width])
        xslice = [slice(sh // 2, sh // 2) for sh in [width, width]]
        x[xslice] = 1.0

        c2 = convolve_fft(x, kernel, boundary='fill')
        c1 = convolve(x, kernel, boundary='fill')

        assert_almost_equal(c1, c2, decimal=12)

    @pytest.mark.parametrize(('width'), widths)
    def test_smallkernel_vs_makekernel(self, width):
        """
        Test smoothing of an image with a single positive pixel

        Compares a small kernel to something produced by makekernel
        """
        box = BoxKernel(width)
        kernel1 = np.ones([width, width])
        kernel2 = np.outer(box.mask, box.mask)

        x = np.zeros(kernel2.shape)
        xslice = [slice(sh // 2, sh // 2) for sh in kernel2.shape]
        x[xslice] = 1.0

        c2 = convolve_fft(x, kernel2, boundary='fill')
        c1 = convolve_fft(x, kernel1, boundary='fill')

        assert_almost_equal(c1, c2, decimal=12)
