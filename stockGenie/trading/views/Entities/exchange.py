from functools import lru_cache
from mainapp.views.cacheRoutines import get_ttl_hash, CACHE_SETTINGS
from trading.models import MarketSessions
from django.db.models import Q

class Exchange():
    def __init__(self, exchange):
        self.Exchange = exchange

    @lru_cache(maxsize=6)
    def getMarketSessions(self, TTLHash = get_ttl_hash(CACHE_SETTINGS.REFRESH_CACHE_DAILY)):
        del TTLHash

        qFilter = Q(broker = None, exchange__code = self.Exchange)        
        sessions = MarketSessions.objects.filter(qFilter)
        if sessions:
            marketSessions =  [(session.startTime,session.EndTime) for session in sessions]    
            return marketSessions
        else:
            return None