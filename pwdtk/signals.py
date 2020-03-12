# PWDTK signals

import django.dispatch

pwd_data_post_change_password = django.dispatch.Signal(
                                    providing_args=["pwd_data"])
