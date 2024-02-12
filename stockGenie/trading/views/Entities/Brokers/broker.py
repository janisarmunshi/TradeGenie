
from datetime import datetime, time
from django.db.models import Q
from functools import lru_cache
from mainapp.views.cacheRoutines import CACHE_SETTINGS, get_ttl_hash
from trading.models import Scripts, MarketSessions

from mainapp.views.utils import isBlankOrNone
import pytz
from time import time as tm
from trading.views.Entities.exchange import Exchange

BROKERS = { 1 : 'ANGEL', 2 : 'ZERODHA', 3 : 'FINVASIA', 4 : 'FYERS', 5 : 'BNRATHI', 6 : 'ALICEBLUE'}
EXCHANGE_SESSIONS = {
    'BSE': [(time(9, 0, 0), time(9, 6, 0)), (time(9, 15, 0), time(15, 30, 0))],
    'NSE': [(time(9, 0, 0), time(9, 6, 0)), (time(9, 15, 0), time(15, 30, 0))],
    'CDS': [(time(9, 0, 0), time(17, 0, 0))],
    'MCX': [(time(9, 0, 0), time(23, 30, 0))],
} 
class Broker():
    ANGEL       = 1
    ZERODHA     = 2
    FINVASIA    = 3
    FYERS       = 4
    BNRATHI     = 5
    ALICEBLUE   = 6      
    def __init__(self, brokerId) -> None:
        self.BrokerId = brokerId

    @lru_cache(maxsize=4)
    def getMarketSessions(self, exchange, TTLHash = get_ttl_hash(CACHE_SETTINGS.REFRESH_CACHE_DAILY)):
        del TTLHash

        qFilter = Q(broker__brokerId = self.BrokerId, exchange__code = exchange)        
        sessions = MarketSessions.objects.filter(qFilter)
        if sessions:
            marketSessions =  [(session.startTime,session.EndTime) for session in sessions]    
            return marketSessions
        else:
            exchange = Exchange(exchange)
            marketSessions = exchange.getMarketSessions()
            if marketSessions:
                return  marketSessions
            else:           
                marketSessions = EXCHANGE_SESSIONS.get(exchange.Exchange)    
                return marketSessions        

    def getQueueId(self, username, clientId, exchange, type):
        return f'{username}:{clientId}:{exchange}:{type}'       

    # @property
    def canPlaceOrder(self, exchSeg = 'MCX'):
        MarketOpen = False
        currDate = datetime.now(pytz.timezone('Asia/Kolkata'))
        currTime = currDate.time()        
        sessions = self.getMarketSessions(exchSeg)        
        for session in sessions:
            if currTime > session[0] and currTime < session[1] and currDate.weekday() < 5:
                MarketOpen = True
                break
        return MarketOpen
    

    def isMarketOpen(self, exchSeg = 'NSE'):
        exchange = Exchange(exchSeg)

        sessions = self.getMarketSessions(exchSeg) 
        currDate = datetime.now(pytz.timezone('Asia/Kolkata'))
        currTime = currDate.time()  
        startTime = sessions[0][0]
        endTime = sessions[-1][1]

        if currTime > startTime and currTime < endTime and currDate.weekday() < 5:
            return True
        else:
            return False
        
    
    @lru_cache(maxsize=24)
    def getScript(self, exchSeg, token, symbol=None, TTLHash = get_ttl_hash(CACHE_SETTINGS.REFRESH_CACHE_DAILY)):
        ''' get script as per the broker. 
        1. either token or symbol is to be provided
        2. if script is searched by both, token will get the preference
        3. if searched by symbol, broker id should be Non Zero
        For all invalid case None is returned instead of raising error 
        '''

        del TTLHash
        if isBlankOrNone(token) and isBlankOrNone(symbol):
            return None
        
        if not isBlankOrNone(token) and isBlankOrNone(symbol) == False:
            symbol = None

        if not isBlankOrNone(symbol) and self.BrokerId == 0:
            return None


        qFilter = Q(exchSeg=exchSeg)
        if not isBlankOrNone(symbol):
            if self.BrokerId in [self.FINVASIA, self.BNRATHI]:
                qFilter &= Q(symbolFinvasia=symbol)

        if not isBlankOrNone(token):
            qFilter &= Q(token=token)

        script = Scripts.objects.filter(qFilter).first()
        if self.BrokerId in [self.BNRATHI, self.FINVASIA]:
            script.symbol = script.symbolFinvasia

        return script

    def VerboseOrder(
            self, variety, exchange, token, symbol, tranType, priceType, prodType, price, quantity, 
            disclQty, validity = 'DAY', stopPrice = 0, stopLoss = 0, takeProfit = 0, orderId ='', 
            orderCategory = 'Normal', gttBuyBuffer = 0, gttSellBuffer = 0):
        # script = self.getScript(exchange,symbol,token)
        tsymb = symbol
        # script = getScriptBySymbol(exchange, symbol, self.brokerId, token)
        script = Scripts.objects.filter(exchSeg=exchange,token=token).first()
        if script == None:
            return None
        
        if exchange == 'CDS' and prodType == 'DELIVERY':
            prodType = 'MARGIN'
            if self.BrokerId in [Broker.FINVASIA, Broker.BNRATHI]:
                tsymb = script.symbolFinvasia
            else:
                tsymb = script.symbolFyers
        else:
            tsymb = script.symbol
        if priceType == 'MARKET':
            price = 0

        lstVerbose = []
        order = {
            "orderId"       : orderId,
            "variety"       : variety,
            "exchSeg"       : exchange,
            "symbol"        : tsymb, 
            "token"         : script.token,            
            "tranType"      : tranType,
            "priceType"     : priceType, 
            "productType"   : prodType,            
            "price"         : round(price,2),
            "quantity"      : quantity,            
            "stopLoss"      : round(stopLoss,2),
            "validity"      : validity,
            "stopPrice"     : round(stopPrice,2),
            "takeProfit"    : round(takeProfit,2),
            "disclosedQty"  : disclQty, 
            "orderCategory" : orderCategory,
            "gttBuyBuffer"  : gttBuyBuffer, 
            "gttSellBuffer" : gttSellBuffer
            }
        lstVerbose.append(order)
        return lstVerbose
