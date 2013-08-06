import re
import warnings

import numpy as np

from astropy import units as u
from astropy.coordinates import Angle
from matplotlib.ticker import Formatter

from mpl_toolkits.axisartist import angle_helper as af

# Define a formatter based on the Astropy Angle class. Of course, we can add
# formatting options later, this is just a proof of concept.


DMS_RE = re.compile('^dd(:mm(:ss(.(s)+)?)?)?$')
HMS_RE = re.compile('^hh(:mm(:ss(.(s)+)?)?)?$')
DDEC_RE = re.compile('^d(.(d)+)?$')


class AngleFormatter(Formatter):

    def __init__(self, precision=1):
        self.precision = precision

    @property
    def format(self):
        return self._format

    @format.setter
    def format(self, value):
        self._format = value
        if DMS_RE.match(value) is not None:
            self._decimal = False
            self._unit = u.degree
            if '.' in value:
                self._precision = len(value) - value.index('.')
                self._fields = 3
            else:
                self._precision = 0
                self._fields = value.count(':') + 1
        elif HMS_RE.match(value) is not None:
            self._decimal = False
            self._unit = u.hourangle
            if '.' in value:
                self._precision = len(value) - value.index('.')
                self._fields = 3
            else:
                self._precision = 0
                self._fields = value.count(':') + 1
        elif DDEC_RE.match(value) is not None:
            self._decimal = True
            self._unit = u.degree
            self._fields = 1
            if '.' in value:
                self._precision = len(value) - value.index('.')
            else:
                self._precision = 0
        else:
            raise ValueError("Invalid format: {0}".format(value))

    def get_locator(self):
        if self._decimal:
            return af.LocatorDMS  # for now, need better locator later
        else:
            if self._unit is u.degree:
                if 'ss' in self._format:
                    return af.LocatorDMS
                elif 'mm' in self._format:
                    return af.LocatorDM
                else:
                    return af.LocatorD
            elif self._unit is u.hourangle:
                if 'ss' in self._format:
                    return af.LocatorHMS
                elif 'mm' in self._format:
                    return af.LocatorHM
                else:
                    return af.LocatorH

    def __call__(self, direction, factor, value, **kwargs):
        if len(value) > 0:
            angles = Angle(np.asarray(value) / factor, unit=u.deg)
            string = angles.to_string(unit=self._unit,
                                      precision=self._precision,
                                      decimal=self._decimal,
                                      fields=self._fields).tolist()
            return string
        else:
            return []
