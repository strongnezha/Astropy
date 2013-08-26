# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import division

import numpy as np
from numpy.testing import assert_equal
from ...tests.helper import pytest
from ...tests.compat import assert_allclose

from .. import funcs
from ...utils.misc import NumpyRNGContext

try:
    from scipy import stats  # used in testing
except ImportError:
    HAS_SCIPY = False
else:
    HAS_SCIPY = True


def test_sigma_clip():
    from numpy.random import randn

    #need to seed the numpy RNG to make sure we don't get some amazingly flukey
    #random number that breaks one of the tests

    with NumpyRNGContext(12345):
        # Amazing, I've got the same combination on my luggage!
        randvar = randn(10000)

        filtered_data = funcs.sigma_clip(randvar, 1, 2)

        assert sum(filtered_data.mask) > 0
        assert sum(~filtered_data.mask) < randvar.size

        #this is actually a silly thing to do, because it uses the standard
        #deviation as the variance, but it tests to make sure these arguments
        #are actually doing something
        filtered_data2 = funcs.sigma_clip(randvar, 1, 2, varfunc=np.std)
        assert not np.all(filtered_data.mask == filtered_data2.mask)

        filtered_data3 = funcs.sigma_clip(randvar, 1, 2, cenfunc=np.mean)
        assert not np.all(filtered_data.mask == filtered_data3.mask)

        # make sure the iters=None method works at all.
        filtered_data = funcs.sigma_clip(randvar, 3, None)

        # test copying
        assert filtered_data.data[0] == randvar[0]
        filtered_data.data[0] += 1.
        assert filtered_data.data[0] != randvar[0]

        filtered_data = funcs.sigma_clip(randvar, 3, None, copy=False)
        assert filtered_data.data[0] == randvar[0]
        filtered_data.data[0] += 1.
        assert filtered_data.data[0] == randvar[0]

        # test axis
        data = np.arange(5)+np.random.normal(0.,0.05,(5,5))+np.diag(np.ones(5))
        filtered_data = funcs.sigma_clip(data, axis=0, sig=2.3)
        assert filtered_data.count() == 20
        filtered_data = funcs.sigma_clip(data, axis=1, sig=2.3)
        assert filtered_data.count() == 25


def test_median_absolute_deviation():
    from numpy.random import randn

    #need to seed the numpy RNG to make sure we don't get some amazingly flukey
    #random number that breaks one of the tests

    with NumpyRNGContext(12345):

        #test that it runs
        randvar = randn(10000)
        mad = funcs.median_absolute_deviation(randvar)

        #test whether an array is returned if an axis is used
        randvar = randvar.reshape((10, 1000))
        mad = funcs.median_absolute_deviation(randvar, axis=1)
        assert len(mad) == 10
        assert mad.size < randvar.size


def test_biweight_location():
    from numpy.random import randn

    #need to seed the numpy RNG to make sure we don't get some amazingly flukey
    #random number that breaks one of the tests

    with NumpyRNGContext(12345):

        #test that it runs
        randvar = randn(10000)
        cbl = funcs.biweight_location(randvar)

        assert abs(cbl-0) < 1e-2


def test_biweight_midvariance():
    from numpy.random import randn

    #need to seed the numpy RNG to make sure we don't get some amazingly flukey
    #random number that breaks one of the tests

    with NumpyRNGContext(12345):

        #test that it runs
        randvar = randn(10000)
        scl = funcs.biweight_midvariance(randvar)

        assert abs(scl-1) < 1e-2


@pytest.mark.skipif('not HAS_SCIPY')
def test_compare_to_scipy_sigmaclip():
    from numpy.random import randn

    #need to seed the numpy RNG to make sure we don't get some amazingly flukey
    #random number that breaks one of the tests

    with NumpyRNGContext(12345):

        randvar = randn(10000)

        astropyres = funcs.sigma_clip(randvar, 3, None, np.mean)
        scipyres = stats.sigmaclip(randvar, 3, 3)[0]

        assert astropyres.count() == len(scipyres)
        assert_equal(astropyres[~astropyres.mask].data, scipyres)


