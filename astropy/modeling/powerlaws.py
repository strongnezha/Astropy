# Licensed under a 3-clause BSD style license - see LICENSE.rst

"""
Power law model variants
"""

from __future__ import (absolute_import, unicode_literals, division,
                        print_function)

import numpy as np

from .core import Fittable1DModel
from .parameters import Parameter, InputParameterError


__all__ = ['PowerLaw1D', 'BrokenPowerLaw1D', 'SmoothlyBrokenPowerLaw1D',
           'ExponentialCutoffPowerLaw1D', 'LogParabola1D']


class PowerLaw1D(Fittable1DModel):
    """
    One dimensional power law model.

    Parameters
    ----------
    amplitude : float
        Model amplitude at the reference point
    x_0 : float
        Reference point
    alpha : float
        Power law index

    See Also
    --------
    BrokenPowerLaw1D, ExponentialCutoffPowerLaw1D, LogParabola1D

    Notes
    -----
    Model formula (with :math:`A` for ``amplitude`` and :math:`\\alpha` for ``alpha``):

        .. math:: f(x) = A (x / x_0) ^ {-\\alpha}

    """

    amplitude = Parameter(default=1)
    x_0 = Parameter(default=1)
    alpha = Parameter(default=1)

    @staticmethod
    def evaluate(x, amplitude, x_0, alpha):
        """One dimensional power law model function"""

        xx = x / x_0
        return amplitude * xx ** (-alpha)

    @staticmethod
    def fit_deriv(x, amplitude, x_0, alpha):
        """One dimensional power law derivative with respect to parameters"""

        xx = x / x_0

        d_amplitude = xx ** (-alpha)
        d_x_0 = amplitude * alpha * d_amplitude / x_0
        d_alpha = -amplitude * d_amplitude * np.log(xx)

        return [d_amplitude, d_x_0, d_alpha]


class BrokenPowerLaw1D(Fittable1DModel):
    """
    One dimensional power law model with a break.

    Parameters
    ----------
    amplitude : float
        Model amplitude at the break point
    x_break : float
        Break point
    alpha_1 : float
        Power law index for x < x_break
    alpha_2 : float
        Power law index for x > x_break

    See Also
    --------
    PowerLaw1D, ExponentialCutoffPowerLaw1D, LogParabola1D

    Notes
    -----
    Model formula (with :math:`A` for ``amplitude`` and :math:`\\alpha_1`
    for ``alpha_1`` and :math:`\\alpha_2` for ``alpha_2``):

        .. math::

            f(x) = \\left \\{
                     \\begin{array}{ll}
                       A (x / x_{break}) ^ {-\\alpha_1} & : x < x_{break} \\\\
                       A (x / x_{break}) ^ {-\\alpha_2} & :  x > x_{break} \\\\
                     \\end{array}
                   \\right.
    """

    amplitude = Parameter(default=1)
    x_break = Parameter(default=1)
    alpha_1 = Parameter(default=1)
    alpha_2 = Parameter(default=1)

    @staticmethod
    def evaluate(x, amplitude, x_break, alpha_1, alpha_2):
        """One dimensional broken power law model function"""

        alpha = np.where(x < x_break, alpha_1, alpha_2)
        xx = x / x_break
        return amplitude * xx ** (-alpha)

    @staticmethod
    def fit_deriv(x, amplitude, x_break, alpha_1, alpha_2):
        """One dimensional broken power law derivative with respect to parameters"""

        alpha = np.where(x < x_break, alpha_1, alpha_2)
        xx = x / x_break

        d_amplitude = xx ** (-alpha)
        d_x_break = amplitude * alpha * d_amplitude / x_break
        d_alpha = -amplitude * d_amplitude * np.log(xx)
        d_alpha_1 = np.where(x < x_break, d_alpha, 0)
        d_alpha_2 = np.where(x >= x_break, d_alpha, 0)

        return [d_amplitude, d_x_break, d_alpha_1, d_alpha_2]


