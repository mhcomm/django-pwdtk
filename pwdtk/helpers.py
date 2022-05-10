from __future__ import absolute_import
from __future__ import print_function

import importlib
import six

from django.conf import settings


def _resolve_object_path(dotted_name):

    if isinstance(dotted_name, six.string_types):

        module_name, obj_name = dotted_name.rsplit(".", 1)
        module = importlib.import_module(module_name)
        return getattr(module, obj_name)

    return dotted_name


class PwdtkSettingsType(type):

    def __getattr__(cls, key):
        return getattr(settings, key)


if getattr(settings, 'PWDTK_CUSTOM_SETTINGS_CLS', None):
    class PwdtkSettings(six.with_metaclass(
      _resolve_object_path(settings.PWDTK_CUSTOM_SETTINGS_CLS))):
        pass
else:
    class PwdtkSettings(six.with_metaclass(PwdtkSettingsType)):
        pass
