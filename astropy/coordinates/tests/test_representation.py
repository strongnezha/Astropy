# -*- coding: utf-8 -*-
# Licensed under a 3-clause BSD style license - see LICENSE.rst

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import numpy as np
from numpy.testing import assert_allclose

from ... import units as u
from ...tests.helper import pytest
from ..angles import Longitude, Latitude, Angle
from ..distances import Distance
from ..representation import (SphericalRepresentation,
                              UnitSphericalRepresentation,
                              CartesianRepresentation,
                              CylindricalRepresentation,
                              PhysicsSphericalRepresentation)


def assert_allclose_quantity(q1, q2):
    assert_allclose(q1.value, q2.to(q1.unit).value)


class TestSphericalRepresentation(object):

    def test_empty_init(self):
        with pytest.raises(TypeError) as exc:
            s = SphericalRepresentation()

    def test_init_quantity(self):

        s3 = SphericalRepresentation(lon=8 * u.hourangle, lat=5 * u.deg, distance=10 * u.kpc)
        assert s3.lon == 8. * u.hourangle
        assert s3.lat == 5. * u.deg
        assert s3.distance == 10 * u.kpc

        assert isinstance(s3.lon, Longitude)
        assert isinstance(s3.lat, Latitude)
        assert isinstance(s3.distance, Distance)

    def test_init_lonlat(self):

        s2 = SphericalRepresentation(Longitude(8, u.hour),
                                     Latitude(5, u.deg),
                                     Distance(10, u.kpc))

        assert s2.lon == 8. * u.hourangle
        assert s2.lat == 5. * u.deg
        assert s2.distance == 10. * u.kpc

        assert isinstance(s2.lon, Longitude)
        assert isinstance(s2.lat, Latitude)
        assert isinstance(s2.distance, Distance)

    def test_init_array(self):

        s1 = SphericalRepresentation(lon=[8, 9] * u.hourangle,
                                     lat=[5, 6] * u.deg,
                                     distance=[1,2] * u.kpc)

        assert_allclose(s1.lon.degree, [120, 135])
        assert_allclose(s1.lat.degree, [5, 6])
        assert_allclose(s1.distance.kpc, [1, 2])

        assert isinstance(s1.lon, Longitude)
        assert isinstance(s1.lat, Latitude)
        assert isinstance(s1.distance, Distance)

    def test_init_array_nocopy(self):

        lon = Longitude([8, 9] * u.hourangle)
        lat = Latitude([5, 6] * u.deg)
        distance = Distance([1, 2] * u.kpc)

        s1 = SphericalRepresentation(lon=lon, lat=lat, distance=distance, copy=False)

        lon[:] = [1,2] * u.rad
        lat[:] = [3,4] * u.arcmin
        distance[:] = [8,9] * u.Mpc

        assert_allclose_quantity(lon, s1.lon)
        assert_allclose_quantity(lat, s1.lat)
        assert_allclose_quantity(distance, s1.distance)

    def test_init_str(self):

        s1 = SphericalRepresentation(lon='2h6m3.3s', lat='0.1rad', distance=1 * u.kpc)
        assert_allclose(s1.lon.degree, 31.513749999999995)
        assert_allclose(s1.lat.degree, 5.729577951308233)
        assert_allclose(s1.distance.kpc, 1.)

    def test_reprobj(self):

        s1 = SphericalRepresentation(lon=8 * u.hourangle, lat=5 * u.deg, distance=10 * u.kpc)

        s2 = SphericalRepresentation.from_representation(s1)

        assert_allclose_quantity(s2.lon, 8. * u.hourangle)
        assert_allclose_quantity(s2.lat, 5. * u.deg)
        assert_allclose_quantity(s2.distance, 10 * u.kpc)

    def test_broadcasting(self):

        s1 = SphericalRepresentation(lon=[8, 9]*u.hourangle,
                                     lat=[5, 6]*u.deg,
                                     distance=10*u.kpc)

        assert_allclose_quantity(s1.lon, [120, 135] * u.degree)
        assert_allclose_quantity(s1.lat, [5, 6] * u.degree)
        assert_allclose_quantity(s1.distance, [10, 10] * u.kpc)

    def test_broadcasting_mismatch(self):

        with pytest.raises(ValueError) as exc:
            s1 = SphericalRepresentation(lon=[8, 9, 10]*u.hourangle,
                                         lat=[5, 6]*u.deg,
                                         distance=[1, 2] * u.kpc)
        assert exc.value.args[0] == "Input parameters lon, lat, and distance cannot be broadcast"

    def test_mixed_units(self):

        # It's also possible to pass in scalar quantity lists with mixed
        # units. These are converted to array quantities following the same
        # rule as `Quantity`: all elements are converted to match the first
        # element's units.

        s1 = SphericalRepresentation(lon=[8*u.hourangle, 135*u.deg],
                                     lat=[5*u.deg, (6*np.pi/180)*u.rad],
                                     distance=[1.*u.kpc, 500*u.pc])
        assert s1.lon.unit == u.hourangle
        assert s1.lat.unit == u.deg
        assert s1.distance.unit == u.kpc
        assert_allclose(s1.lon.value, [8,9])
        assert_allclose(s1.lat.value, [5,6])
        assert_allclose(s1.distance.value, [1,0.5])

    def test_readonly(self):

        s1 = SphericalRepresentation(lon=[8*u.hourangle, 135*u.deg],
                                     lat=[5*u.deg, (6*np.pi/180)*u.rad],
                                     distance=[1.*u.kpc, 500*u.pc])

        with pytest.raises(AttributeError):
            s1.lon = 1. * u.deg

        with pytest.raises(AttributeError):
            s1.lat = 1. * u.deg

        with pytest.raises(AttributeError):
            s1.distance = 1. * u.kpc

    def test_getitem(self):

        s = SphericalRepresentation(lon=np.arange(10) * u.deg,
                                    lat=-np.arange(10) * u.deg,
                                    distance=1 * u.kpc)

        s_slc = s[2:8:2]

        assert_allclose_quantity(s_slc.lon, [2,4,6] * u.deg)
        assert_allclose_quantity(s_slc.lat, [-2,-4,-6] * u.deg)
        assert_allclose_quantity(s_slc.distance, [1,1,1] * u.kpc)

    def test_getitem_scalar(self):

        s = SphericalRepresentation(lon=1 * u.deg,
                                    lat=-2 * u.deg,
                                    distance=3 * u.kpc)

        with pytest.raises(TypeError):
            s_slc = s[0]


