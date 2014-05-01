# -*- coding: utf-8 -*-
# Licensed under a 3-clause BSD style license - see LICENSE.rst

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import functools

import numpy as np

from ... import units as u
from ...tests.helper import pytest
from ...coordinates import (ICRS, FK4, FK5, FK4NoETerms, Galactic, SkyCoord, Angle,
                            SphericalRepresentation, CartesianRepresentation)
from ...time import Time

RA = 1.0 * u.deg
DEC = 2.0 * u.deg
C_ICRS = ICRS(RA, DEC)
C_FK5 = C_ICRS.transform_to(FK5)
J2001 = Time('J2001', scale='utc')

allclose = functools.partial(np.allclose, rtol=0.0, atol=1e-8)


def test_transform_to():
    for frame in (FK5, FK5(equinox=Time('J1975.0')),
                  FK4, FK4(equinox=Time('J1975.0'))):
        c_frame = C_ICRS.transform_to(frame)
        s_icrs = SkyCoord(RA, DEC, frame='icrs')
        s_frame = s_icrs.transform_to(frame)
        assert allclose(c_frame.ra, s_frame.ra)
        assert allclose(c_frame.dec, s_frame.dec)
        assert allclose(c_frame.distance, s_frame.distance)


def test_round_tripping():
    """
    Test round tripping out and back using transform_to in every combination.
    """
    frames = [ICRS, FK4, FK5, FK4NoETerms, Galactic]
    attrs0 = {}
    attrs1 = {}
    for frame_cls0 in frames:
        for frame_cls1 in frames:
            for equinox0 in (None, 'J1975.0'):
                attrs0['equinox'] = equinox0

                for obstime0 in (None, 'J1980.0'):
                    attrs0['obstime'] = obstime0

                    for equinox1 in (None, 'J1975.0'):
                        attrs1['equinox'] = equinox1

                        for obstime1 in (None, 'J1980.0'):
                            attrs1['obstime'] = obstime1

                            # Remove None values
                            attrs0 = dict((k, v) for k, v in attrs0.items() if v is not None)
                            attrs1 = dict((k, v) for k, v in attrs1.items() if v is not None)

                            print(attrs0, equinox0, obstime0, frame_cls0)
                            # Go out and back
                            sc = SkyCoord(frame_cls0, RA, DEC, **attrs0)

                            # Keep only frame attributes for frame1
                            attrs1 = dict((attr, val) for attr, val in attrs1.items()
                                          if attr in frame_cls1.frame_attr_names)
                            sc2 = sc.transform_to(frame_cls1(**attrs1))

                            # When coming back only keep frame0 attributes for transform_to
                            attrs0 = dict((attr, val) for attr, val in attrs0.items()
                                          if attr in frame_cls0.frame_attr_names)
                            sc_rt = sc2.transform_to(frame_cls0(**attrs0))

                            if frame_cls0 is Galactic:
                                assert allclose(sc.l, sc_rt.l)
                                assert allclose(sc.b, sc_rt.b)
                            else:
                                assert allclose(sc.ra, sc_rt.ra)
                                assert allclose(sc.dec, sc_rt.dec)
                            if equinox0:
                                assert Time(sc.equinox) == Time(sc_rt.equinox)
                            if obstime0:
                                assert Time(sc.obstime) == Time(sc_rt.obstime)




def test_coord_init_string():
    """
    Spherical or Cartesian represenation input coordinates.
    """
    sc = SkyCoord('1d 2d')
    assert allclose(sc.ra, 1 * u.deg)
    assert allclose(sc.dec, 2 * u.deg)

    sc = SkyCoord('1d', '2d')
    assert allclose(sc.ra, 1 * u.deg)
    assert allclose(sc.dec, 2 * u.deg)

    sc = SkyCoord(u'1°2′3″', u'2°3′4″')
    assert allclose(sc.ra, Angle(u'1°2′3″'))
    assert allclose(sc.dec, Angle(u'2°3′4″'))

    sc = SkyCoord(u'1°2′3″ 2°3′4″')
    assert allclose(sc.ra, Angle(u'1°2′3″'))
    assert allclose(sc.dec, Angle(u'2°3′4″'))

    with pytest.raises(ValueError) as err:
        SkyCoord('1d 2d 3d')
    assert "Cannot parse longitude and latitude" in str(err)


