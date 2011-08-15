#!/usr/bin/env python
from __future__ import division

"""
Version numbering for astropy. The `major`, `minor`, and `bugfix` varaibles hold
the respective parts of the version number. The `release` variable is True if 
this is a release, and False if this is a development version of astropy. For
the actual version string, use::

    from astropy.version import version
    
"""

major = 0
minor = 0
bugfix = 0

release = False

version = '{0}.{1}.{2}'.format(major,minor,bugfix)    


def _get_git_devstr(sha=False):
    r"""Determines the number of revisions in this repository.

    These

    Parameters
    ----------
    sha : bool
        If True, the full SHA1 hash will be at the end of the devstr. Otherwise,
        the total count of commits in the repository will be used as a "revision
        number".

    Returns
    -------
    devstr : str
        A string that begins with 'dev' to be appended to the astropy version
        number string.
        
    """
    from os import path
    from subprocess import Popen,PIPE
    from warnings import warn
    
    if release:
        raise ValueError('revsion devstring should not be used in a release version')

    currdir = path.abspath(path.split(__file__)[0])
    
    p = Popen(['git','rev-list','HEAD'],cwd=currdir,
              stdout=PIPE,stderr=PIPE,stdin=PIPE)
    stdout,stderr = p.communicate()
        
    if p.returncode == 128:
        warn('No git repository present! Using default dev version.')
        return 'dev'
    elif p.returncode != 0:
        warn('Git failed while determining revision count: '+stderr)
        return 'dev'
    
    if sha:
        return 'dev-git-'+stdout[:40]
    else:
        nrev = stdout.count('\n')
        return  'dev-r%i'%nrev
    
if not release:
    version = version+_get_git_devstr(False)