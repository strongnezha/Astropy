# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Validate VO Services.

*CONFIGURABLE PROPERTIES*

These properties are set via Astropy configuration system:

    * `astropy.vo.server.cs_mstr_list`
    * Also depends on properties in `astropy.vo.client`

.. note::

    This is not meant to be used by a typical AstroPy user.

"""
# STDLIB
from collections import defaultdict
from copy import deepcopy
import json
import os
import shutil
import time
import warnings

# THIRD PARTY
import numpy

# LOCAL
from ..client import vos_catalog
from ...io import votable
from ...io.votable.validator import html, result
from ...logger import log
from ...utils.misc import NumpyScalarEncoder

# LOCAL CONFIG
from ...config.configuration import ConfigurationItem

__all__ = ['check_conesearch_sites']

CS_MSTR_LIST = ConfigurationItem(
    'cs_mstr_list',
    'http://vao.stsci.edu/directory/NVORegInt.asmx/VOTCapabilityPredOpt?'
    'predicate=1%3D1&capability=conesearch&VOTStyleOption=2',
    'Conesearch master list query from VAO.')

_OUT_ROOT = None  # Set by `check_conesearch_sites`


def check_conesearch_sites(destdir=os.curdir, verbose=True, multiproc=True,
                           url_list=None):
    """
    Validate Cone Search Services.

    A master list of all available Cone Search sites is
    obtained from `astropy.vo.server.cs_mstr_list`, which
    is a URL query to an external VAO service.

    These sites are validated using `astropy.io.votable.validator`
    and separated into four groups below, each is stored as a JSON
    database in `destdir`. Existing files with same names will be
    deleted to avoid confusion:

        #. 'conesearch_good.json' - Passed validation without any
           warnings or exceptions. If this database is not empty,
           it will be used by `astropy.vo.client.conesearch`.
        #. 'conesearch_warn.json' - Has some warnings but no
           exceptions. Use this instead if database above is empty.
        #. 'conesearch_exception.json' - Has some exceptions.
           *Never* use this. For informational purpose only.
        #. 'conesearch_error.json' - Has network connection error.
           *Never* use this. For informational purpose only.

    For convenience, the database that `astropy.vo.client.conesearch`
    is supposed to use will be symbolically linked (Unix) or copied
    (if linking fails) to 'conesearch.json'.

    HTML pages summarizing the validation results are generated by
    `astropy.io.votable.validator` and stored in 'results'
    sub-directory. Downloaded XML files are also stored here.

    *BUILDING THE DATABASE*

    For user-friendly catalog listing, title will be the catalog key.
    To avoid repeating the same query, access URL should be unique.
    But a title can have multiple access URLs, and vice versa.
    In addition, the same title and access URL can also repeat under
    different descriptions.

    In the case of (title, url 1) and (title, url 2), they will appear
    as two different entries with title renamed to 'title N' where N
    is a sequence number. If the title does not repeat in the entire
    database, only 'title 1' exists.

    In the case of (title 1, url) and (title 2, url), database will
    use (title 1, url) and ignore (title 2, url).

    If the same (title, url) has multiple entries, database will use
    the first match and ignore the rest.

    A new field named 'duplicatesIgnored' is added to each catalog in
    the database to count ignored duplicate entries.

    Parameters
    ----------
    destdir : string
        Directory to store output files. Will be created if does
        not exist.

    verbose : bool
        Print extra info to log.

    multiproc : bool
        Enable multiprocessing.

    url_list : list of string
        Only check these access URLs from the master list and
        ignore the others, which will not appear in output files.
        This is useful for testing or debugging. If `None`, check
        everything.

    Raises
    ------
    AssertionError
        Parameter failed assertion test.

    timeout
        URL request timed out.

    """
    global _OUT_ROOT

    assert (not os.path.exists(destdir) and len(destdir) > 0) or \
        (os.path.exists(destdir) and os.path.isdir(destdir)), \
        'Invalid destination directory'

    if url_list is not None:
        from collections import Iterable
        assert isinstance(url_list, Iterable)
        for cur_url in url_list:
            assert isinstance(cur_url, basestring)

    if not os.path.exists(destdir):
        os.mkdir(destdir)

    if destdir[-1] != os.sep:
        destdir += os.sep

    # Output dir created by votable.validator
    _OUT_ROOT = destdir + 'results'

    # Output files
    db_file = {}
    db_file['good'] = destdir + 'conesearch_good.json'
    db_file['warn'] = destdir + 'conesearch_warn.json'
    db_file['excp'] = destdir + 'conesearch_exception.json'
    db_file['nerr'] = destdir + 'conesearch_error.json'
    db_to_use = destdir + 'conesearch.json'

    # JSON dictionaries for output files
    js_template = {'__version__': 1, 'catalogs': {}}
    js_mstr = deepcopy(js_template)
    js_tree = {}
    for key in db_file:
        js_tree[key] = deepcopy(js_template)

        # Delete existing files, if any, to be on the safe side.
        # Else can cause confusion if program exited prior to
        # new files being written but old files are still there.
        _do_rmfile(db_file[key], verbose=verbose)
    _do_rmfile(db_to_use, verbose=verbose)

    # Get all Cone Search sites

    if CS_MSTR_LIST().startswith(('http://', 'file://', 'ftp://')):
        import urllib2
        cur_url = urllib2.urlopen(CS_MSTR_LIST(),
                                  timeout=vos_catalog.TIMEOUT())
    else:
        cur_url = CS_MSTR_LIST()

    tab_all = votable.parse_single_table(cur_url, pedantic=False)
    arr_cone = tab_all.array.data[numpy.where(
        tab_all.array['capabilityClass'] == 'ConeSearch')]

    assert arr_cone.size > 0, 'CS_MSTR_LIST yields no valid result'

    # Re-structure dictionary for JSON file

    col_names = arr_cone.dtype.names
    col_to_rename = {'accessURL': 'url'}  # To be consistent with client
    uniq_urls = set(arr_cone['accessURL'])
    uniq_rows = len(uniq_urls)
    check_sum = 0
    title_counter = defaultdict(int)
    conesearch_pars = 'RA=0&DEC=0&SR=0'
    key_lookup_by_url = {}

    for cur_url in uniq_urls:
        if url_list is not None and cur_url not in url_list:
            if verbose:
                log.info('Skipping {}'.format(cur_url))
            continue

        i_same_url = numpy.where(arr_cone['accessURL'] == cur_url)
        i = i_same_url[0][0]

        num_match = len(i_same_url[0])
        check_sum += num_match
        row_d = {'duplicatesIgnored': num_match - 1}

        cur_title = arr_cone[i]['title']
        title_counter[cur_title] += 1
        cat_key = '{} {}'.format(cur_title, title_counter[cur_title])

        for col in col_names:
            if col in col_to_rename:
                row_d[col_to_rename[col]] = arr_cone[i][col]
            else:
                row_d[col] = arr_cone[i][col]

        js_mstr['catalogs'][cat_key] = row_d
        key_lookup_by_url[cur_url + conesearch_pars] = cat_key

    assert check_sum == arr_cone.size, 'Database checksum error'
    assert len(js_mstr['catalogs']) == uniq_rows, \
        'Number of database entries do not match unique access URLs'

    # Validate URLs

    all_urls = key_lookup_by_url.keys()
    t_beg = time.time()

    if multiproc:
        import multiprocessing
        mp_list = []
        pool = multiprocessing.Pool()
        mp_proc = pool.map_async(_do_validation, all_urls,
                                 callback=mp_list.append)
        mp_proc.wait()
        mp_list = mp_list[0]

    else:
        mp_list = [_do_validation(cur_url) for cur_url in all_urls]

    t_end = time.time()

    if verbose:
        log.info('Validation of {} sites took {} s'.format(uniq_rows,
                                                           t_end - t_beg))

    # Categorize validation results
    for r in mp_list:
        db_key = r['out_db_name']
        cat_key = key_lookup_by_url[r.url]
        js_tree[db_key]['catalogs'][cat_key] = js_mstr['catalogs'][cat_key]

    # Write to HTML

    html_subsets = result.get_result_subsets(mp_list, _OUT_ROOT)
    html.write_index(html_subsets, all_urls, _OUT_ROOT)

    if multiproc:
        html_subindex_args = [(html_subset, uniq_rows)
                              for html_subset in html_subsets]
        pool = multiprocessing.Pool()
        mp_proc = pool.map_async(_html_subindex, html_subindex_args)
        mp_proc.wait()

    else:
        for html_subset in html_subsets:
            _html_subindex((html_subset, uniq_rows))

    # Write to JSON
    n = {}
    for key in db_file:
        n[key] = len(js_tree[key]['catalogs'])
        if verbose:
            log.info('{}: {} catalogs'.format(key, n[key]))
        with open(db_file[key], 'w') as f_json:
            f_json.write(json.dumps(js_tree[key], cls=NumpyScalarEncoder,
                                    sort_keys=True, indent=4))

    # Make symbolic link
    if n['good'] > 0:
        _do_symlink_or_copy(db_file['good'], db_to_use)
    elif n['warn'] > 0:
        _do_symlink_or_copy(db_file['warn'], db_to_use)
        if verbose:
            log.info('No Cone Search sites cleanly passed validation.')
    else:
        log.warn('All sites have exceptions or errors. '
                 'No viable database for Cone Search.')


def _do_validation(url):
    """Validation for multiprocessing support."""
    r = result.Result(url, root=_OUT_ROOT)
    r.validate_vo()

    if r['network_error'] is not None:
        r['out_db_name'] = 'nerr'
        r['expected'] = 'broken'
    elif r['nexceptions'] > 0:
        r['out_db_name'] = 'excp'
        r['expected'] = 'incorrect'
    elif r['nwarnings'] > 0:
        r['out_db_name'] = 'warn'
        r['expected'] = 'incorrect'
    else:
        r['out_db_name'] = 'good'
        r['expected'] = 'good'

    # Catch well-formed error responses
    # Accessing URL instead of using cache (not elegant but works for now)

    nexceptions = 0
    nwarnings = 0
    lines = []

    with warnings.catch_warnings(record=True) as warning_lines:
        try:
            tab = vos_catalog._vo_service_request(r.url, False, {})
        except (IndexError, vos_catalog.VOSError) as e:
            lines.append(str(e))
            nexceptions += 1
    lines = [str(x.message) for x in warning_lines] + lines

    warning_types = set()
    for line in lines:
        w = votable.exceptions.parse_vowarning(line)
        if w['is_warning']:
            nwarnings += 1
        if w['is_exception']:
            nexceptions += 1
        warning_types.add(w['warning'])

    r['nwarnings'] += nwarnings
    r['nexceptions'] += nexceptions
    r['warnings'] += lines
    r['warning_types'] = r['warning_types'].union(warning_types)

    # HTML page
    html.write_result(r)

    return r


def _html_subindex(args):
    """HTML writer for multiprocessing support."""
    subset, total = args
    html.write_index_table(_OUT_ROOT, *subset, total=total)


def _do_rmfile(filename, verbose=True):
    """Delete a file or symbolic link."""
    if os.path.exists(filename):
        assert not os.path.isdir(filename), \
            '{} is a directory, cannot continue'.format(filename)
        os.remove(filename)
        if verbose:
            log.info('Existing file {} deleted'.format(filename))
    elif os.path.lexists(filename):
        os.unlink(filename)
        if verbose:
            log.info('Existing symbolic link {} deleted'.format(filename))


def _do_symlink_or_copy(src, dst):
    """Create symbolic link (Unix) or a copy (if sym link fails)."""
    try:
        os.symlink(src, dst)
    except:
        shutil.copyfile(src, dst)