class SmoothlyBrokenPowerLaw1D(Fittable1DModel):
    """One dimensional smoothly broken power law model.

    Parameters
    ----------
    amplitude : float
        Model amplitude at the break point.
    log_break : float
        logarithm (base 10) of break point.
    alpha_1 : float
        Power law index for ``x << 10 ** log_break``.
    alpha_2 : float
        Power law index for ``x >> 10 ** log_break``.
    delta : float
        Smoothness parameter (must be positive).

    See Also
    --------
    BrokenPowerLaw1D

    Notes
    -----
    Model formula (with :math:`A` for ``amplitude``, :math:`x_b` for
    ``10 ** log_break``, :math:`\\alpha_1` for ``alpha_1``,
    :math:`\\alpha_2` for ``alpha_2`` and :math:`\\Delta` for
    ``delta``):

        .. math::

            f(x) = A \\left( \\frac{x}{x_b} \\right) ^ {-\\alpha_1}
                   \\left\\{
                      \\frac{1}{2}
                      \\left[
                        1 + \\left( \\frac{x}{x_b}\\right)^{1 / \\Delta}
                      \\right]
                   \\right\\}^{(\\alpha_1 - \\alpha_2) \\Delta}


    The change of slope occurs between the values :math:`x_1`
    and :math:`x_2` such that:

        .. math::
            \\log_{10} \\frac{x_2}{x_b} = \\log_{10} \\frac{x_b}{x_1}
            \\sim \\Delta


    At values :math:`x \\lesssim x_1` and :math:`x \\gtrsim x_2` the
    model is approximately a simple power law with index
    :math:`\\alpha_1` and :math:`\\alpha_2` respectively.  The two
    power laws are smoothly joined at values :math:`x_1 < x < x_2`,
    hence the :math:`\\Delta` parameter sets the "smoothness" of the
    slope change.


    Examples
    --------
    .. plot::
        :include-source:

        import numpy as np
        import matplotlib.pyplot as plt
        from astropy.modeling import models

        x = np.logspace(0.7, 2.3, 500)
        f = models.SmoothlyBrokenPowerLaw1D(amplitude=1, log_break=1.5,
                                            alpha_1=-2, alpha_2=2)

        plt.figure()
        plt.title("amplitude=1, log_break=1.5, alpha_1=-2, alpha_2=2")

        f.delta = 0.5
        plt.loglog(x, f(x), '--', label='delta=0.5')

        f.delta = 0.3
        plt.loglog(x, f(x), '-.', label='delta=0.3')

        f.delta = 0.1
        plt.loglog(x, f(x), label='delta=0.1')

        plt.axis([x.min(), x.max(), 0.1, 1.1])
        plt.legend(loc='lower center')
        plt.grid(True)
        plt.show()

    """

    amplitude = Parameter(default=1, min=0)
    log_break = Parameter(default=1)
    alpha_1 = Parameter(default=-2)
    alpha_2 = Parameter(default=2)
    delta = Parameter(default=1, min=1.e-3)

    @amplitude.validator
    def amplitude(self, value):
        if np.any(value <= 0):
            raise InputParameterError(
                "amplitude parameter must be > 0")

    @delta.validator
    def delta(self, value):
        if np.any(value < 0.001):
            raise InputParameterError(
                "delta parameter must be >= 0.001")




    @staticmethod
    def evaluate(x, amplitude, log_break, alpha_1, alpha_2, delta):
        """One dimensional smoothly broken power law model function"""

        #Pre-calculate `x_b` and `x/x_b`
        x_b = 10. ** log_break
        xx = x / x_b

        #Initialize the return value
        f = np.zeros_like(xx)

        #The quantity `t = (x / x_b)^(1 / delta)` can become quite
        #large.  To avoid overflow errors we will start by calculating
        #its natural logarithm:
        logt = np.log(xx) / delta

        #When `t >> 1` or `t << 1` we don't actually need to compute
        #the `t` value since the main formula (see docstring) can be
        #significantly simplified by neglecting `1` or `t`
        #respectively.  In the following we will check whether `t` is
        #much greater, much smaller, or comparable to 1 by comparing
        #the `logt` value with an appropriate threshold.
        threshold = 30 #corresponding to exp(30) ~ 1e13
        i = logt > threshold
        if (i.max()):
            #In this case the main formula reduces to a simple power
            #law with index `alpha_2`.
            f[i] = amplitude * xx[i] ** (-alpha_2) \
                   / (2. ** ((alpha_1 - alpha_2) * delta))

        i = logt < -threshold
        if (i.max()):
            #In this case the main formula reduces to a simple power
            #law with index `alpha_1`.
            f[i] = amplitude * xx[i] ** (-alpha_1) \
                   / (2. ** ((alpha_1 - alpha_2) * delta))

        i = np.abs(logt) <= threshold
        if (i.max()):
            #In this case the `t` value is "comparable" to 1, hence we
            #we will evaluate the whole formula.
            t = np.exp(logt[i])
            r = (1. + t) / 2.
            f[i] = amplitude * xx[i] ** (-alpha_1) \
                   * r ** ((alpha_1 - alpha_2) * delta)

        return f

    @staticmethod
    def fit_deriv(x, amplitude, log_break, alpha_1, alpha_2, delta):
        """One dimensional smoothly broken power law derivative with respect
           to parameters"""

        #Pre-calculate `x_b` and `x/x_b` and `logt` (see comments in
        #SmoothlyBrokenPowerLaw1D.evaluate)
        x_b = 10. ** log_break
        xx = x / x_b
        logt = np.log(xx) / delta

        #Initialize the return values
        f = np.zeros_like(xx)
        d_amplitude = np.zeros_like(xx)
        d_log_break = np.zeros_like(xx)
        d_alpha_1 = np.zeros_like(xx)
        d_alpha_2 = np.zeros_like(xx)
        d_delta = np.zeros_like(xx)

        threshold = 30 #(see comments in SmoothlyBrokenPowerLaw1D.evaluate)
        i = logt > threshold
        if (i.max()):
            f[i] = amplitude * xx[i] ** (-alpha_2) \
                   / (2. ** ((alpha_1 - alpha_2) * delta))

            d_amplitude[i] = f[i] / amplitude
            d_log_break[i] = f[i] * alpha_2 * np.log(10)
            d_alpha_1[i] = f[i] * (-delta * np.log(2))
            d_alpha_2[i] = f[i] * (-np.log(xx[i]) + delta * np.log(2))
            d_delta[i] = f[i] * (-(alpha_1 - alpha_2) * np.log(2))

        i = logt < -threshold
        if (i.max()):
            f[i] = amplitude * xx[i] ** (-alpha_1) \
                   / (2. ** ((alpha_1 - alpha_2) * delta))

            d_amplitude[i] = f[i] / amplitude
            d_log_break[i] = f[i] * alpha_1 * np.log(10)
            d_alpha_1[i] = f[i] * (-np.log(xx[i]) - delta * np.log(2))
            d_alpha_2[i] = f[i] * delta * np.log(2)
            d_delta[i] = f[i] * (-(alpha_1 - alpha_2) * np.log(2))

        i = np.abs(logt) <= threshold
        if (i.max()):
            t = np.exp(logt[i])
            r = (1. + t) / 2.
            f[i] = amplitude * xx[i] ** (-alpha_1) \
                   * r ** ((alpha_1 - alpha_2) * delta)

            d_amplitude[i] = f[i] / amplitude
            d_log_break[i] = f[i] \
                             * (alpha_1 - (alpha_1 - alpha_2) * t / 2. / r) \
                             * np.log(10)
            d_alpha_1[i] = f[i] * (-np.log(xx[i]) + delta * np.log(r))
            d_alpha_2[i] = f[i] * (-delta * np.log(r))
            d_delta[i] = f[i] * (alpha_1 - alpha_2) \
                         * (np.log(r) - t / (1. + t) / delta * np.log(xx[i]))

        return [d_amplitude, d_log_break, d_alpha_1, d_alpha_2, d_delta]