def test_coord_init_list():
    """
    Spherical or Cartesian representation input coordinates.
    """
    sc = SkyCoord([('1d', '2d'),
                   (1 * u.deg, 2 * u.deg),
                   '1d 2d',
                   (u'1°', u'2°'),
                   u'1° 2°'], unit='deg')
    assert allclose(sc.ra, Angle('1d'))
    assert allclose(sc.dec, Angle('2d'))

    with pytest.raises(ValueError) as err:
        SkyCoord(['1d 2d 3d'])
    assert "Cannot parse longitude and latitude" in str(err)

    with pytest.raises(ValueError) as err:
        SkyCoord([('1d', '2d', '3d')])
    assert "Cannot parse longitude and latitude" in str(err)

    sc = SkyCoord([1 * u.deg, 1 * u.deg], [2 * u.deg, 2 * u.deg])
    assert allclose(sc.ra, Angle('1d'))
    assert allclose(sc.dec, Angle('2d'))

    with pytest.raises(ValueError) as err:
        SkyCoord([1 * u.deg, 2 * u.deg])  # this list is taken as RA w/ missing dec
    assert "Cannot parse longitude and latitude" in str(err)


def test_coord_init_representation():
    """
    Spherical or Cartesian represenation input coordinates.
    """
    coord = SphericalRepresentation(lon=8 * u.deg, lat=5 * u.deg, distance=1 * u.kpc)
    sc = SkyCoord(coord, 'icrs')
    assert allclose(sc.ra, coord.lon)
    assert allclose(sc.dec, coord.lat)
    assert allclose(sc.distance, coord.distance)

    with pytest.raises(ValueError) as err:
        SkyCoord(coord, 'icrs', ra='1d')
    assert "conflicts with keyword argument 'ra'" in str(err)

    coord = CartesianRepresentation(1, 2, 3)
    sc = SkyCoord(coord, 'icrs')
    sc_cart = sc.represent_as(CartesianRepresentation)
    assert allclose(sc_cart.x, 1.0)
    assert allclose(sc_cart.y, 2.0)
    assert allclose(sc_cart.z, 3.0)


def test_frame_init():
    """
    Different ways of providing the frame.
    """
    sc = SkyCoord(RA, DEC, frame='icrs')
    assert sc.frame == 'icrs'

    sc = SkyCoord(RA, DEC, frame=ICRS)
    assert sc.frame == 'icrs'

    sc = SkyCoord(RA, DEC, 'icrs')
    assert sc.frame == 'icrs'

    sc = SkyCoord(RA, DEC, ICRS)
    assert sc.frame == 'icrs'

    sc = SkyCoord('icrs', RA, DEC)
    assert sc.frame == 'icrs'

    sc = SkyCoord(ICRS, RA, DEC)
    assert sc.frame == 'icrs'

    sc = SkyCoord(sc)
    assert sc.frame == 'icrs'

    sc = SkyCoord(C_ICRS)
    assert sc.frame == 'icrs'

    SkyCoord(C_ICRS, frame='icrs')
    assert sc.frame == 'icrs'

    with pytest.raises(ValueError) as err:
        SkyCoord(C_ICRS, frame='galactic')
    assert 'Cannot override frame=' in str(err)


