from trading.views.Strategies import strategy 
from trading.views.Strategies.strategyManager import StrategyManager
from trading.views.Entities.Brokers.broker import Broker
import pandas as pd
from time import sleep
from mainapp.views.utils import pdSeries
from celery import shared_task
from json import dumps as jsondumps, loads as jsonloads
from trading.views.Redis.messageQueue import MessageQueue
from django.conf import settings
import pytz
from datetime import datetime
from mainapp.views.socialconnect import Telegram
from django.http import HttpResponse

class StrategyMonitor():
    def __init__(self, user) -> None:
        self.User = user

    def startMonitor(self) -> None:

        self.Manager = StrategyManager(self.User)
        self.Manager.getActiveStrategies()
        series = None
        if len(self.Manager.ActiveScripts) > 0 :
            
            scriptFrame = pd.DataFrame(self.Manager.ActiveScripts)
            scriptSeries = pdSeries(scriptFrame)
            for OrderQId in scriptSeries.OrderQId:
                if OrderQId is not None:
                    workerStrategyMonitor(self.User.id, OrderQId, jsondumps(self.Manager.ActiveScripts))
                    

            for TickQId in scriptSeries.TickQId:
                if TickQId is not None:
                    workerStrategyMonitor(self.User.id, TickQId, jsondumps(self.Manager.ActiveScripts))
                    

            print('Monitor process Assginment completed')


@shared_task(bind=True)
def workerStrategyMonitor(self, UserId, QueueId, lstActiveScripts):
    moniterTime = settings.WORKER_MONITOR_TIME
    lstActiveScripts = jsonloads(lstActiveScripts)
    scriptFrame = pd.DataFrame(lstActiveScripts)
    series = None
    tg = Telegram(UserId)
    ordSeries = pdSeries(scriptFrame,'OrderQId',QueueId)
    tickSeries = pdSeries(scriptFrame,'TickQId',QueueId)

    if len(ordSeries.strategyCode) == 0:
        series = tickSeries

    if len(tickSeries.strategyCode) == 0:
        series = ordSeries

    if not series.empty:

        broker = Broker(series.brokerId[0])
        mq = MessageQueue(QueueId)
        while broker.isMarketOpen(series.exchange[0]):
            la = mq.getLastAccess(QueueId) 
            if la:
                diff = datetime.now(pytz.timezone('Asia/Kolkata')) - la
                diff = int(diff.total_seconds())
                if diff > moniterTime:
                    
                    tg.sendMessage(f'Message Queue {QueueId} has stoped from {diff} second(s)')

            for scode in series.strategyCode:
                QSCode = f'{QueueId}:{scode}'
                la = mq.getLastAccess(QSCode)
                if la:
                    diff = datetime.now(pytz.timezone('Asia/Kolkata')) - la 
                    diff = int(diff.total_seconds())
                    if diff > moniterTime:                    
                        tg.sendMessage(f'Message Queue {QSCode} has stoped from {diff} second(s)')
                        
            sleep(moniterTime)
    print(f'Queue Monitoring for {QueueId} is ended')



def reqMonitor(request):
    monitor = StrategyMonitor(request.user)
    monitor.startMonitor()
    return HttpResponse('Monitor started')