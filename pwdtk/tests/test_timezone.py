#!/usr/bin/env python

# ############################################################################
# Copyright  : (C) 2025 by MHComm. All rights reserved
#
# Name       : pwdtk.tests.test_timezone
"""
  Summary    : Test timezone related functions

__author__ = "Jonathan Lajus"
__email__ = "info@mhcomm.fr"
"""
# #############################################################################

import datetime

from pwdtk.models import PwdData


def test_aware_fail_time():
    data = PwdData()
    data.fail_time = datetime.datetime(2025, 6, 1, 0, 0, 0, tzinfo=None)
    assert data.aware_fail_time.tzinfo is not None