class TestUnitSphericalRepresentation(object):

    def test_empty_init(self):
        with pytest.raises(TypeError) as exc:
            s = UnitSphericalRepresentation()

    def test_init_quantity(self):

        s3 = UnitSphericalRepresentation(lon=8 * u.hourangle, lat=5 * u.deg)
        assert s3.lon == 8. * u.hourangle
        assert s3.lat == 5. * u.deg

        assert isinstance(s3.lon, Longitude)
        assert isinstance(s3.lat, Latitude)

    def test_init_lonlat(self):

        s2 = UnitSphericalRepresentation(Longitude(8, u.hour),
                                     Latitude(5, u.deg))

        assert s2.lon == 8. * u.hourangle
        assert s2.lat == 5. * u.deg

        assert isinstance(s2.lon, Longitude)
        assert isinstance(s2.lat, Latitude)

    def test_init_array(self):

        s1 = UnitSphericalRepresentation(lon=[8, 9] * u.hourangle,
                                     lat=[5, 6] * u.deg)

        assert_allclose(s1.lon.degree, [120, 135])
        assert_allclose(s1.lat.degree, [5, 6])

        assert isinstance(s1.lon, Longitude)
        assert isinstance(s1.lat, Latitude)

    def test_init_array_nocopy(self):

        lon = Longitude([8, 9] * u.hourangle)
        lat = Latitude([5, 6] * u.deg)

        s1 = UnitSphericalRepresentation(lon=lon, lat=lat, copy=False)

        lon[:] = [1,2] * u.rad
        lat[:] = [3,4] * u.arcmin

        assert_allclose_quantity(lon, s1.lon)
        assert_allclose_quantity(lat, s1.lat)

    def test_init_str(self):

        s1 = UnitSphericalRepresentation(lon='2h6m3.3s', lat='0.1rad')
        assert_allclose(s1.lon.degree, 31.513749999999995)
        assert_allclose(s1.lat.degree, 5.729577951308233)

    def test_reprobj(self):

        s1 = UnitSphericalRepresentation(lon=8 * u.hourangle, lat=5 * u.deg)

        s2 = UnitSphericalRepresentation.from_representation(s1)

        assert_allclose_quantity(s2.lon, 8. * u.hourangle)
        assert_allclose_quantity(s2.lat, 5. * u.deg)

    def test_broadcasting(self):

        s1 = UnitSphericalRepresentation(lon=[8, 9]*u.hourangle,
                                     lat=[5, 6]*u.deg)

        assert_allclose_quantity(s1.lon, [120, 135] * u.degree)
        assert_allclose_quantity(s1.lat, [5, 6] * u.degree)

    def test_broadcasting_mismatch(self):

        with pytest.raises(ValueError) as exc:
            s1 = UnitSphericalRepresentation(lon=[8, 9, 10]*u.hourangle,
                                         lat=[5, 6]*u.deg)
        assert exc.value.args[0] == "Input parameters lon and lat cannot be broadcast"

    def test_mixed_units(self):

        # It's also possible to pass in scalar quantity lists with mixed
        # units. These are converted to array quantities following the same
        # rule as `Quantity`: all elements are converted to match the first
        # element's units.

        s1 = UnitSphericalRepresentation(lon=[8*u.hourangle, 135*u.deg],
                                     lat=[5*u.deg, (6*np.pi/180)*u.rad])

        assert s1.lon.unit == u.hourangle
        assert s1.lat.unit == u.deg
        assert_allclose(s1.lon.value, [8,9])
        assert_allclose(s1.lat.value, [5,6])

    def test_readonly(self):

        s1 = UnitSphericalRepresentation(lon=[8*u.hourangle, 135*u.deg],
                                     lat=[5*u.deg, (6*np.pi/180)*u.rad])

        with pytest.raises(AttributeError):
            s1.lon = 1. * u.deg

        with pytest.raises(AttributeError):
            s1.lat = 1. * u.deg

    def test_getitem(self):

        s = UnitSphericalRepresentation(lon=np.arange(10) * u.deg,
                                        lat=-np.arange(10) * u.deg)

        s_slc = s[2:8:2]

        assert_allclose_quantity(s_slc.lon, [2,4,6] * u.deg)
        assert_allclose_quantity(s_slc.lat, [-2,-4,-6] * u.deg)

    def test_getitem_scalar(self):

        s = UnitSphericalRepresentation(lon=1 * u.deg,
                                        lat=-2 * u.deg)

        with pytest.raises(TypeError):
            s_slc = s[0]


