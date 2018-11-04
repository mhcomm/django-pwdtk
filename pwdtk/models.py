from __future__ import absolute_import

import jsonfield

from django.db import models


class PwdData(models.Model):
    """ a model in case not custom way is specified for storing related data
    """
    user_id = models.PositiveIntegerField(null=True, blank=True, default=0)
    username = models.CharField(max_length=80, null=True,
                                blank=True, default='')
    data = jsonfield.JSONField(default={})
