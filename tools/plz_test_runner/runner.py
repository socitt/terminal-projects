"""Stdlib-only python_test runner for Please.

Please's built-in `unittest` test runner depends on the `xmlrunner` and
`portalocker` wheels (see //third_party/python:unittest_bootstrap in the
python-rules plugin). Fetching/repackaging those wheels fails under
iSH-AOK with `signal: hangup` (see docs/KNOWN_ISSUES.md). This runner
uses only unittest from the standard library, so python_test targets
that reference it never trigger a python_wheel build action.

Wired in via `TestRunner`/`TestrunnerDeps` in the root .plzconfig.
"""

import os
import sys
import unittest
from importlib import import_module


def _list_cases(suite):
    for test in suite:
        if isinstance(test, unittest.suite.TestSuite):
            yield from _list_cases(test)
        else:
            yield test, test.__class__.__module__ + '.' + test.id()


def _import_tests(test_names):
    for filename in test_names:
        module_name, _ = os.path.splitext(filename.replace('/', '.'))
        yield import_module(module_name)


def run(test_names, args):
    """Entry point. `test_names` are the python_test srcs; `args` are
    any extra `plz test` command-line filters."""
    suite = unittest.TestSuite(
        unittest.defaultTestLoader.loadTestsFromModule(module)
        for module in _import_tests(test_names)
    )

    filters = [a for a in args if not a.startswith('-')]
    if filters:
        filtered = unittest.TestSuite()
        for case, name in _list_cases(suite):
            if any(f in name for f in filters):
                filtered.addTest(case)
        suite = filtered

    result = unittest.TextTestRunner(verbosity=2, stream=sys.stdout).run(suite)
    return len(result.errors) + len(result.failures)
