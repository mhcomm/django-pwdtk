from __future__ import absolute_import
from __future__ import print_function

import logging

from django.utils import timezone

from pwdtk.helpers import PwdtkSettings
from pwdtk.signals import pwd_data_post_change_password

logger = logging.getLogger(__name__)


class PwdTkValidator(object):

    def validate(self, password, user=None):
        return None

    def get_help_text(self):
        return ""

    def password_changed(self, password, user=None):

        if user and hasattr(user, 'pwdtk_data'):
            now = timezone.now()
            user.pwdtk_data.password_history.insert(0, (now, user.password))
            user.pwdtk_data.password_history[PwdtkSettings.PWDTK_PASSWD_HISTORY_LEN:] = []
            user.pwdtk_data.last_change_time = now
            user.pwdtk_data.must_renew = False
            user.pwdtk_data.save()
            pwd_data_post_change_password.send(sender=user.pwdtk_data.__class__, pwd_data=user.pwdtk_data)
