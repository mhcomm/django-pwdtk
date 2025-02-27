# PWDTK signals

import django.dispatch

# providing_args=["pwd_data"]
pwd_data_post_change_password = django.dispatch.Signal()
