""" Test behavior related to masked tables
# TESTS:
# Add a masked column to existing non-masked table (should fail)
# Add a non-masked column to existing masked table (should succeed)
# Add a masked row to existing non-masked table (should fail)
# Add a non-masked row to existing masked table (should succeed)

"""

from .. import Column, MaskedColumn, Table
import numpy as np
import numpy.ma as ma


class SetupData(object):
    def setup_method(self, method):
        self.a = MaskedColumn('a', [1, 2, 3])
        self.b = MaskedColumn('b', [4, 5, 6], mask=True)
        self.c = MaskedColumn('c', [7, 8, 9], mask=False)
        self.d_mask = np.array([False, True, False])
        self.d = MaskedColumn('d', [7, 8, 7], mask=self.d_mask)
        self.t = Table([self.a, self.b], masked=True)
        self.ca = Column('ca', [1, 2, 3])


class TestMaskedColumnInit(SetupData):
    """Initialization of a masked column
    """

    def test_1(self):
        """Check that mask gets set properly and that it is a copy, not ref"""
        assert np.all(self.a.mask == False)
        assert np.all(self.b.mask == True)
        assert np.all(self.c.mask == False)
        assert np.all(self.d.mask == self.d_mask)
        self.d.mask[0] = True
        assert not np.all(self.d.mask == self.d_mask)

    def test_2(self):
        """Set mask from a list"""
        mask_list = [False, True, False]
        a = MaskedColumn('a', [1, 2, 3], mask=mask_list)
        assert np.all(a.mask == mask_list)

    def test_3(self):
        """Override existing mask values"""
        mask_list = [False, True, False]
        b = MaskedColumn('b', self.b, mask=mask_list)
        assert np.all(b.mask == mask_list)

    def test_4(self):
        """Incomplete mask specification (mask values cycle through available)"""
        mask_list = [False, True]
        b = MaskedColumn('b', length=4, mask=mask_list)
        assert np.all(b.mask == mask_list + mask_list)


class TestTableInit(SetupData):
    """Initializing a table"""

    def test_1(self):
        """Masking is True if any input is masked"""
        t = Table([self.ca, self.a])
        assert t.masked is True
        t = Table([self.ca])
        assert t.masked is False
        t = Table([self.ca, ma.array([1, 2, 3])])
        assert t.masked is True
