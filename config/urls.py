"""app URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
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
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.staticfiles.urls import static
from django.urls import include, path

from rest_framework.authtoken.views import obtain_auth_token


# URLs

urlpatterns = [
    path('accounts/', include(
        'oidc_provider.urls',
        namespace='oidc_provider'
    )),
    path('accounts/login/', LoginView.as_view(), name='login'),
    path('accounts/login/', LogoutView.as_view(
        next_page=settings.LOGIN_URL),
        name='logout'
    ),
    path('api/', include('apps.core.urls')),
    path('api/', include('apps.shop.urls')),
    path('api/auth-token/', obtain_auth_token)
]

if settings.DEBUG:
    urlpatterns += [
        path('admin/', admin.site.urls)
    ]
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
