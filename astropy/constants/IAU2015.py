# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Astronomical and physics constants in SI units.  See :mod:`astropy.constants`
for a complete listing of constants defined in Astropy.
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import numpy as np

from .constant import Constant
import CODATA2014

# ASTRONOMICAL CONSTANTS

class Iau2015(Constant):
    default_reference = 'IAU 2015'

    def __new__(cls, abbrev, name, value, unit, uncertainty,
                reference=default_reference, system=None):
        super().__new__(cls, abbrev, name, value, unit, uncertainty,
                        reference, system)


# DISTANCE

# Astronomical Unit
au = Iau2015('au', "Astronomical Unit", 1.49597870700e11, 'm', 0.0,
              "IAU 2012 Resolution B2", system='si')

# Parsec

pc = Iau2015('pc', "Parsec", au.value / np.tan(np.radians(1. / 3600.)), 'm',
              au.uncertainty / np.tan(np.radians(1. / 3600.)),
              "Derived from au", system='si')

# Kiloparsec
kpc = Iau2015('kpc', "Kiloparsec",
               1000. * au.value / np.tan(np.radians(1. / 3600.)), 'm',
               1000. * au.uncertainty / np.tan(np.radians(1. / 3600.)),
               "Derived from au", system='si')

# Luminosity
L_bol0 = Iau2015('L_bol0', "Luminosity for absolute bolometric magnitude 0",
                  3.0128e28, "W", 0.0, "IAU 2015 Resolution B 2", system='si')


# SOLAR QUANTITIES

# Solar luminosity
L_sun = Iau2015('L_sun', "Nominal solar luminosity", 3.828e26,
                 'W', 0.0, "IAU 2015 Resolution B 3", system='si')

# Solar mass parameter
GM_sun = Iau2015('GM_sun', 'Nominal solar mass parameter', 1.3271244e20,
                  'm3 / (s2)', 0.0, "IAU 2015 Resolution B 3", system='si')

# Solar mass (derived from mass parameter and gravitational constant)
M_sun = Iau2015('M_sun', "Solar mass", GM_sun.value / CODATA2014.G.value,
                 'kg', ((CODATA2014.G.uncertainty / CODATA2014.G.value) *
                        (GM_sun.value / CODATA2014.G.value)),
                 "IAU 2015 Resolution B 3 + CODATA 2014", system='si')

# Solar radius
R_sun = Iau2015('R_sun', "Nominal solar radius", 6.957e8, 'm', 0.0,
                 "IAU 2015 Resolution B 3", system='si')


# OTHER SOLAR SYSTEM QUANTITIES

# Jupiter mass parameter
GM_jup = Iau2015('GM_jup', 'Nominal Jupiter mass parameter', 1.2668653e17,
                  'm3 / (s2)', 0.0, "IAU 2015 Resolution B 3", system='si')

# Jupiter mass (derived from mass parameter and gravitational constant)
M_jup = Iau2015('M_jup', "Jupiter mass", GM_jup.value / CODATA2014.G.value,
                 'kg', ((CODATA2014.G.uncertainty / CODATA2014.G.value) *
                        (GM_jup.value / CODATA2014.G.value)),
                 "IAU 2015 Resolution B 3 + CODATA 2014", system='si')

# Jupiter equatorial radius
R_jup = Iau2015('R_jup', "Nominal Jupiter equatorial radius", 7.1492e7,
                 'm', 0.0, "IAU 2015 Resolution B 3", system='si')

# Earth mass parameter
GM_earth = Iau2015('GM_earth', 'Nominal Earth mass parameter', 3.986004e14,
                  'm3 / (s2)', 0.0, "IAU 2015 Resolution B 3", system='si')

# Earth mass (derived from mass parameter and gravitational constant)
M_earth = Iau2015('M_earth', "Earth mass",
                   GM_earth.value / CODATA2014.G.value,
                 'kg', ((CODATA2014.G.uncertainty / CODATA2014.G.value) *
                        (GM_earth.value / CODATA2014.G.value)),
                 "IAU 2015 Resolution B 3 + CODATA 2014", system='si')

# Earth equatorial radius
R_earth = Iau2015('R_earth', "Nominal Earth equatorial radius", 6.3568e6,
                   'm', 0.0, "IAU 2015 Resolution B 3", system='si')

