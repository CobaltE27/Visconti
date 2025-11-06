"""
URL configuration for visconti project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.contrib import admin
from django.urls import path
from game import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('host/', views.host_match, name='host_match'),
    path('', views.load_match, name='load_match'),
    path('join/', views.join_match, name='join_match'),
    path('test/', views.test_match, name='test_match'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# TODO persistent users/players leaving
# TODO break up css
# TODO end game graphs
# TODO error messages
# TODO harbor sound vs claim sound
# TODO obfuscate deck to bots