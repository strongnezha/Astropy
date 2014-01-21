# Licensed under a 3-clause BSD style license - see LICENSE.rst

import os


def get_package_data():
    return {
            'astropy.vo.samp': [os.path.join('data', '*.png')],
            'astropy.vo.samp.tests': [os.path.join('data', '*')]
           }
