from django.conf import settings
from django.http import HttpResponse


def password_change(request):
    html = "you should change passwords"
    return HttpResponse(html)
