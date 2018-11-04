import logging

from django.contrib.auth import get_user_model

from pwdtk.models import PwdData


logger = logging.getLogger(__name__)
logger.debug("######## Imp backend2 data")  # for debugging dj 1.8 -> 1.11


class PwdTkError(Exception):
    """ custom exception """


class UserData(object):
    User = None

    def __init__(self, user=None, username=None):
        cls = self.__class__

        User = cls.User
        if not User:
            User = cls.User = get_user_model()

        if user:
            username = user.username
        elif username:
            user = User.objects.get(username=username)
        else:
            msg = "need either user or username"
            logger.error(msg)
            raise PwdTkError(msg)

        self.user = user
        pwd_data, created = PwdData.objects.get_or_create(
            user_id=user.id,
            defaults={
                'username': username,
                'data': {},
                }
            )
        pwd_data.save()

        self.pwd_data = pwd_data
        self.data = self.pwd_data.data

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

    @property
    def passwd_history(self):
        """ password history
            a list of tuples of timestamp, pwd_hash
        """
        hist = self.data.get('passwd_history')
        if hist is None:
            hist = self.data['passwd_history'] = []

        return hist

    def save(self):
        if self.pwd_data:
            self.pwd_data.save()


logger.debug("######## Imped backend2 data")  # for debugging dj 1.8 -> 1.11
