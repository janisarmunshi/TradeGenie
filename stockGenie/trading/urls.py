from django.contrib import admin
from django.urls import path, include
from trading.views.temp import getConnection, startStrategy
from trading.views.masterdata import syncSymbolsReq
from trading.views.Entities.senitizer import reqSenitization
from trading.views.Strategies.strategyMonitor import reqMonitor
urlpatterns = [
# Help Ajax calls
    path('test',getConnection,name='test'),     
    path('start', startStrategy, name='start'),
    path('symbols', syncSymbolsReq, name='symbols'),
    path('senitize', reqSenitization, name='senitize'),
    path('monitor', reqMonitor, name='monitor'),
]