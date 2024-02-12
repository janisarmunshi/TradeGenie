from django.contrib import admin
from trading.models import MarketSessions, Strategis, Strategy1Settings, BrokerAccounts, Brokers
# Register your models here.

admin.site.register(Brokers)
admin.site.register(BrokerAccounts)
admin.site.register(MarketSessions)
admin.site.register(Strategis)
admin.site.register(Strategy1Settings)