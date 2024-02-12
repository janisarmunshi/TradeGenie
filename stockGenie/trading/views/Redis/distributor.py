from redis import Redis
from json import dumps as jsondumps, loads as jsonloads
import time
from trading.views.Redis.messageQueue import MessageQueue
from trading.views.Entities.Brokers.broker import Broker
from mainapp.models import CustomUser
from trading.models import BrokerAccounts
from celery import shared_task
import pandas as pd
from mainapp.views.utils import pdSeries
from trading.views.Strategies.strategy import getStrategyQueueId
class Distributor():
    def __init__(self, user: CustomUser, lstActiveScripts:list = None):
        self.user = user
        self.ActiveScripts = lstActiveScripts        
        self.Queue = MessageQueue('DUMMY')

    def startDistribution(self, lstActiveScripts):

        if len(lstActiveScripts) > 0 :
            
            scriptFrame = pd.DataFrame(lstActiveScripts)
            scriptSeries = pdSeries(scriptFrame)
            for OrderQId in scriptSeries.OrderQId:
                if OrderQId is not None:
                    mq = MessageQueue(OrderQId)
                    mq.clearQueue()                    
                    workerStartDistribution.delay(OrderQId, jsondumps(lstActiveScripts))
                    # workerStartDistribution(OrderQId, jsondumps(lstActiveScripts))

            for TickQId in scriptSeries.TickQId:
                if TickQId is not None:
                    mq = MessageQueue(TickQId)
                    mq.clearQueue()                                     
                    # workerStartDistribution.delay(TickQId, jsondumps(lstActiveScripts))
                    workerStartDistribution(TickQId, jsondumps(lstActiveScripts))

            print('Distribution Assginment completed')

@shared_task(bind=True)
def workerStartDistribution(self, QueueId, lstActiveScripts):
    lstActiveScripts = jsonloads(lstActiveScripts)
    scriptFrame = pd.DataFrame(lstActiveScripts)
    series = None
    ordSeries = pdSeries(scriptFrame,'OrderQId',QueueId)
    tickSeries = pdSeries(scriptFrame,'TickQId',QueueId)

    if len(ordSeries.strategyCode) == 0:
        series = tickSeries

    if len(tickSeries.strategyCode) == 0:
        series = ordSeries

    broker = Broker(series.brokerId[0])
    mq = MessageQueue(QueueId)
    while broker.isMarketOpen(series.exchange[0]):
        mq.setLastAccess()
        data = mq.brpop()
        if data is not None:
            tkf = scriptFrame.loc[scriptFrame['token'] == str(data.get('token'))]
            for i in range(len(tkf)):
                mq.lpush(data, f'{QueueId}:{tkf.strategyCode.tolist()[i]}')
                print(f'data {data} pushed to {QueueId}:{tkf.strategyCode.tolist()[i]}')




        