class TestPhysicsSphericalRepresentation(object):

    def test_empty_init(self):
        with pytest.raises(TypeError) as exc:
            s = PhysicsSphericalRepresentation()

    def test_init_quantity(self):

        s3 = PhysicsSphericalRepresentation(phi=8 * u.hourangle, theta=5 * u.deg, r=10 * u.kpc)
        assert s3.phi == 8. * u.hourangle
        assert s3.theta == 5. * u.deg
        assert s3.r == 10 * u.kpc

        assert isinstance(s3.phi, Angle)
        assert isinstance(s3.theta, Angle)
        assert isinstance(s3.r, Distance)

    def test_init_phitheta(self):

        s2 = PhysicsSphericalRepresentation(Angle(8, u.hour),
                                     Angle(5, u.deg),
                                     Distance(10, u.kpc))

        assert s2.phi == 8. * u.hourangle
        assert s2.theta == 5. * u.deg
        assert s2.r == 10. * u.kpc

        assert isinstance(s2.phi, Angle)
        assert isinstance(s2.theta, Angle)
        assert isinstance(s2.r, Distance)

    def test_init_array(self):

        s1 = PhysicsSphericalRepresentation(phi=[8, 9] * u.hourangle,
                                     theta=[5, 6] * u.deg,
                                     r=[1,2] * u.kpc)

        assert_allclose(s1.phi.degree, [120, 135])
        assert_allclose(s1.theta.degree, [5, 6])
        assert_allclose(s1.r.kpc, [1, 2])

        assert isinstance(s1.phi, Angle)
        assert isinstance(s1.theta, Angle)
        assert isinstance(s1.r, Distance)

    def test_init_array_nocopy(self):

        phi = Angle([8, 9] * u.hourangle)
        theta = Angle([5, 6] * u.deg)
        r = Distance([1, 2] * u.kpc)

        s1 = PhysicsSphericalRepresentation(phi=phi, theta=theta, r=r, copy=False)

        phi[:] = [1,2] * u.rad
        theta[:] = [3,4] * u.arcmin
        r[:] = [8,9] * u.Mpc

        assert_allclose_quantity(phi, s1.phi)
        assert_allclose_quantity(theta, s1.theta)
        assert_allclose_quantity(r, s1.r)

    def test_init_str(self):

        s1 = PhysicsSphericalRepresentation(phi='2h6m3.3s', theta='0.1rad', r=1 * u.kpc)
        assert_allclose(s1.phi.degree, 31.513749999999995)
        assert_allclose(s1.theta.degree, 5.729577951308233)
        assert_allclose(s1.r.kpc, 1.)

    def test_reprobj(self):

        s1 = PhysicsSphericalRepresentation(phi=8 * u.hourangle, theta=5 * u.deg, r=10 * u.kpc)

        s2 = PhysicsSphericalRepresentation.from_representation(s1)

        assert_allclose_quantity(s2.phi, 8. * u.hourangle)
        assert_allclose_quantity(s2.theta, 5. * u.deg)
        assert_allclose_quantity(s2.r, 10 * u.kpc)

    def test_broadcasting(self):

        s1 = PhysicsSphericalRepresentation(phi=[8, 9]*u.hourangle,
                                     theta=[5, 6]*u.deg,
                                     r=10*u.kpc)

        assert_allclose_quantity(s1.phi, [120, 135] * u.degree)
        assert_allclose_quantity(s1.theta, [5, 6] * u.degree)
        assert_allclose_quantity(s1.r, [10, 10] * u.kpc)

    def test_broadcasting_mismatch(self):

        with pytest.raises(ValueError) as exc:
            s1 = PhysicsSphericalRepresentation(phi=[8, 9, 10]*u.hourangle,
                                         theta=[5, 6]*u.deg,
                                         r=[1, 2] * u.kpc)
        assert exc.value.args[0] == "Input parameters phi, theta, and r cannot be broadcast"

    def test_mixed_units(self):

        # It's also possible to pass in scalar quantity lists with mixed
        # units. These are converted to array quantities following the same
        # rule as `Quantity`: all elements are converted to match the first
        # element's units.

        s1 = PhysicsSphericalRepresentation(phi=[8*u.hourangle, 135*u.deg],
                                     theta=[5*u.deg, (6*np.pi/180)*u.rad],
                                     r=[1.*u.kpc, 500*u.pc])
        assert s1.phi.unit == u.hourangle
        assert s1.theta.unit == u.deg
        assert s1.r.unit == u.kpc
        assert_allclose(s1.phi.value, [8,9])
        assert_allclose(s1.theta.value, [5,6])
        assert_allclose(s1.r.value, [1,0.5])

    def test_readonly(self):

        s1 = PhysicsSphericalRepresentation(phi=[8*u.hourangle, 135*u.deg],
                                     theta=[5*u.deg, (6*np.pi/180)*u.rad],
                                     r=[1.*u.kpc, 500*u.pc])

        with pytest.raises(AttributeError):
            s1.phi = 1. * u.deg

        with pytest.raises(AttributeError):
            s1.theta = 1. * u.deg

        with pytest.raises(AttributeError):
            s1.r = 1. * u.kpc

    def test_getitem(self):

        s = PhysicsSphericalRepresentation(phi=np.arange(10) * u.deg,
                                    theta=-np.arange(10) * u.deg,
                                    r=1 * u.kpc)

        s_slc = s[2:8:2]

        assert_allclose_quantity(s_slc.phi, [2,4,6] * u.deg)
        assert_allclose_quantity(s_slc.theta, [-2,-4,-6] * u.deg)
        assert_allclose_quantity(s_slc.r, [1,1,1] * u.kpc)

    def test_getitem_scalar(self):

        s = PhysicsSphericalRepresentation(phi=1 * u.deg,
                                    theta=-2 * u.deg,
                                    r=3 * u.kpc)

        with pytest.raises(TypeError):
            s_slc = s[0]


