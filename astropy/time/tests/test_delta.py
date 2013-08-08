# Licensed under a 3-clause BSD style license - see LICENSE.rst
import functools

import numpy as np

from ...tests.helper import pytest
from .. import Time, TimeDelta, OperandTypeError

allclose_jd = functools.partial(np.allclose, rtol=2. ** -52, atol=0)
allclose_jd2 = functools.partial(np.allclose, rtol=2. ** -52,
                                 atol=2. ** -52)  # 20 ps atol
allclose_sec = functools.partial(np.allclose, rtol=2. ** -52,
                                 atol=2. ** -52 * 24 * 3600)  # 20 ps atol


class TestTimeDelta():
    """Test TimeDelta class"""

    def setup(self):
        self.t = Time('2010-01-01', scale='utc')
        self.t2 = Time('2010-01-02 00:00:01', scale='utc')
        self.dt = TimeDelta(100.0, format='sec')
        self.dt_array = TimeDelta(np.arange(100, 1000, 100), format='sec')

    def test_sub(self):
        # time - time
        dt = self.t2 - self.t
        assert (repr(dt).startswith("<TimeDelta object: scale='tai' "
                                    "format='jd' vals=1.00001157407"))
        assert allclose_jd(dt.jd, 86401.0 / 86400.0)
        assert allclose_sec(dt.sec, 86401.0)

        # time - delta_time
        t = self.t2 - dt
        assert t.iso == self.t.iso

        # delta_time - delta_time
        dt2 = dt - self.dt
        assert allclose_sec(dt2.sec, 86301.0)

        # delta_time - time
        with pytest.raises(OperandTypeError):
            dt - self.t

    def test_add(self):
        # time + time
        with pytest.raises(OperandTypeError):
            self.t2 + self.t

        # time + delta_time
        dt = self.t2 - self.t
        t2 = self.t + dt
        assert t2.iso == self.t2.iso

        # delta_time + delta_time
        dt2 = dt + self.dt
        assert allclose_sec(dt2.sec, 86501.0)

        # delta_time + time
        dt = self.t2 - self.t
        t2 = dt + self.t
        assert t2.iso == self.t2.iso

    def test_add_vector(self):
        t = Time(0.0, format='mjd', scale='utc')
        t2 = Time([0.0, 1.0], format='mjd', scale='utc')
        dt = TimeDelta(100.0, format='jd')
        dt2 = TimeDelta([100.0, 200.0], format='jd')

        out = t + dt2
        assert allclose_jd(out.mjd, [100.0, 200.0])

        out = t2 + dt
        assert allclose_jd(out.mjd, [100.0, 101.0])

        out = dt + dt2
        assert allclose_jd(out.jd, [200.0, 300.0])

        # Reverse the argument order
        out = dt2 + t
        assert allclose_jd(out.mjd, [100.0, 200.0])

        out = dt + t2
        assert allclose_jd(out.mjd, [100.0, 101.0])

        out = dt2 + dt
        assert allclose_jd(out.jd, [200.0, 300.0])

    def test_sub_vector(self):
        t = Time(0.0, format='mjd', scale='utc')
        t2 = Time([0.0, 1.0], format='mjd', scale='utc')
        dt = TimeDelta(100.0, format='jd')
        dt2 = TimeDelta([100.0, 200.0], format='jd')

        out = t - dt2
        assert allclose_jd(out.mjd, [-100.0, -200.0])

        out = t2 - dt
        assert allclose_jd(out.mjd, [-100.0, -99.0])

        out = dt - dt2
        assert allclose_jd(out.jd, [0.0, -100.0])

    def test_copy_timedelta(self):
        """Test copying the values of a TimeDelta object by passing it into the
        Time initializer.
        """
        t = Time(2455197.5, format='jd', scale='utc')
        t2 = Time(2455198.5, format='jd', scale='utc')
        dt = t2 - t

        dt2 = TimeDelta(dt, copy=False)
        assert dt.jd == dt2.jd
        assert dt._time.jd1 is dt2._time.jd1
        assert dt._time.jd2 is dt2._time.jd2

        dt2 = TimeDelta(dt, copy=True)
        assert dt.jd == dt2.jd
        assert dt._time.jd1 is not dt2._time.jd1
        assert dt._time.jd2 is not dt2._time.jd2

        # Include initializers
        dt2 = TimeDelta(dt, format='sec')
        assert allclose_sec(dt2.val, 86400.0)

    def test_neg_abs(self):
        for dt in (self.dt, self.dt_array):
            dt2 = -dt
            assert np.all(dt2.jd == -dt.jd)
            dt3 = abs(dt)
            assert np.all(dt3.jd == dt.jd)
            dt4 = abs(dt2)
            assert np.all(dt4.jd == dt.jd)

    def test_mul_div(self):
        for dt in (self.dt, self.dt_array):
            dt2 = dt + dt + dt
            dt3 = 3. * dt
            assert allclose_jd(dt2.jd, dt3.jd)
            dt4 = dt3 / 3.
            assert allclose_jd(dt4.jd, dt.jd)
        dt5 = self.dt * np.arange(3)
        assert dt5[0].jd == 0.
        assert dt5[-1].jd == (self.dt + self.dt).jd
        with pytest.raises(OperandTypeError):
            self.dt * self.dt
        with pytest.raises(OperandTypeError):
            self.dt * self.t
        with pytest.raises(TypeError):
            2. / self.dt


    def test_precision(self):
        t = Time(2455555., 0.5, format='jd', scale='utc')
        dt_tiny = TimeDelta(2. ** -52, format='jd')

        # Check that an addition at the limit of precision (2^-52) is seen
        t_dt = t + dt_tiny
        assert t_dt.jd1 == t.jd1 and t_dt.jd2 != t.jd2

        # Check that the addition is exactly reversed by the corresponding subtraction
        t2 = t_dt - dt_tiny
        assert t2.jd1 == t.jd1 and t2.jd2 == t.jd2

        dt_small = 6 * dt_tiny
        # pick a number that will leave remainder if divided by 6.
        dt_big = TimeDelta(20000., format='jd')
        dt_big_small_by_6 = (dt_big + dt_small) / 6.
        dt_frac = dt_big_small_by_6 - TimeDelta(3333., format='jd')
        assert allclose_jd2(dt_frac.jd2, 0.33333333333333354)

        # Check that 3 ways of specifying a time + small offset are equivalent
        dt_tiny_sec = dt_tiny.jd2 * 86400.
        t1 = Time(1e11, format='cxcsec') + dt_tiny
        t2 = Time(1e11, dt_tiny_sec, format='cxcsec')
        t3 = Time(dt_tiny_sec, 1e11, format='cxcsec')
        assert t1.jd1 == t2.jd1
        assert t1.jd2 == t3.jd2
        assert t1.jd1 == t2.jd1
        assert t1.jd2 == t3.jd2

        # Check that Time object really holds more precision than float64
        # by looking at the (naively) summed 64-bit result and asserting
        # equality at the bit level.
        t1 = Time(1.23456789e11, format='cxcsec')
        t2 = t1 + dt_tiny
        assert t1.jd == t2.jd

        # Check that precision holds through scale change (cxcsec is TT)
        t0 = Time(1.0, format='cxcsec')
        dt_tt = t1 - t0
        dt_tai = t1.tai - t0.tai
        assert allclose_jd(dt_tt.jd1, dt_tai.jd1)
        assert allclose_jd2(dt_tt.jd2, dt_tai.jd2)

        # Check when initializing from ISO date
        t1 = Time('2000:001:00:00:00.00000001', scale='tai')
        t2 = Time('3000:001:13:00:00.00000002', scale='tai')
        dt = t2 - t1
        assert allclose_jd2(dt.jd2, 13. / 24. + 1e-8 / 86400. - 1.0)

        # Check that jd1 is a multiple of 0.5 (note the difference from when
        # Time is created with a format like 'jd' or 'cxcsec', where jd1 is
        # a multiple of 1.0).
        t1 = Time('2000:001:00:00:00.00000001', scale='tai')
        assert np.round(t1.jd1 * 2) == t1.jd1 * 2
        t1 = Time(1.23456789, 12345678.90123456, format='jd', scale='tai')
        assert np.round(t1.jd1) == t1.jd1

    @pytest.mark.xfail
    def test_precision_neg(self):
        """
        Check precision when jd1 is negative.  Currently fails because ERFA routines use a
        test like jd1 > jd2 to decide which component to update.  Should be
        abs(jd1) > abs(jd2).
        """
        t1 = Time(-100000.123456, format='jd', scale='tt')
        assert np.round(t1.jd1) == t1.jd1
        t1_tai = t1.tai
        assert np.round(t1_tai.jd1) == t1_tai.jd1
