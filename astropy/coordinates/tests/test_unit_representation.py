"""
This file tests the behaviour of subclasses of Representation and Frames
"""

from astropy.utils.compat.odict import OrderedDict
from astropy.coordinates import Longitude, Latitude
from astropy.coordinates.representation import (SphericalRepresentation,
                                                UnitSphericalRepresentation)
from astropy.coordinates.baseframe import frame_transform_graph
from astropy.coordinates.transformations import FunctionTransform


import astropy.units as u

import astropy.coordinates

# Classes setup, borrowed from SunPy.


class Longitude180(Longitude):
    def __new__(cls, angle, unit=None, wrap_angle=180*u.deg, **kwargs):
        self = super(Longitude180, cls).__new__(cls, angle, unit=unit,
                                                wrap_angle=wrap_angle, **kwargs)
        return self


class UnitSphericalWrap180Representation(UnitSphericalRepresentation):
    attr_classes = OrderedDict([('lon', Longitude180),
                                ('lat', Latitude)])
    recommended_units = {'lon': u.deg, 'lat': u.deg}


class SphericalWrap180Representation(SphericalRepresentation):
    attr_classes = OrderedDict([('lon', Longitude180),
                                ('lat', Latitude),
                                ('distance', u.Quantity)])
    recommended_units = {'lon': u.deg, 'lat': u.deg}

    _unit_representation = UnitSphericalWrap180Representation


class myframe(astropy.coordinates.ICRS):
    default_representation = SphericalWrap180Representation


@frame_transform_graph.transform(FunctionTransform,
                                 myframe, astropy.coordinates.ICRS)
def myframe_to_icrs(myframe_coo, icrs):
    return icrs.realize_frame(myframe_coo._data)


def test_init():
    f = myframe(10*u.deg, 10*u.deg)
    assert isinstance(f._data, UnitSphericalWrap180Representation)
    assert isinstance(f.lon, Longitude180)


def test_transform():
    f = myframe(10*u.deg, 10*u.deg)
    g = f.transform_to(astropy.coordinates.ICRS)
    assert isinstance(g, astropy.coordinates.ICRS)
    assert isinstance(g._data, UnitSphericalWrap180Representation)