class TestCartesianRepresentation(object):

    def test_empty_init(self):
        with pytest.raises(TypeError) as exc:
            s = CartesianRepresentation()

    def test_init_quantity(self):

        s1 = CartesianRepresentation(x=1 * u.kpc, y=2 * u.kpc, z=3 * u.kpc)

        assert s1.x.unit is u.kpc
        assert s1.y.unit is u.kpc
        assert s1.z.unit is u.kpc

        assert_allclose(s1.x.value,1)
        assert_allclose(s1.y.value,2)
        assert_allclose(s1.z.value,3)

    def test_init_singleunit(self):

        s1 = CartesianRepresentation(x=1,y=2,z=3,unit=u.kpc)

        assert s1.x.unit is u.kpc
        assert s1.y.unit is u.kpc
        assert s1.z.unit is u.kpc

        assert_allclose(s1.x.value,1)
        assert_allclose(s1.y.value,2)
        assert_allclose(s1.z.value,3)

    def test_init_override_unit(self):

        s1 = CartesianRepresentation(x=1 * u.pc,y=2 * u.Mpc,z=3 * u.kpc,unit=u.kpc)

        assert s1.x.unit is u.kpc
        assert s1.y.unit is u.kpc
        assert s1.z.unit is u.kpc

        assert_allclose(s1.x.value,0.001)
        assert_allclose(s1.y.value,2000)
        assert_allclose(s1.z.value,3)

    def test_init_array(self):

        s1 = CartesianRepresentation(x=[1,2,3] * u.pc,
                                     y=[2,3,4]* u.Mpc,
                                     z=[3,4,5] * u.kpc)

        assert s1.x.unit is u.pc
        assert s1.y.unit is u.Mpc
        assert s1.z.unit is u.kpc

        assert_allclose(s1.x.value,[1,2,3])
        assert_allclose(s1.y.value,[2,3,4])
        assert_allclose(s1.z.value,[3,4,5])

    def test_init_one_array(self):

        s1 = CartesianRepresentation(x=[1,2,3] * u.pc)

        assert s1.x.unit is u.pc
        assert s1.y.unit is u.pc
        assert s1.z.unit is u.pc

        assert_allclose(s1.x.value,1)
        assert_allclose(s1.y.value,2)
        assert_allclose(s1.z.value,3)

    def test_init_one_array_size_fail(self):

        with pytest.raises(ValueError) as exc:
            s1 = CartesianRepresentation(x=[1,2,3,4] * u.pc)

        # exception text differs on Python 2 and Python 3
        assert exc.value.args[0].startswith("too many values to unpack")

    def test_init_one_array_yz_fail(self):

        with pytest.raises(ValueError) as exc:
            s1 = CartesianRepresentation(x=[1,2,3,4] * u.pc, y=[1,2]* u.pc)

        assert exc.value.args[0] == "x, y, and z are required to instantiate CartesianRepresentation"

    def test_init_array_nocopy(self):

        x = [8, 9, 10] * u.pc
        y = [5, 6, 7] * u.Mpc
        z = [2, 3, 4] * u.kpc

        s1 = CartesianRepresentation(x=x, y=y, z=z, copy=False)

        x[:] = [1,2,3] * u.kpc
        y[:] = [9,9,8] * u.kpc
        z[:] = [1,2,1] * u.kpc

        assert_allclose_quantity(x, s1.x)
        assert_allclose_quantity(y, s1.y)
        assert_allclose_quantity(z, s1.z)

    def test_reprobj(self):

        s1 = CartesianRepresentation(x=1 * u.kpc, y=2 * u.kpc, z=3 * u.kpc)

        s2 = CartesianRepresentation.from_representation(s1)

        assert s2.x == 1 * u.kpc
        assert s2.y == 2 * u.kpc
        assert s2.z == 3 * u.kpc

    def test_broadcasting(self):

        s1 = CartesianRepresentation(x=[1,2] * u.kpc, y=[3,4] * u.kpc, z=5 * u.kpc)

        assert s1.x.unit == u.kpc
        assert s1.y.unit == u.kpc
        assert s1.z.unit == u.kpc

        assert_allclose(s1.x.value, [1, 2])
        assert_allclose(s1.y.value, [3, 4])
        assert_allclose(s1.z.value, [5, 5])

    def test_broadcasting_mismatch(self):

        with pytest.raises(ValueError) as exc:
            s1 = CartesianRepresentation(x=[1,2] * u.kpc, y=[3,4] * u.kpc, z=[5,6,7] * u.kpc)
        assert exc.value.args[0] == "Input parameters x, y, and z cannot be broadcast"

    def test_mixed_units(self):

        # It's also possible to pass in scalar quantity lists with mixed
        # units. These are converted to array quantities following the same
        # rule as `Quantity`: all elements are converted to match the first
        # element's units.

        s1 = CartesianRepresentation(x=[1 * u.kpc,2 * u.Mpc],
                                     y=[3 * u.kpc, 4 * u.pc] ,
                                     z=[5. * u.cm, 6 * u.m])

        assert s1.x.unit == u.kpc
        assert s1.y.unit == u.kpc
        assert s1.z.unit == u.cm
        assert_allclose(s1.x.value, [1, 2000])
        assert_allclose(s1.y.value, [3, 0.004])
        assert_allclose(s1.z.value, [5, 600])

    def test_readonly(self):

        s1 = CartesianRepresentation(x=1 * u.kpc, y=2 * u.kpc, z=3 * u.kpc)

        with pytest.raises(AttributeError):
            s1.x = 1. * u.kpc

        with pytest.raises(AttributeError):
            s1.y = 1. * u.kpc

        with pytest.raises(AttributeError):
            s1.z = 1. * u.kpc

    def test_xyz(self):

        s1 = CartesianRepresentation(x=1,y=2,z=3,unit=u.kpc)

        assert isinstance(s1.xyz, u.Quantity)
        assert s1.xyz.unit is u.kpc

        assert_allclose(s1.xyz.value,[1,2,3])

    def test_unit_mismatch(self):

        q_len = u.Quantity([1], u.km)
        q_nonlen = u.Quantity([1], u.kg)

        with pytest.raises(u.UnitsError) as exc:
            s1 = CartesianRepresentation(x=q_nonlen, y=q_len, z=q_len)
        assert exc.value.args[0] == "x, y, and z should have matching physical types"

        with pytest.raises(u.UnitsError) as exc:
            s1 = CartesianRepresentation(x=q_len, y=q_nonlen, z=q_len)
        assert exc.value.args[0] == "x, y, and z should have matching physical types"

        with pytest.raises(u.UnitsError) as exc:
            s1 = CartesianRepresentation(x=q_len, y=q_len, z=q_nonlen)
        assert exc.value.args[0] == "x, y, and z should have matching physical types"

    def test_unit_non_length(self):

        s1 = CartesianRepresentation(x=1, y=2, z=3, unit=u.kg)

        s2 = CartesianRepresentation(x=1, y=2, z=3, unit=u.km / u.s)

        s3 = CartesianRepresentation(x=1, y=2, z=3, unit=u.def_unit('banana'))


    def test_getitem(self):

        s = CartesianRepresentation(x=np.arange(10) * u.m,
                                    y=-np.arange(10) * u.m,
                                    z=3 * u.km)

        s_slc = s[2:8:2]

        assert_allclose_quantity(s_slc.x, [2,4,6] * u.m)
        assert_allclose_quantity(s_slc.y, [-2,-4,-6] * u.m)
        assert_allclose_quantity(s_slc.z, [3,3,3] * u.km)

    def test_getitem_scalar(self):

        s = CartesianRepresentation(x=1 * u.m,
                                    y=-2 * u.m,
                                    z=3 * u.km)

        with pytest.raises(TypeError):
            s_slc = s[0]


