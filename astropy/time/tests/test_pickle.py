# Licensed under a 3-clause BSD style license - see LICENSE.rst

import numpy as np

from .. import Time
from ...extern.six.moves import cPickle as pickle


class TestPickle():
    """Basic pickle test of time"""

    def test_pickle(self):
        times = ['1999-01-01 00:00:00.123456789', '2010-01-01 00:00:00']
        t1 = Time(times, scale='utc')
        t1d = pickle.dumps(t1)
        t1l = pickle.loads(t1d)
        assert np.all(t1l == t1)

        t2 = Time('2012-06-30 12:00:00', scale='utc')
        t2d = pickle.dumps(t2)
        t2l = pickle.loads(t2d)

        assert t2l == t2
