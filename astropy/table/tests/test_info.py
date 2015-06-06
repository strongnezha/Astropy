# -*- coding: utf-8 -*-
# Licensed under a 3-clause BSD style license - see LICENSE.rst

# TEST_UNICODE_LITERALS

import numpy as np

from ...extern import six
from ... import units as u
from ... import time
from ... import table
from ...utils.data_info import data_info_factory
from ...utils import OrderedDict

STRING8 = 'string8' if six.PY2 else 'bytes8'

def test_info_attributes(table_types):
    """
    Test the info() method of printing a summary of table column attributes
    """
    a = np.array([1, 2, 3], dtype='int32')
    b = np.array([1, 2, 3], dtype='float32')
    c = np.array(['a', 'c', 'e'], dtype='|S1')
    t = table_types.Table([a, b, c], names=['a', 'b', 'c'])

    # Minimal output for a typical table
    tinfo = t.info(out=None)
    subcls = ['class'] if table_types.Table.__name__ == 'MyTable' else []
    assert tinfo.colnames == ['name', 'dtype'] + subcls
    assert np.all(tinfo['name'] == ['a', 'b', 'c'])
    assert np.all(tinfo['dtype'] == ['int32', 'float32', STRING8])
    if subcls:
        assert np.all(tinfo['class'] == ['MyColumn'] * 3)

    # All output fields including a mixin column
    t['d'] = [1,2,3] * u.m
    t['d'].description = 'description'
    t['a'].format = '%02d'
    t['e'] = time.Time([1,2,3], format='mjd')
    tinfo = t.info(out=None)
    assert tinfo.colnames == 'name  dtype  unit format description class'.split()
    assert np.all(tinfo['name'] == 'a b c d e'.split())
    assert np.all(tinfo['dtype'] == ['int32', 'float32', STRING8, 'float64', 'object'])
    assert np.all(tinfo['unit'] == ['', '', '', 'm', ''])
    assert np.all(tinfo['format'] == ['%02d', '', '', '', ''])
    assert np.all(tinfo['description'] == ['', '', '', 'description', ''])
    cls = 'MyColumn' if subcls else ''
    assert np.all(tinfo['class'] == [cls, cls, cls, cls, 'Time'])

def test_info_stats(table_types):
    """
    Test the info() method of printing a summary of table column statistics
    """
    a = np.array([1, 2, 1, 2], dtype='int32')
    b = np.array([1, 2, 1, 2], dtype='float32')
    c = np.array(['a', 'c', 'e', 'f'], dtype='|S1')
    d = time.Time([1, 2, 1, 2], format='mjd')
    t = table_types.Table([a, b, c, d], names=['a', 'b', 'c', 'd'])

    # option = 'stats'
    masked = 'masked=True ' if t.masked else ''
    out = six.moves.cStringIO()
    t.info('stats', out=out)
    table_header_line = '<{0} {1}length=4>'.format(t.__class__.__name__, masked)
    exp = [table_header_line,
           'name mean std min max',
           '---- ---- --- --- ---',
           '   a  1.5 0.5   1   2',
           '   b  1.5 0.5 1.0 2.0',
           '   c   --  --  --  --',
           '   d   --  -- 1.0 2.0']
    assert out.getvalue().splitlines() == exp

    # option = ['attributes', 'stats']
    tinfo = t.info(['attributes', 'stats'], out=None)
    assert tinfo.colnames == 'name  dtype  class mean std min max'.split()
    assert np.all(tinfo['mean'] == ['1.5', '1.5', '--', '--'])
    assert np.all(tinfo['std'] == ['0.5', '0.5', '--', '--'])
    assert np.all(tinfo['min'] == ['1', '1.0', '--', '1.0'])
    assert np.all(tinfo['max'] == ['2', '2.0', '--', '2.0'])

    # option = ['attributes', custom]
    custom = data_info_factory(names=['sum', 'first'],
                               funcs=[np.sum, lambda col: col[0]])
    out = six.moves.cStringIO()
    tinfo = t.info(['attributes', custom], out=None)
    assert tinfo.colnames == 'name dtype class sum first'.split()
    assert np.all(tinfo['name'] == ['a', 'b', 'c', 'd'])
    assert np.all(tinfo['dtype'] == ['int32', 'float32', STRING8, 'object'])
    assert np.all(tinfo['sum'] == ['6', '6.0', '--', '--'])
    assert np.all(tinfo['first'] == ['1', '1.0', 'a' if six.PY2 else "b'a'", '1.0'])

def test_data_info():
    """
    Test getting info for just a column.
    """
    cols = [table.Column([1.0, 2.0, np.nan], name='name',
                         description='description', unit='m/s'),
            table.MaskedColumn([1.0, 2.0, 3.0], name='name',
                               description='description', unit='m/s',
                               mask=[False, False, True])]
    for c in cols:
        # Test getting the full ordered dict
        cinfo = c.info(out=None)
        assert cinfo == OrderedDict([('name', 'name'),
                                     ('dtype', 'float64'),
                                     ('shape', ''),
                                     ('unit', 'm / s'),
                                     ('format', ''),
                                     ('description', 'description'),
                                     ('class', ''),
                                     ('n_bad', 1),
                                     ('length', 3)])

        # Test the console (string) version which omits trivial values
        out = six.moves.cStringIO()
        c.info(out=out)
        exp = ['name = name',
               'dtype = float64',
               'unit = m / s',
               'description = description',
               'n_bad = 1',
               'length = 3']
        assert out.getvalue().splitlines() == exp

        # Test stats info
        cinfo = c.info('stats', out=None)
        assert cinfo == OrderedDict([('name', 'name'),
                                     ('mean', '1.5'),
                                     ('std', '0.5'),
                                     ('min', '1.0'),
                                     ('max', '2.0'),
                                     ('n_bad', 1),
                                     ('length', 3)])

def test_data_info_subclass():
    class Column(table.Column):
        """
        Confusingly named Column on purpose, but that is legal.
        """
        pass
    c = Column([1, 2], dtype='int64')
    cinfo = c.info(out=None)
    assert cinfo == OrderedDict([('dtype', 'int64'),
                                 ('shape', ''),
                                 ('unit', ''),
                                 ('format', ''),
                                 ('description', ''),
                                 ('class', 'Column'),
                                 ('n_bad', 0),
                                 ('length', 2)])
