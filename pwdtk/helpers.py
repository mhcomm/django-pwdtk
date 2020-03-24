from __future__ import absolute_import
from __future__ import print_function

import importlib
import inspect
import six

from django.conf import settings


def recursion_depth():
    """return recursion depth. 0 if no recursion"""
    # taken from https://github.com/looking-for-a-job/recursion-detect.py
    counter = 0
    frames = inspect.getouterframes(inspect.currentframe())[1:]
    top_frame = inspect.getframeinfo(frames[0][0])
    for frame, _, _, _, _, _ in frames[1:]:
        (path, line_number, func_name, lines, index) = inspect.getframeinfo(
            frame)
        if path == top_frame[0] and func_name == top_frame[2]:
            counter += 1
    return counter


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
