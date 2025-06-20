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

urlpatterns = [
    path('admin/', admin.site.urls),
    path('host/', views.host_match, name='host_match'),
    path('', views.load_match, name='load_match'),
    path('join/', views.join_match, name='join_match'),
]

# TODO persistent users/players leaving
# TODO sounds
# TODO favicon
# TODO full rules
# TODO break up css
# TODO end game graphs
# TODO ai players

# TODO animate numbers changing?
# TODO dock or tide animations