class TestCylindricalRepresentation(object):

    def test_empty_init(self):
        with pytest.raises(TypeError) as exc:
            s = CylindricalRepresentation()

    def test_init_quantity(self):

        s1 = CylindricalRepresentation(rho=1 * u.kpc, phi=2 * u.deg, z=3 * u.kpc)

        assert s1.rho.unit is u.kpc
        assert s1.phi.unit is u.deg
        assert s1.z.unit is u.kpc

        assert_allclose(s1.rho.value,1)
        assert_allclose(s1.phi.value,2)
        assert_allclose(s1.z.value,3)

    def test_init_array(self):

        s1 = CylindricalRepresentation(rho=[1,2,3] * u.pc,
                                     phi=[2,3,4]* u.deg,
                                     z=[3,4,5] * u.kpc)

        assert s1.rho.unit is u.pc
        assert s1.phi.unit is u.deg
        assert s1.z.unit is u.kpc

        assert_allclose(s1.rho.value,[1,2,3])
        assert_allclose(s1.phi.value,[2,3,4])
        assert_allclose(s1.z.value,[3,4,5])

    def test_init_array_nocopy(self):

        rho = [8, 9, 10] * u.pc
        phi = [5, 6, 7] * u.deg
        z = [2, 3, 4] * u.kpc

        s1 = CylindricalRepresentation(rho=rho, phi=phi, z=z, copy=False)

        rho[:] = [9,2,3] * u.kpc
        phi[:] = [1, 2, 3] * u.arcmin
        z[:] = [-2, 3, 8] * u.kpc

        assert_allclose_quantity(rho, s1.rho)
        assert_allclose_quantity(phi, s1.phi)
        assert_allclose_quantity(z, s1.z)

    def test_reprobj(self):

        s1 = CylindricalRepresentation(rho=1 * u.kpc, phi=2 * u.deg, z=3 * u.kpc)

        s2 = CylindricalRepresentation.from_representation(s1)

        assert s2.rho == 1 * u.kpc
        assert s2.phi == 2 * u.deg
        assert s2.z == 3 * u.kpc

    def test_broadcasting(self):

        s1 = CylindricalRepresentation(rho=[1,2] * u.kpc, phi=[3,4] * u.deg, z=5 * u.kpc)

        assert s1.rho.unit == u.kpc
        assert s1.phi.unit == u.deg
        assert s1.z.unit == u.kpc

        assert_allclose(s1.rho.value, [1, 2])
        assert_allclose(s1.phi.value, [3, 4])
        assert_allclose(s1.z.value, [5, 5])

    def test_broadcasting_mismatch(self):

        with pytest.raises(ValueError) as exc:
            s1 = CylindricalRepresentation(rho=[1,2] * u.kpc, phi=[3,4] * u.deg, z=[5,6,7] * u.kpc)
        assert exc.value.args[0] == "Input parameters rho, phi, and z cannot be broadcast"

    def test_mixed_units(self):

        # It's also possible to pass in scalar quantity lists with mixed
        # units. These are converted to array quantities following the same
        # rule as `Quantity`: all elements are converted to match the first
        # element's units.

        s1 = CylindricalRepresentation(rho=[1 * u.kpc,2 * u.Mpc],
                                     phi=[3 * u.deg, 4 * u.arcmin] ,
                                     z=[5. * u.cm, 6 * u.m])

        assert s1.rho.unit == u.kpc
        assert s1.phi.unit == u.deg
        assert s1.z.unit == u.cm
        assert_allclose(s1.rho.value, [1, 2000])
        assert_allclose(s1.phi.value, [3, 4./60.])
        assert_allclose(s1.z.value, [5, 600])

    def test_readonly(self):

        s1 = CylindricalRepresentation(rho=1 * u.kpc, phi=20 * u.deg, z=3 * u.kpc)

        with pytest.raises(AttributeError):
            s1.rho = 1. * u.kpc

        with pytest.raises(AttributeError):
            s1.phi = 20 * u.deg

        with pytest.raises(AttributeError):
            s1.z = 1. * u.kpc

    def unit_mismatch(self):

        q_len = u.Quantity([1], u.kpc)
        q_nonlen = u.Quantity([1], u.kg)

        with pytest.raises(u.UnitsError) as exc:
            s1 = CylindricalRepresentation(rho=q_nonlen, phi=10*u.deg, z=q_len)
        assert exc.value.args[0] == "rho and z should have matching physical types"

        with pytest.raises(u.UnitsError) as exc:
            s1 = CylindricalRepresentation(rho=q_len, phi=10*u.deg, z=q_nonlen)
        assert exc.value.args[0] == "rho and z should have matching physical types"

    def test_getitem(self):

        s = CylindricalRepresentation(rho=np.arange(10) * u.pc,
                                      phi=-np.arange(10) * u.deg,
                                      z=1 * u.kpc)

        s_slc = s[2:8:2]

        assert_allclose_quantity(s_slc.rho, [2,4,6] * u.pc)
        assert_allclose_quantity(s_slc.phi, [-2,-4,-6] * u.deg)
        assert_allclose_quantity(s_slc.z, [1,1,1] * u.kpc)

    def test_getitem_scalar(self):

        s = CylindricalRepresentation(rho=1 * u.pc,
                                      phi=-2 * u.deg,
                                      z=3 * u.kpc)

        with pytest.raises(TypeError):
            s_slc = s[0]

