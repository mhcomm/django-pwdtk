from __future__ import absolute_import
from __future__ import print_function

from django.contrib import admin

from pwdtk.models import PwdData


@admin.register(PwdData)
class PwdDataAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'locked', 'failed_logins', 'fail_time', 'last_change_time')
    search_fields = ('id', 'user')
