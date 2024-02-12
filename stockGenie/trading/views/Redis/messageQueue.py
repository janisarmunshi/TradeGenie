from redis import Redis
from json import dumps as jsondumps, loads as jsonloads
import time
import pytz

from datetime import datetime
from mainapp.models import CustomUser
from trading.models import BrokerAccounts


class MessageQueue():
    def __init__(self, QueueId):    
        self.QueueId = QueueId
        self.Redis = Redis()
    
    # @property
    def getLastAccess(self, QueueId = None):
        # https://roman.pt/posts/time-series-caching/
        if QueueId == None:
            QueueId = self.QueueId
        try:            
            return datetime.strptime(jsonloads(self.Redis.get(QueueId)), '%Y-%m-%d %H:%M:%S.%f%z')
        except Exception:
            return None

    # @lastAccess.setter
    def setLastAccess(self,QueueId = None):
        # https://roman.pt/posts/time-series-caching/
        if QueueId == None:
            QueueId = self.QueueId

        self.Redis.set(QueueId,str(datetime.now(pytz.timezone('Asia/Kolkata'))))

    def clearQueue(self, QueueId=None):
        if QueueId == None:
            QueueId = self.QueueId
        while self.Redis.rpop(QueueId) is not None:
            pass        
        return True

    def lpush(self, message:dict, QueueId=None): 
        if QueueId == None:
            QueueId = self.QueueId                        
        return self.Redis.lpush(QueueId,jsondumps(message))
    
    def rpush(self, message:dict, QueueId=None):
        if QueueId == None:
            QueueId = self.QueueId        
        return self.Redis.rpush(QueueId,jsondumps(message))

    def rpop(self, QueueId=None):
        try:
            if QueueId == None:
                QueueId = self.QueueId        
            if self.Redis.llen(QueueId) > 0:
                return jsonloads(self.Redis.rpop(QueueId))                
            else:
                return None
        except Exception as ex:
            print(ex)

    def lpop(self, QueueId=None):
        try:
            if QueueId == None:
                QueueId = self.QueueId        
            if self.Redis.llen(QueueId) > 0:
                return jsonloads(self.Redis.lpop(QueueId))    
            else:
                return None
        except Exception as ex:
            print(ex)

    def brpop(self, QueueId=None, timeout=1):
        try:
            if QueueId == None:
                QueueId = self.QueueId        
            if self.Redis.llen(QueueId) > 0:
                return jsonloads(self.Redis.brpop(QueueId,timeout)[1])           
            else:
                time.sleep(timeout)
                return None
        except Exception as ex:
            print(ex)            

    def blpop(self, QueueId=None, timeout=1):
        try:
            if QueueId == None:
                QueueId = self.QueueId        
            if self.Redis.llen(QueueId) > 0:
                return jsonloads(self.Redis.blpop(QueueId, timeout)[1])    
            else:
                time.sleep(timeout)
                return None
        except Exception as ex:
            print(ex)            