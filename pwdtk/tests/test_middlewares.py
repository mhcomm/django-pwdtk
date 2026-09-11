#!/usr/bin/env python

# ############################################################################
# Name       : pwdtk.tests.test_middlewares
"""
  Summary    : Test the middleware hooks that the login flows do not reach:
               the per request reset of a cached custom settings class and
               the pass through of unrelated exceptions
"""
# #############################################################################

from unittest import mock

from django.test import RequestFactory

from pwdtk.middlewares import PwdtkMiddleware


def make_middleware():
    """ helper building the middleware around a view answering nothing """
    return PwdtkMiddleware(get_response=lambda request: None)


class CachedSettingsStub:
    """ stand-in for a custom settings class caching its values """
    reset_calls = 0

    @classmethod
    def reset_cache(cls):
        cls.reset_calls += 1


def test_settings_cache_is_reset_per_request():
    """ a custom settings class with a cache gets it dropped once per request """
    request = RequestFactory().get("/")

    with mock.patch("pwdtk.middlewares.PwdtkSettings", new=CachedSettingsStub):
        assert make_middleware().process_request(request) is None

    assert CachedSettingsStub.reset_calls == 1


def test_unrelated_exception_is_not_handled():
    """ an exception of the integrating project is left to django """
    request = RequestFactory().get("/")

    assert make_middleware().process_exception(request, ValueError("boom")) is None
