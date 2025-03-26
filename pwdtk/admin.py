from __future__ import absolute_import
from __future__ import print_function

from django.contrib import admin

from pwdtk.models import PwdData


@admin.register(PwdData)
class PwdDataAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'locked',
        'failed_logins',
        'fail_time',
        'last_change_time',
        'must_renew',
        'lockout_count',
        'lockout_time_remaining_formatted',
        )
    search_fields = ('id', 'user')

    def get_readonly_fields(self, request, obj=None):
        return ['lockout_time_remaining_formatted'] + list(super().get_readonly_fields(request, obj))