def test_attr_inheritance():
    """
    When initializing from an existing coord the preferred attrs like
    equinox should be inherited to the SkyCoord.  If there is a conflict
    then raise an exception.
    """
    sc = SkyCoord('icrs', 1, 2, unit='deg', equinox='J1999', obstime='J2001')
    sc2 = SkyCoord(sc)
    assert sc2.equinox == sc.equinox
    assert sc2.obstime == sc.obstime
    assert allclose(sc2.ra, sc.ra)
    assert allclose(sc2.dec, sc.dec)
    assert allclose(sc2.distance, sc.distance)

    sc2 = SkyCoord(sc._coord)  # Doesn't have equinox there so we get FK4 defaults
    assert sc2.equinox != sc.equinox
    assert sc2.obstime != sc.obstime
    assert allclose(sc2.ra, sc.ra)
    assert allclose(sc2.dec, sc.dec)
    assert allclose(sc2.distance, sc.distance)

    sc = SkyCoord('fk4', 1, 2, unit='deg', equinox='J1999', obstime='J2001')
    sc2 = SkyCoord(sc)
    assert sc2.equinox == sc.equinox
    assert sc2.obstime == sc.obstime
    assert allclose(sc2.ra, sc.ra)
    assert allclose(sc2.dec, sc.dec)
    assert allclose(sc2.distance, sc.distance)

    sc2 = SkyCoord(sc._coord)  # sc._coord has equinox, obstime
    assert sc2.equinox == sc.equinox
    assert sc2.obstime == sc.obstime
    assert allclose(sc2.ra, sc.ra)
    assert allclose(sc2.dec, sc.dec)
    assert allclose(sc2.distance, sc.distance)


def test_attr_conflicts():
    """
    Check conflicts resolution between coordinate attributes and init kwargs.
    """
    sc = SkyCoord('icrs', 1, 2, unit='deg', equinox='J1999', obstime='J2001')

    # OK if attrs both specified but with identical values
    SkyCoord(sc, equinox='J1999', obstime='J2001')

    # OK because sc._coord doesn't have obstime
    SkyCoord(sc._coord, equinox='J1999', obstime='J2100')

    # Not OK if attrs don't match
    with pytest.raises(ValueError) as err:
        SkyCoord(sc, equinox='J1999', obstime='J2002')
    assert "Coordinate attribute 'obstime'=" in str(err)

    # Same game but with fk4 which has equinox and obstime frame attrs
    sc = SkyCoord('fk4', 1, 2, unit='deg', equinox='J1999', obstime='J2001')

    # OK if attrs both specified but with identical values
    SkyCoord(sc, equinox='J1999', obstime='J2001')

    # Not OK if SkyCoord attrs don't match
    with pytest.raises(ValueError) as err:
        SkyCoord(sc, equinox='J1999', obstime='J2002')
    assert "Coordinate attribute 'obstime'=" in str(err)

    # Not OK because sc._coord has different attrs
    with pytest.raises(ValueError) as err:
        SkyCoord(sc._coord, equinox='J1999', obstime='J2002')
    assert "Coordinate attribute 'obstime'=" in str(err)


def test_frame_attr_getattr():
    """
    When accessing frame attributes like equinox, the value should come
    from self._coord when that object has the relevant attribute, otherwise
    from self.
    """
    sc = SkyCoord('icrs', 1, 2, unit='deg', equinox='J1999', obstime='J2001')
    assert sc.equinox == 'J1999'  # Just the raw value (not validated)
    assert sc.obstime == 'J2001'

    sc = SkyCoord('fk4', 1, 2, unit='deg', equinox='J1999', obstime='J2001')
    assert sc.equinox == Time('J1999')  # Coming from the self._coord object
    assert sc.obstime == Time('J2001')

    sc = SkyCoord('fk4', 1, 2, unit='deg', equinox='J1999')
    assert sc.equinox == Time('J1999')
    assert sc.obstime == Time('J1999')