class ExponentialCutoffPowerLaw1D(Fittable1DModel):
    """
    One dimensional power law model with an exponential cutoff.

    Parameters
    ----------
    amplitude : float
        Model amplitude
    x_0 : float
        Reference point
    alpha : float
        Power law index
    x_cutoff : float
        Cutoff point

    See Also
    --------
    PowerLaw1D, BrokenPowerLaw1D, LogParabola1D

    Notes
    -----
    Model formula (with :math:`A` for ``amplitude`` and :math:`\\alpha` for ``alpha``):

        .. math:: f(x) = A (x / x_0) ^ {-\\alpha} \\exp (-x / x_{cutoff})

    """

    amplitude = Parameter(default=1)
    x_0 = Parameter(default=1)
    alpha = Parameter(default=1)
    x_cutoff = Parameter(default=1)

    @staticmethod
    def evaluate(x, amplitude, x_0, alpha, x_cutoff):
        """One dimensional exponential cutoff power law model function"""

        xx = x / x_0
        return amplitude * xx ** (-alpha) * np.exp(-x / x_cutoff)

    @staticmethod
    def fit_deriv(x, amplitude, x_0, alpha, x_cutoff):
        """One dimensional exponential cutoff power law derivative with respect to parameters"""

        xx = x / x_0
        xc = x / x_cutoff

        d_amplitude = xx ** (-alpha) * np.exp(-xc)
        d_x_0 = alpha * amplitude * d_amplitude / x_0
        d_alpha = -amplitude * d_amplitude * np.log(xx)
        d_x_cutoff = amplitude * x * d_amplitude / x_cutoff ** 2

        return [d_amplitude, d_x_0, d_alpha, d_x_cutoff]


