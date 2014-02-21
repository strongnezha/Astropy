import sys

from ..hub_script import hub_script

from ..utils import ALLOW_INTERNET


def setup_module(module):
    ALLOW_INTERNET.set(False)


def setup_function(function):
    function.sys_argv_orig = sys.argv
    sys.argv = ["samp_hub"]


def teardown_function(function):
    sys.argv = function.sys_argv_orig


def test_hub_script():
    sys.argv.append('-m')  # run in multiple mode
    sys.argv.append('-w')  # disable web profile
    hub_script(timeout=3)
