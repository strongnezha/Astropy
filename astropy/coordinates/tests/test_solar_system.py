from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from ...time import Time
from ... import units as u
from ...constants import c
from ..builtin_frames import GCRS
from ..earth import EarthLocation
from ..sky_coordinate import SkyCoord
from ..solar_system import get_body, get_moon, _apparent_position_in_true_coordinates
from ...tests.helper import pytest, assert_quantity_allclose, remote_data

try:
    import jplephem  # pylint: disable=W0611
except ImportError:
    HAS_JPLEPHEM = False
else:
    HAS_JPLEPHEM = True

try:
    from skyfield.api import load  # pylint: disable=W0611
except ImportError:
    HAS_SKYFIELD = False
else:
    HAS_SKYFIELD = True

de430_separation_tolerance_planets = 5*u.arcsec
de430_separation_tolerance_moon = 5*u.arcsec
de430_distance_tolerance = 20*u.km

skyfield_angular_separation_tolerance = 1*u.arcsec
skyfield_separation_tolerance = 10*u.km


@remote_data
@pytest.mark.skipif(str('not HAS_SKYFIELD'))
def test_positions_skyfield():
    """
    Test positions against those generated by skyfield.
    """

    t = Time('1980-03-25 00:00')
    location = None

    # skyfield ephemeris
    planets = load('de421.bsp')
    ts = load.timescale()
    mercury, jupiter, moon = planets['mercury'], planets['jupiter barycenter'], planets['moon']
    earth = planets['earth']

    skyfield_t = ts.from_astropy(t)

    if location is not None:
        earth = earth.topos(latitude_degrees=location.latitude.to(u.deg).value,
                            longitude_degrees=location.longitude.to(u.deg).value,
                            elevation_m=location.height.to(u.m).value)

    skyfield_mercury = earth.at(skyfield_t).observe(mercury).apparent()
    skyfield_jupiter = earth.at(skyfield_t).observe(jupiter).apparent()
    skyfield_moon = earth.at(skyfield_t).observe(moon).apparent()

    if location is not None:
        obsgeoloc, obsgeovel = location.get_gcrs_posvel(t)
        frame = GCRS(obstime=t, obsgeoloc=obsgeoloc, obsgeovel=obsgeovel)
    else:
        frame = GCRS(obstime=t)

    ra, dec, dist = skyfield_mercury.radec(epoch='date')
    skyfield_mercury = SkyCoord(ra.to(u.deg), dec.to(u.deg), distance=dist.to(u.km),
                                frame=frame)
    ra, dec, dist = skyfield_jupiter.radec(epoch='date')
    skyfield_jupiter = SkyCoord(ra.to(u.deg), dec.to(u.deg), distance=dist.to(u.km),
                                frame=frame)
    ra, dec, dist = skyfield_moon.radec(epoch='date')
    skyfield_moon = SkyCoord(ra.to(u.deg), dec.to(u.deg), distance=dist.to(u.km),
                             frame=frame)

    moon_astropy = get_moon(t, location, ephemeris='de430')
    mercury_astropy = get_body('mercury', t, location, ephemeris='de430')
    jupiter_astropy = get_body('jupiter', t, location, ephemeris='de430')

    # convert to true equator and equinox
    jupiter_astropy = _apparent_position_in_true_coordinates(jupiter_astropy)
    mercury_astropy = _apparent_position_in_true_coordinates(mercury_astropy)
    moon_astropy = _apparent_position_in_true_coordinates(moon_astropy)

    assert (moon_astropy.separation(skyfield_moon) <
            skyfield_angular_separation_tolerance)
    assert (moon_astropy.separation_3d(skyfield_moon) < skyfield_separation_tolerance)

    assert (jupiter_astropy.separation(skyfield_jupiter) <
            skyfield_angular_separation_tolerance)
    assert (jupiter_astropy.separation_3d(skyfield_jupiter) <
            skyfield_separation_tolerance)

    assert (mercury_astropy.separation(skyfield_mercury) <
            skyfield_angular_separation_tolerance)
    assert (mercury_astropy.separation_3d(skyfield_mercury) <
            skyfield_separation_tolerance)