class LogParabola1D(Fittable1DModel):
    """
    One dimensional log parabola model (sometimes called curved power law).

    Parameters
    ----------
    amplitude : float
        Model amplitude
    x_0 : float
        Reference point
    alpha : float
        Power law index
    beta : float
        Power law curvature

    See Also
    --------
    PowerLaw1D, BrokenPowerLaw1D, ExponentialCutoffPowerLaw1D

    Notes
    -----
    Model formula (with :math:`A` for ``amplitude`` and :math:`\\alpha` for ``alpha`` and :math:`\\beta` for ``beta``):

        .. math:: f(x) = A \\left(\\frac{x}{x_{0}}\\right)^{- \\alpha - \\beta \\log{\\left (\\frac{x}{x_{0}} \\right )}}

    """

    amplitude = Parameter(default=1)
    x_0 = Parameter(default=1)
    alpha = Parameter(default=1)
    beta = Parameter(default=0)

    @staticmethod
    def evaluate(x, amplitude, x_0, alpha, beta):
        """One dimensional log parabola model function"""

        xx = x / x_0
        exponent = -alpha - beta * np.log(xx)
        return amplitude * xx ** exponent

    @staticmethod
    def fit_deriv(x, amplitude, x_0, alpha, beta):
        """One dimensional log parabola derivative with respect to parameters"""

        xx = x / x_0
        log_xx = np.log(xx)
        exponent = -alpha - beta * log_xx

        d_amplitude = xx ** exponent
        d_beta = -amplitude * d_amplitude * log_xx ** 2
        d_x_0 = amplitude * d_amplitude * (beta * log_xx / x_0 - exponent / x_0)
        d_alpha = -amplitude * d_amplitude * log_xx
        return [d_amplitude, d_x_0, d_alpha, d_beta]
