#!/usr/bin/env python

# ############################################################################
# Name       : pwdtk.tests.test_helpers
"""
  Summary    : Test how the pwdtk settings are looked up: through django's
               settings by default, through PWDTK_CUSTOM_SETTINGS_CLS when
               an integrating project provides one, and through the obsolete
               pwdtk.auth_backends_settings module
"""
# #############################################################################

import importlib
import importlib.util
import logging
import sys

from django.test import override_settings

import pwdtk.helpers
import pwdtk.settings
from pwdtk.helpers import PwdtkSettingsType
from pwdtk.helpers import _resolve_object_path


class CustomSettingsType(type):
    """ stand-in for the settings class of an integrating project """

    def __getattr__(cls, key):
        return "custom:" + key


def test_resolve_object_path():
    """ a custom settings class is given as a dotted path or as the class """
    assert _resolve_object_path("pwdtk.helpers.PwdtkSettingsType") is PwdtkSettingsType
    assert _resolve_object_path(PwdtkSettingsType) is PwdtkSettingsType


def test_custom_settings_class():
    """ PWDTK_CUSTOM_SETTINGS_CLS replaces the lookup in django's settings """
    # the choice is made when the module is imported, hence it is executed
    # once more into a module of its own, leaving the imported one untouched
    spec = importlib.util.spec_from_file_location("pwdtk_helpers_custom", pwdtk.helpers.__file__)
    helpers = importlib.util.module_from_spec(spec)

    with override_settings(PWDTK_CUSTOM_SETTINGS_CLS="pwdtk.tests.test_helpers.CustomSettingsType"):
        spec.loader.exec_module(helpers)

    assert helpers.PwdtkSettings.PWDTK_LOCKOUT_TIME == "custom:PWDTK_LOCKOUT_TIME"
    assert pwdtk.helpers.PwdtkSettings.PWDTK_LOCKOUT_TIME == pwdtk.settings.PWDTK_LOCKOUT_TIME


def test_obsolete_settings_module(caplog):
    """ the obsolete pwdtk.auth_backends_settings still works, but warns """
    sys.modules.pop("pwdtk.auth_backends_settings", None)

    with caplog.at_level(logging.WARNING):
        obsolete = importlib.import_module("pwdtk.auth_backends_settings")

    assert obsolete.PWDTK_ENABLED is pwdtk.settings.PWDTK_ENABLED
    warnings = [record.getMessage() for record in caplog.records if record.levelno == logging.WARNING]
    assert len(warnings) == 1
    assert "obsolete" in warnings[0]
    assert "pwdtk.settings" in warnings[0]