class TestPositionsGeocentric(object):
    """
    Test positions against those generated by JPL Horizons accessed on
    2016-03-28, with refraction turned on.
    """
    def setup(self):
        self.t = Time('1980-03-25 00:00')
        self.frame = GCRS(obstime=self.t)
        # Results returned by JPL Horizons web interface
        self.horizons = {
            'mercury': SkyCoord(ra='22h41m47.78s', dec='-08d29m32.0s',
                                distance=c*6.323037*u.min, frame=self.frame),
            'moon': SkyCoord(ra='07h32m02.62s', dec='+18d34m05.0s',
                             distance=c*0.021921*u.min, frame=self.frame),
            'jupiter':  SkyCoord(ra='10h17m12.82s', dec='+12d02m57.0s',
                                 distance=c*37.694557*u.min, frame=self.frame),
            'sun': SkyCoord(ra='00h16m31.00s', dec='+01d47m16.9s',
                            distance=c*8.294858*u.min, frame=self.frame)}

    @pytest.mark.parametrize(('body', 'sep_tol', 'dist_tol'),
                             (('mercury', 7.*u.arcsec, 1000*u.km),
                              ('jupiter', 78.*u.arcsec, 76000*u.km),
                              ('sun', 5.*u.arcsec, 11.*u.km)))
    def test_erfa_planet(self, body, sep_tol, dist_tol):
        """Test predictions using plan94.

        Accuracies are maximum deviations listed in erfa/plan94.c
        """
        astropy = get_body(body, self.t, ephemeris='erfa')
        horizons = self.horizons[body]

        # convert to true equator and equinox
        astropy = _apparent_position_in_true_coordinates(astropy)

        # Assert sky coordinates are close.
        assert astropy.separation(horizons) < sep_tol

        # Assert distances are close.
        assert_quantity_allclose(astropy.distance, horizons.distance,
                                 atol=dist_tol)

    @remote_data
    @pytest.mark.skipif('not HAS_JPLEPHEM')
    @pytest.mark.parametrize('body', ('mercury', 'jupiter', 'sun'))
    def test_de430_planet(self, body):
        astropy = get_body(body, self.t, ephemeris='de432s')
        horizons = self.horizons[body]

        # convert to true equator and equinox
        astropy = _apparent_position_in_true_coordinates(astropy)

        # Assert sky coordinates are close.
        assert (astropy.separation(horizons) <
                de430_separation_tolerance_planets)

        # Assert distances are close.
        assert_quantity_allclose(astropy.distance, horizons.distance,
                                 atol=de430_distance_tolerance)

    @remote_data
    @pytest.mark.skipif('not HAS_JPLEPHEM')
    def test_de430_moon(self):
        astropy = get_moon(self.t, ephemeris='de432s')
        horizons = self.horizons['moon']

        # convert to true equator and equinox
        astropy = _apparent_position_in_true_coordinates(astropy)

        # Assert sky coordinates are close.
        assert (astropy.separation(horizons) <
                de430_separation_tolerance_moon)

        # Assert distances are close.
        assert_quantity_allclose(astropy.distance, horizons.distance,
                                 atol=de430_distance_tolerance)



class TestPositionKittPeak(object):
    """
    Test positions against those generated by JPL Horizons accessed on
    2016-03-28, with refraction turned on.
    """

    def setup(self):
        kitt_peak = EarthLocation.from_geodetic(lon=-111.6*u.deg,
                                                lat=31.963333333333342*u.deg,
                                                height=2120*u.m)
        self.t = Time('2014-09-25T00:00', location=kitt_peak)
        obsgeoloc, obsgeovel = kitt_peak.get_gcrs_posvel(self.t)
        self.frame = GCRS(obstime=self.t,
                          obsgeoloc=obsgeoloc, obsgeovel=obsgeovel)
        # Results returned by JPL Horizons web interface
        self.horizons = {
            'mercury': SkyCoord(ra='13h38m58.50s', dec='-13d34m42.6s',
                                distance=c*7.699020*u.min, frame=self.frame),
            'moon': SkyCoord(ra='12h33m12.85s', dec='-05d17m54.4s',
                             distance=c*0.022054*u.min, frame=self.frame),
            'jupiter' : SkyCoord(ra='09h09m55.55s', dec='+16d51m57.8s',
                                 distance=c*49.244937*u.min, frame=self.frame)}

    @pytest.mark.parametrize(('body', 'sep_tol', 'dist_tol'),
                             (('mercury', 7.*u.arcsec, 500*u.km),
                              ('jupiter', 78.*u.arcsec, 82000*u.km)))
    def test_erfa_planet(self, body, sep_tol, dist_tol):
        """Test predictions using erfa/plan94.

        Accuracies are maximum deviations listed in erfa/plan94.c
        """
        # Add uncertainty in position of Earth
        dist_tol = dist_tol + 1300 * u.km

        astropy = get_body(body, self.t, ephemeris='erfa')
        horizons = self.horizons[body]

        # convert to true equator and equinox
        astropy = _apparent_position_in_true_coordinates(astropy)

        # Assert sky coordinates are close.
        assert astropy.separation(horizons) < sep_tol

        # Assert distances are close.
        assert_quantity_allclose(astropy.distance, horizons.distance,
                                 atol=dist_tol)

    @remote_data
    @pytest.mark.skipif('not HAS_JPLEPHEM')
    @pytest.mark.parametrize('body', ('mercury', 'jupiter'))
    def test_de430_planet(self, body):
        astropy = get_body(body, self.t, ephemeris='de432s')
        horizons = self.horizons[body]

        # convert to true equator and equinox
        astropy = _apparent_position_in_true_coordinates(astropy)

        # Assert sky coordinates are close.
        assert (astropy.separation(horizons) <
                de430_separation_tolerance_planets)

        # Assert distances are close.
        assert_quantity_allclose(astropy.distance, horizons.distance,
                                 atol=de430_distance_tolerance)

    @remote_data
    @pytest.mark.skipif('not HAS_JPLEPHEM')
    def test_de430_moon(self):
        astropy = get_moon(self.t, ephemeris='de432s')
        horizons = self.horizons['moon']

        # convert to true equator and equinox
        astropy = _apparent_position_in_true_coordinates(astropy)

        # Assert sky coordinates are close.
        assert (astropy.separation(horizons) <
                de430_separation_tolerance_moon)

        # Assert distances are close.
        assert_quantity_allclose(astropy.distance, horizons.distance,
                                 atol=de430_distance_tolerance)
