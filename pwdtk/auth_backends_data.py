import logging

from django.contrib.auth import get_user_model


logger = logging.getLogger(__name__)
logger.debug("######## Imp backend2 data")  # for debugging dj 1.8 -> 1.11


class UserData(object):
    User = None

    def __init__(self, user=None, username=None):
        cls = self.__class__
        if user:
            self.user = user
        else:
            User = cls.User
            if not cls.User:
                User = cls.User = get_user_model()

            self.user = user = User.objects.get(username=username)

        try:
            self.user_profile = user.user_profile
        except Exception:
            self.user_profile = None
            self.data = {}
            logger.warning("problems getting profile for user %s",
                           user.username)
            return

        data = self.data = user.user_profile.data.get('pwd_policy') or {}
        user.user_profile.data['pwd_policy'] = data
        user.user_profile.save()

    @property
    def failed_logins(self):
        return self.data.get('failed_logins', 0)

    @failed_logins.setter
    def failed_logins(self, value):
        self.data['failed_logins'] = value

    @property
    def locked(self):
        return self.data.get('locked', False)

    @locked.setter
    def locked(self, value):
        self.data['locked'] = value

    @property
    def fail_time(self):
        return self.data.get('fail_time') or ''

    @fail_time.setter
    def fail_time(self, value):
        self.data['fail_time'] = value

    def save(self):
        if self.user_profile:
            self.user_profile.save()


logger.debug("######## Imped backend2 data")  # for debugging dj 1.8 -> 1.11