def test_cartesian_spherical_roundtrip():

    s1 = CartesianRepresentation(x=[1 * u.kpc,2 * u.Mpc],
                                 y=[3 * u.kpc, 4 * u.pc] ,
                                 z=[5. * u.cm, 6 * u.m])

    s2 = SphericalRepresentation.from_representation(s1)

    s3 = CartesianRepresentation.from_representation(s2)

    s4 = SphericalRepresentation.from_representation(s3)

    assert_allclose_quantity(s1.x, s3.x)
    assert_allclose_quantity(s1.y, s3.y)
    assert_allclose_quantity(s1.z, s3.z)

    assert_allclose_quantity(s2.lon, s4.lon)
    assert_allclose_quantity(s2.lat, s4.lat)
    assert_allclose_quantity(s2.distance, s4.distance)


def test_cartesian_physics_spherical_roundtrip():

    s1 = CartesianRepresentation(x=[1 * u.kpc,2 * u.Mpc],
                                 y=[3 * u.kpc, 4 * u.pc] ,
                                 z=[5. * u.pc, 6 * u.kpc])

    s2 = PhysicsSphericalRepresentation.from_representation(s1)

    s3 = CartesianRepresentation.from_representation(s2)

    s4 = PhysicsSphericalRepresentation.from_representation(s3)

    assert_allclose_quantity(s1.x, s3.x)
    assert_allclose_quantity(s1.y, s3.y)
    assert_allclose_quantity(s1.z, s3.z)

    assert_allclose_quantity(s2.phi, s4.phi)
    assert_allclose_quantity(s2.theta, s4.theta)
    assert_allclose_quantity(s2.r, s4.r)


