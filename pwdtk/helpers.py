from __future__ import absolute_import
from __future__ import print_function

import inspect
import datetime
import dateutil
import six

from django.conf import settings

def get_delta_seconds(timestr, now=None):
    if not timestr:
        return 0
    now = now if now else datetime.datetime.utcnow()
    delta = now - dateutil.parser.parse(timestr)
    delta_secs = delta.days * 86400 + delta.seconds
    return delta_secs


def get_fail_age(fail_time):
    """ returns fail age in seconds """
    t_fail = dateutil.parser.parse(fail_time)
    t_delta = datetime.datetime.utcnow() - t_fail
    delta_secs = t_delta.days * 86400 + t_delta.seconds
    return delta_secs


def seconds_to_iso8601(seconds):
    """ helper to convert seconds to iso string """

    seconds = float(seconds)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    days, hours, minutes = map(int, (days, hours, minutes))
    seconds = round(seconds, 6)

    # ## build date
    date = ''
    if days:
        date = '%sD' % days

    # ## build time
    time = u'T'
    # hours
    bigger_exists = date or hours
    if bigger_exists:
        time += '{:02}H'.format(hours)
    # minutes
    bigger_exists = bigger_exists or minutes
    if bigger_exists:
        time += '{:02}M'.format(minutes)
    # seconds
    if seconds.is_integer():
        seconds = '{:02}'.format(int(seconds))
    else:
        # 9 chars long w/leading 0, 6 digits after decimal
        seconds = '%09.6f' % seconds
    # remove trailing zeros
    seconds = seconds.rstrip('0')
    time += '{}S'.format(seconds)
    return u'P' + date + time


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
        path = dotted_name.split('.')
        module = __import__(dotted_name.rsplit('.', 1)[0])
        for item in path[1:-1]:
            module = getattr(module, item)
        return getattr(module, path[-1])

    return dotted_name


class PwdtkSettingsType(type):

    def __getattr__(cls, key):
        return getattr(settings, key)


class PwdtkSettings:

    if getattr(settings, 'PWDTK_CUSTOM_SETTINGS_CLS', None):
        __metaclass__ = _resolve_object_path(settings.PWDTK_CUSTOM_SETTINGS_CLS)
    else:
        __metaclass__ = PwdtkSettingsType
