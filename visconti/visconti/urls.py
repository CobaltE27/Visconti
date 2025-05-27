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
    path('', views.host_match),
    path('join/', views.join_match),
    path('data/', views.data),
    path('setname/', views.set_name),
    path('start/', views.start_match),
    path('choose/', views.receive_choice),
    path('bid/', views.receive_bid),
    path('ready/', views.set_ready),
]

# TODO collapse urls
# TODO persistent users/players leaving
# TODO delta money
# TODO sounds

# TODO ghost cards slot marking
# TODO display days out of total
# TODO animate numbers changing
# TODO clarify colors vs. goods