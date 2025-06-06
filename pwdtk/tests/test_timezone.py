#!/usr/bin/env python

# ############################################################################
# Name       : pwdtk.tests.test_timezone
"""
  Summary    : Test timezone related functions
"""
# #############################################################################

import datetime

from pwdtk.models import PwdData


def test_aware_fail_time():
    data = PwdData()
    data.fail_time = datetime.datetime(2025, 6, 1, 0, 0, 0, tzinfo=None)
    assert data.aware_fail_time.tzinfo is not None
