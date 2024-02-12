from functools import lru_cache
from django.db.models import Q
from mainapp.models import UserSocialProfile
from trading.models import MarketSessions
from mainapp.views.utils import isBlankOrNone
from time import time as tm
from datetime import time

class CACHE_SETTINGS:
    REFRESH_CACHE_WEEKLY = 60 * 60 * 24 * 7 #Daily Seconds * minutes * hours
    REFRESH_CACHE_DAILY = 60 * 60 * 24      #Daily Seconds * minutes * hours
    REFRESH_CACHE_HOURLY = 60 * 60          #Hourly Seconds * minutes
    REFRESH_CACHE_12HOUR = 60 * 60 * 12     #Hourly Seconds * minutes
    REFRESH_CACHE_5MINUTES = 60 * 5         #Hourly Seconds * minutes
    REFRESH_CACHE_10MINUTES = 60 * 10       #Hourly Seconds * minutes
    REFRESH_CACHE_30MINUTES = 60 * 30       #Hourly Seconds * minutes

def get_ttl_hash(seconds= CACHE_SETTINGS.REFRESH_CACHE_DAILY):
    """Return the same value withing `seconds` time period"""
    return round(tm() / seconds)

@lru_cache(maxsize=10)
def getUserSocialProfile(userid, TTLHash = get_ttl_hash(CACHE_SETTINGS.REFRESH_CACHE_DAILY) ):
    del TTLHash
    return UserSocialProfile.objects.filter(user_id = userid).first()

@lru_cache(maxsize=24)
def getMarketSessions(brokerId, exchange='MCX', TTLHash = get_ttl_hash(CACHE_SETTINGS.REFRESH_CACHE_DAILY)):
    del TTLHash
    exchngeSessions = {
        'BSE': [(time(9, 0, 0), time(9, 6, 0)), (time(9, 15, 0), time(15, 30, 0))],
        'NSE': [(time(9, 0, 0), time(9, 6, 0)), (time(9, 15, 0), time(15, 30, 0))],
        'CDS': [(time(9, 0, 0), time(17, 0, 0))],
        'MCX': [(time(9, 0, 0), time(17, 0, 0))],
    }

    qFilter = Q()
    if brokerId > 0:
        qFilter &= Q(broker__id = brokerId)
    
    if isBlankOrNone(exchange):
        qFilter &= Q(exchange__code = exchange)

    sessions = MarketSessions.objects.filter(qFilter)
    if sessions:
        marketSessions =  [(session.startTime,session.EndTime) for session in sessions]
    else:
        marketSessions = exchngeSessions.get(exchange)

    return marketSessions


    
