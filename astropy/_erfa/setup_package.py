# Licensed under a 3-clause BSD style license - see LICENSE.rst

import os
import glob

from distutils import log
from distutils.extension import Extension

from astropy_helpers import setup_helpers
from astropy_helpers.version_helpers import get_pkg_version_module

ERFAPKGDIR = os.path.relpath(os.path.dirname(__file__))

ERFA_SRC = os.path.abspath(os.path.join(ERFAPKGDIR, '..', '..', 'cextern', 'erfa'))

SRC_FILES = glob.glob(os.path.join(ERFA_SRC, '*'))
SRC_FILES += [os.path.join(ERFAPKGDIR, filename)
              for filename in ['core.py.templ', 'core.c.templ', 'erfa_generator.py']]

GEN_FILES = [os.path.join(ERFAPKGDIR, 'core.py'), os.path.join(ERFAPKGDIR, 'core.c')]


def pre_build_py_hook(cmd_obj):
    preprocess_source()


def pre_build_ext_hook(cmd_obj):
    preprocess_source()


def pre_sdist_hook(cmd_obj):
    preprocess_source()


def preprocess_source():
    # Generating the ERFA wrappers should only be done if needed. This also
    # ensures that it is not done for any release tarball since those will
    # include core.py and core.c.
    if all(os.path.exists(filename) for filename in GEN_FILES):

        # Determine modification times
        erfa_mtime = max(os.path.getmtime(filename) for filename in SRC_FILES)
        gen_mtime = min(os.path.getmtime(filename) for filename in GEN_FILES)

        version = get_pkg_version_module('astropy')

        if gen_mtime > erfa_mtime:
            # If generated source is recent enough, don't update
            return
        elif version.release:
            # or, if we're on a release, issue a warning, but go ahead and use
            # the wrappers anyway
            log.warn('WARNING: The autogenerated wrappers in astropy._erfa '
                     'seem to be older than the source templates used to '
                     'create them. Because this is a release version we will '
                     'use them anyway, but this might be a sign of some sort '
                     'of version mismatch or other tampering. Or it might just '
                     'mean you moved some files around or otherwise '
                     'accidentally changed timestamps.')
            return
        # otherwise rebuild the autogenerated files

        # If jinja2 isn't present, then print a warning and use existing files
        try:
            import jinja2  # pylint: disable=W0611
        except ImportError:
            log.warn("WARNING: jinja2 could not be imported, so the existing "
                     "ERFA core.py and core.c files will be used")
            return

    name = 'erfa_generator'
    filename = os.path.join(ERFAPKGDIR, 'erfa_generator.py')

    try:
        from importlib import machinery as import_machinery
        loader = import_machinery.SourceFileLoader(name, filename)
        gen = loader.load_module()
    except ImportError:
        import imp
        gen = imp.load_source(name, filename)

    gen.main(gen.DEFAULT_ERFA_LOC,
             os.path.join(ERFAPKGDIR, 'core.py'),
             gen.DEFAULT_TEMPLATE_LOC,
             verbose=False)


def get_extensions():
    sources = [os.path.join(ERFAPKGDIR, "core.c")]
    include_dirs = ['numpy']
    libraries = []

    if setup_helpers.use_system_library('erfa'):
        libraries.append('erfa')
    else:
        # get all of the .c files in the cextern/erfa directory
        erfafns = os.listdir(ERFA_SRC)
        sources.extend(['cextern/erfa/'+fn for fn in erfafns if fn.endswith('.c')])

        include_dirs.append('cextern/erfa')

    erfa_ext = Extension(
        name="astropy._erfa._core",
        sources=sources,
        include_dirs=include_dirs,
        libraries=libraries,
        language="c",)

    return [erfa_ext]


def get_external_libraries():
    return ['erfa']
