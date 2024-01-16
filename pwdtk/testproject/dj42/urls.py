"""dj42 URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""


from django.contrib.auth import views as auth_views
from django.urls import path, re_path
from django.contrib import admin

from pwdtk.testviews import home
from pwdtk.testviews import logout_view
from pwdtk.testviews import protected

urlpatterns = [
    path('', home, name='pwdtk_test_home'),
    re_path(r'^login', auth_views.LoginView.as_view(),
            name='pwdtk_test_login'),
    re_path(r'^accounts/login', auth_views.LoginView.as_view(),
            name='pwdtk_test_login2'),
    re_path(r'^logout', logout_view,
            name='pwdtk_test_logout'),
    re_path(r'^protected', protected,
            name='pwdtk_test_protected'),
    re_path(r'^admin/', admin.site.urls),
    path('accounts/password_change/',
         auth_views.PasswordChangeView.as_view(),
         name='password_change'),
    path('accounts/password_change/done/',
         auth_views.PasswordChangeDoneView.as_view(),
         name='password_change_done'),
]
