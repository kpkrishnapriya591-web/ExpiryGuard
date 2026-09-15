from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect


def root_redirect(request):
    return redirect('/staff/login/')


urlpatterns = [
    path('admin/', admin.site.urls),

    # Admin website
    path('', include('main.urls')),

    # Staff website
    path('staff/', include('staff.urls')),

    path('', root_redirect, name='root'),
]