def test_spherical_physics_spherical_roundtrip():

    s1 = SphericalRepresentation(lon=3 * u.deg, lat=4 * u.deg, distance=3 * u.kpc)

    s2 = PhysicsSphericalRepresentation.from_representation(s1)

    s3 = SphericalRepresentation.from_representation(s2)

    s4 = PhysicsSphericalRepresentation.from_representation(s3)

    assert_allclose_quantity(s1.lon, s3.lon)
    assert_allclose_quantity(s1.lat, s3.lat)
    assert_allclose_quantity(s1.distance, s3.distance)

    assert_allclose_quantity(s2.phi, s4.phi)
    assert_allclose_quantity(s2.theta, s4.theta)
    assert_allclose_quantity(s2.r, s4.r)

    assert_allclose_quantity(s1.lon, s4.phi)
    assert_allclose_quantity(s1.lat, 90. * u.deg - s4.theta)
    assert_allclose_quantity(s1.distance, s4.r)


def test_cartesian_cylindrical_roundtrip():

    s1 = CartesianRepresentation(x=[1 * u.kpc,2 * u.Mpc],
                                 y=[3 * u.kpc, 4 * u.pc] ,
                                 z=[5. * u.cm, 6 * u.m])

    s2 = CylindricalRepresentation.from_representation(s1)

    s3 = CartesianRepresentation.from_representation(s2)

    s4 = CylindricalRepresentation.from_representation(s3)

    assert_allclose_quantity(s1.x, s3.x)
    assert_allclose_quantity(s1.y, s3.y)
    assert_allclose_quantity(s1.z, s3.z)

    assert_allclose_quantity(s2.rho, s4.rho)
    assert_allclose_quantity(s2.phi, s4.phi)
    assert_allclose_quantity(s2.z, s4.z)


def test_unit_spherical_roundtrip():

    s1 = UnitSphericalRepresentation(lon=[10. * u.deg, 30 * u.deg],
                                     lat=[5. * u.arcmin, 6. * u.arcmin])

    s2 = CartesianRepresentation.from_representation(s1)

    s3 = SphericalRepresentation.from_representation(s2)

    s4 = UnitSphericalRepresentation.from_representation(s3)

    assert_allclose_quantity(s1.lon, s4.lon)
    assert_allclose_quantity(s1.lat, s4.lat)
