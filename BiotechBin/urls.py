from django.urls import path
from . import views
from django.contrib.auth.views import LoginView

urlpatterns = [
    path('', views.home, name='home'),
    path('tickers/', views.tickers, name='tickers'),
    path('events/', views.events, name='events'),
    path('login/', LoginView.as_view(template_name='BiotechBin/login.html'), name='login'),
    path('logout/', views.custom_logout, name='logout'),
]