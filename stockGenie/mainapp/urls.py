from django.contrib import admin
from django.urls import path, include
from .views.render import home, showLogin, test, index, doLogout  #LoginView
from .views.helper import *
urlpatterns = [
# Help Ajax calls
    path("helpHeader/",helpHeader, name="helpHeader"),
    path("helpData/", helpData, name="helpData"),


    path('index/', index, name='index'),
    path('home/', home, name='home'),
    path('', home, name='home'),

    path('login', showLogin, name='login'),
    path('logout', doLogout, name='logout'),
    # path('api/login/',LoginView.as_view(),name='apilogin'),
    path('test',test,name='test'),     
    path('test1',test,name='test1'),     
]