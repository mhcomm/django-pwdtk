from __future__ import absolute_import
from __future__ import print_function

import django
print(django.VERSION)
if django.VERSION < (1, 9):
    from pwdtk.testproject.dj18.settings import *  # noqa: F401, F403
elif django.VERSION < (2, ):
    from pwdtk.testproject.dj1.settings import *  # noqa: F401, F403
else:
    from pwdtk.testproject.dj21.settings import *  # noqa: F401, F403
