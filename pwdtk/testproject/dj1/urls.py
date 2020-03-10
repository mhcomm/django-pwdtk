"""dj1 URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""

import django.contrib.auth.views

from django.conf.urls import url
from django.contrib import admin

from pwdtk.testviews import home
from pwdtk.testviews import logout_view
from pwdtk.testviews import protected

urlpatterns = [
    url(r'^$', home, name='pwdtk_test_home'),
    url(r'^login', django.contrib.auth.views.LoginView.as_view(),
        name='pwdtk_test_login'),
    url(r'^accounts/login', django.contrib.auth.views.login,
        name='pwdtk_test_login2'),
    url(r'^logout', logout_view,
        name='pwdtk_test_logout'),
    url(r'^protected', protected,
        name='pwdtk_test_protected'),
    url(r'^admin/', admin.site.urls),
    url(r'^accounts/password_change/$',
        django.contrib.auth.views.password_change,
        name='password_change'),
    url(r'^accounts/password_change/done/$',
        django.contrib.auth.views.password_change_done,
        name='password_change_done'),
]
