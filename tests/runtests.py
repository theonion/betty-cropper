#!/usr/bin/env python
import unittest

from betty.flask.tests import BettyTestCase

if __name__ == '__main__':
    flask_suite = unittest.TestLoader().loadTestsFromTestCase(BettyTestCase)
    unittest.TextTestRunner(verbosity=2).run(flask_suite)
