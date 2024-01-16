from __future__ import absolute_import
from __future__ import print_function

import django
print(django.VERSION)
if django.VERSION < (2, ):
    from pwdtk.testproject.dj1.settings import *  # noqa: F401, F403
elif django.VERSION < (2, 2):
    from pwdtk.testproject.dj21.settings import *  # noqa: F401, F403
elif django.VERSION < (3, 1):
    from pwdtk.testproject.dj22.settings import *  # noqa: F401, F403
elif django.VERSION < (4, 2):
    from pwdtk.testproject.dj31.settings import *  # noqa: F401, F403
else:
    from pwdtk.testproject.dj42.settings import *  # noqa: F401, F403