def test_api():
    """
    Verify that the API take-2 examples run
    """

    sc = SkyCoord(SphericalRepresentation(lon=8 * u.hour, lat=5 * u.deg, distance=1 * u.kpc),
                  frame='icrs')

    sc = SkyCoord(ra=8 * u.hour, dec=5 * u.deg, frame='icrs')
    sc = SkyCoord(l=120 * u.deg, b=5 * u.deg, frame='galactic')

    # High-level classes can also be initialized directly from low-level objects
    sc = SkyCoord(ICRS(ra=8 * u.hour, dec=5 * u.deg))

    # The next example raises an error because the high-level class must always
    # have position data.
    with pytest.raises(ValueError):
        sc = SkyCoord(FK5(equinox=J2001))  # raises ValueError

    # similarly, the low-level object can always be accessed

    # NOT YET.  NEVER?
    # assert str(sc.frame) == '<ICRS RA=120.000 deg, Dec=5.00000 deg>'

    # Supports a variety of possible complex string formats
    sc = SkyCoord('8h00m00s +5d00m00.0s', frame='icrs')

    # In the next example, the unit is only needed b/c units are ambiguous.  In
    # general, we *never* accept ambiguity
    sc = SkyCoord('8:00:00 +5:00:00.0', unit=(u.hour, u.deg), frame='icrs')

    # The next one would yield length-2 array coordinates, because of the comma

    sc = SkyCoord(['8h 5d', '2°2′3″ 0.3rad'], frame='icrs')

    # It should also interpret common designation styles as a coordinate
    # NOT YET
    # sc = SkyCoord('SDSS J123456.89-012345.6', frame='icrs')

    # the string representation can be inherited from the low-level class.

    # NOT YET
    # assert str(sc) == '<SkyCoord (ICRS) RA=120.000 deg, Dec=5.00000 deg>'

    # but it should also be possible to provide formats for outputting to strings,
    # similar to `Time`.  This can be added right away or at a later date.

    # transformation is done the same as for low-level classes, which it delegates to

    sc_fk5_j2001 = sc.transform_to(FK5(equinox=J2001))
    assert sc_fk5_j2001.equinox == J2001

    # The key difference is that the high-level class remembers frame information
    # necessary for round-tripping, unlike the low-level classes:
    sc1 = SkyCoord(ra=8 * u.hour, dec=5 * u.deg, equinox=J2001, frame='fk5')
    sc2 = sc1.transform_to('icrs')

    # The next assertion succeeds, but it doesn't mean anything for ICRS, as ICRS
    # isn't defined in terms of an equinox
    assert sc2.equinox == J2001

    # But it *is* necessary once we transform to FK5
    sc3 = sc2.transform_to('fk5')
    assert sc3.equinox == J2001
    assert allclose(sc1.ra, sc3.ra)

    # `SkyCoord` will also include the attribute-style access that is in the
    # v0.2/0.3 coordinate objects.  This will *not* be in the low-level classes
    sc = SkyCoord(ra=8 * u.hour, dec=5 * u.deg, frame='icrs')
    scgal = sc.galactic
    assert str(scgal).startswith('<Galactic SkyCoord: l=216.317')

    # the existing `from_name` and `match_to_catalog_*` methods will be moved to the
    # high-level class as convenience functionality.

    if False:
        m31icrs = SkyCoord.from_name('M31', frame='icrs')
        assert str(m31icrs) == '<SkyCoord (ICRS) RA=10.68471 deg, Dec=41.26875 deg>'

        cat1 = SkyCoord(ra=1 * u.hr, dec=2 * u.deg, distance=3 * u.kpc)
        cat2 = SkyCoord(ra=1 * u.hr, dec=2 * u.deg, distance=3 * u.kpc)
        idx2, sep2d, dist3d = cat1.match_to_catalog_sky(cat2)
        idx2, sep2d, dist3d = cat1.match_to_catalog_3d(cat2)

        # additional convenience functionality for the future should be added as methods
        # on `SkyCoord`, *not* the low-level classes.
