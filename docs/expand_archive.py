# This Sphinx extension expands all the tar files from the archive into the
# build directory.

import os
import glob
from tarfile import TarFile

from sphinx.util.console import bold
from sphinx.util import logging
logger = logging.getLogger(__name__)


def setup(app):
    from sphinx.application import Sphinx
    if not isinstance(app, Sphinx):
        return
    app.connect('build-finished', expand_archive)


META_NOINDEX = '<meta name="robots" content="noindex, nofollow">'


def expand_archive(app, exc):

    # Expand all tgz files directly into the build output

    archive_dir = os.path.join(app.builder.srcdir, 'archive')

    logger.info(bold('scanning {0} for archives...'.format(archive_dir)))

    for filename in sorted(glob.glob(os.path.join(archive_dir, '*.tgz'))):
        logger.info('   extracting {0}'.format(filename))
        tar_file = TarFile.open(filename)
        tar_file.extractall(app.builder.outdir)

    # Go through all html files in the built output and add the meta tag
    # to prevent search engines from crawling the pages

    logger.info(bold('adding {0} tag to pages...').format(META_NOINDEX))

    for filename in glob.glob(os.path.join(app.builder.outdir, '**', '*.html'), recursive=True):

        with open(filename, 'r') as f:
            content = f.read()

        if META_NOINDEX not in content:
            if '<head>' in content:
                content = content.replace('<head>', '<head>{0}'.format(META_NOINDEX))
            else:
                raise Exception("Could not determine start of <head> section in {0}".format(filename))

        with open(filename, 'w') as f:
            f.write(content)