@pytest.mark.skipif('not HAS_SCIPY')
def test_binom_conf_interval():

    # Test Wilson and Jeffreys interval for corner cases:
    # Corner cases: k = 0, k = n, conf = 0., conf = 1.
    n = 5
    k = [0, 4, 5]
    for conf in [0., 0.5, 1.]:
        res = funcs.binom_conf_interval(k, n, conf=conf, interval='wilson')
        assert ((res >= 0.) & (res <= 1.)).all()
        res = funcs.binom_conf_interval(k, n, conf=conf, interval='jeffreys')
        assert ((res >= 0.) & (res <= 1.)).all()

    # Test Jeffreys interval accuracy against table in Brown et al. (2001).
    # (See `binom_conf_interval` docstring for reference.)
    k = [0, 1, 2, 3, 4]
    n = 7
    conf = 0.95
    result = funcs.binom_conf_interval(k, n, conf=conf, interval='jeffreys')
    table = np.array([[0.000, 0.016, 0.065, 0.139, 0.234],
                      [0.292, 0.501, 0.648, 0.766, 0.861]])
    assert_allclose(result, table, atol=1.e-3, rtol=0.)

    # Test Wald interval
    result = funcs.binom_conf_interval(0, 5, interval='wald')
    assert_allclose(result, 0.)  # conf interval is [0, 0] when k = 0
    result = funcs.binom_conf_interval(5, 5, interval='wald')
    assert_allclose(result, 1.)  # conf interval is [1, 1] when k = n
    result = funcs.binom_conf_interval(500, 1000, conf=0.68269,
                                       interval='wald')
    assert_allclose(result[0], 0.5 - 0.5 / np.sqrt(1000.))
    assert_allclose(result[1], 0.5 + 0.5 / np.sqrt(1000.))


@pytest.mark.skipif('not HAS_SCIPY')
def test_binned_binom_proportion():

    # Check that it works.
    nbins = 20
    x = np.linspace(0., 10., 100)  # Guarantee an `x` in every bin.
    success = np.ones(len(x), dtype=np.bool)
    bin_ctr, bin_hw, p, perr = funcs.binned_binom_proportion(x, success,
                                                             bins=nbins)

    # Check shape of outputs
    assert bin_ctr.shape == (nbins,)
    assert bin_hw.shape == (nbins,)
    assert p.shape == (nbins,)
    assert perr.shape == (2, nbins)

    # Check that p is 1 in all bins, since success = True for all `x`.
    assert (p == 1.).all()

    # Check that p is 0 in all bins if success = False for all `x`.
    success[:] = False
    bin_ctr, bin_hw, p, perr = funcs.binned_binom_proportion(x, success,
                                                             bins=nbins)
    assert (p == 0.).all()
    
def test_signal_to_noise_oir_ccd():
    
    result = funcs.signal_to_noise_oir_ccd(1,25,0,0,0,1)
    assert 5.0 == result
    #check to make sure gain works
    result = funcs.signal_to_noise_oir_ccd(1,5,0,0,0,1,5)
    assert 5.0 == result
    
    #now add in sky, dark current, and read noise 
    #make sure the snr goes down
    result = funcs.signal_to_noise_oir_ccd(1,25,1,0,0,1)
    assert result < 5.0
    result = funcs.signal_to_noise_oir_ccd(1,25,0,1,0,1)
    assert result < 5.0
    result = funcs.signal_to_noise_oir_ccd(1,25,0,0,1,1)
    assert result < 5.0
    
    #make sure snr increases with time
    result = funcs.signal_to_noise_oir_ccd(2,25,0,0,0,1)
    assert result > 5.0

def test_bootstrap():
    bootarr = np.array([1,2,3,4,5,6,7,8,9,0])
    #test general bootstrapping
    answer = np.array([[7,4,8,5,7,0,3,7,8,5],[4,8,8,3,6,5,2,8,6,2]])
    with NumpyRNGContext(42):
        assert_equal(answer,funcs.bootstrap(bootarr,2))
    
    #test with a bootfunction
    with NumpyRNGContext(42):
        bootresult = np.mean(bootstrap(a,10000,bootfunc=np.mean))
        assert_allclose(np.mean(bootarr),bootresult,atol=0.01)

    
