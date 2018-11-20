"""dj18 URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import include, url
from django.contrib import admin


urlpatterns = [
    url(r'^$', 'pwdtk.testviews.home', name='pwdtk_test_home'),
    url(r'^login', 'pwdtk.testviews.login_view',
        name='pwdtk_test_login'),
    url(r'^logout', 'pwdtk.testviews.logout_view',
        name='pwdtk_test_logout'),
    url(r'^protected', 'pwdtk.testviews.protected',
        name='pwdtk_test_protected'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^ch_passwd/', 'pwdtk.views.password_change', name='password_change'),
]
