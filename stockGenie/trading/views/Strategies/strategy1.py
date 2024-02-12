from trading.models import Strategy1Settings, StrategyStatus, Strategis, Strategy1Log
from mainapp.views.socialconnect import Telegram
# from trading.views.Entities.brokerAccount import BrokerAccount
from trading.views.Strategies.strategy import Strategy
import pandas as pd
from mainapp.views.utils import isBlankOrNone
from mainapp.views.socialconnect import Telegram
from celery import shared_task
from mainapp.views.utils import pdSeries
# from mainapp.views.utils import pdSeries
from datetime import datetime
from threading import Thread
from trading.views.Entities.Brokers.broker import Broker
from trading.views.Entities.brokerAccount import BrokerAccount
import pytz 
from decimal import Decimal
from trading.views.Redis.messageQueue import MessageQueue
from trading.views.Strategies.strategy import getStrategyQueueId
from mainapp.models import CustomUser
from trading.models import BrokerAccounts
import json
class Strategy1(Strategy):
    def __init__(self, user) -> None:
        self.code = 'JOBBING'
        StrategyMaster = Strategis.objects.filter(code = self.code).first()
        if not StrategyMaster:
            raise Exception(f'No strategy defined with code {self.code}')
        self.User = user
        self.StrategyMaster = StrategyMaster
        self.isActive = StrategyMaster.isActive
        self.getActiveSetup()
        self.MasterQueue = 'DUMMY'
      

    def getActiveSetup(self):
        lstActiveAccounts = []
        lstActiveScripts = []
        self.Setups = Strategy1Settings.objects.select_related().filter(user = self.User, isActive = True, target__isActive = True).order_by('target_id','exchSeg')
        # self.setupFrame = pd.DataFrame(list(self.Setups.values()))
        # print(self.setupFrame)
        broker = Broker(0)
        for setup in self.Setups:
            if setup.target.id not in lstActiveAccounts:
                lstActiveAccounts.append(setup.target.id)      

            activeScript = {
                'OrderQId'      : broker.getQueueId(self.User.username,setup.target.clientId,setup.exchSeg,'O') if self.requireOrderCallback else None,
                'TickQId'       : broker.getQueueId(self.User.username,setup.target.clientId,setup.exchSeg,'T') if self.requireTickCallback else None,
                'strategyCode'  : self.code,
                'accountId'     : setup.target.id,
                'clientId'      : setup.target.clientId,
                'brokerId'      : setup.target.broker.brokerId,
                'exchange'      : setup.exchSeg,
                'token'         : setup.token,
                'symbol'        : setup.symbol
            }
            if activeScript not in lstActiveScripts:
                lstActiveScripts.append(activeScript)             

        self.ActiveAccounts = lstActiveAccounts
        self.ActiveScripts = lstActiveScripts
        return self.Setups

    def isActive(self, user = None):
        if not self.StrategyMaster.isActive: #check in the master table
            return False
        
        if not user:
            user = self.User
        
        if user == None:
            raise Exception(f'No user defined for strategy code {self.code}')

        setups = self.getActiveSetup()        
        return setups != None

    def getScriptForTickCallback(self):
        # it should be in the format of {'accountId': {accountId}, 'exchange': {exchange}, 'token': {token}, 'symbol':{symbol}}
        return []
    
    @property
    def requireOrderCallback(self):
        return True

    @property
    def requireTickCallback(self):
        return False

    def getStatus(self):
        status = StrategyStatus.objects.filter(user = self.User, strategy = self.StrategyMaster).first()
        if status:
            return status.currStatus
        else:
            return None

    def setStatus(self, status):
        stat = StrategyStatus.objects.filter(user = self.User, strategy = self.StrategyMaster).first()
        if stat:
            stat.currStatus = status
        else:
            stat = StrategyStatus(
                user            = self.User,
                strategy        = self.StrategyMaster,
                currStatus      = status,                
                taskId          = ''
            )
        stat.save()

    def initiate(self):
        try:
            self.setStatus('Initiated')
            return self.isActive

        except Exception as exc:
            print(exc)
            return False
        
    def start(self, brokerAccount):
        self.createInitialOrder(brokerAccount)

        self.processOrderCallback(self)
        self.processTickCallback()

    def createInitialOrder(self, brokerAccount):
        tmpAccountID = 0
        for setup in self.Setups:
            if tmpAccountID != setup.target.id:
                brokerObj = brokerAccount.getBrokerObject(setup.target.id)
            
            simulation = setup.simulate         
            flagReverseTick = False   
            # script = Scripts.objects.filter(exchSeg = setup.exchSeg, token = setup.token).first()

            lotSize = setup.lotSize
            lotSizeSell = setup.lotSizeSell
            tickSize = setup.tickSize
            tickSizeSell = setup.tickSizeSell
            
            Strategy1Log.objects.filter(user = self.User, exchSeg = setup.exchSeg, token = setup.token).exclude(status = 'COMPLETE').delete()
            log = Strategy1Log.objects.filter(user = self.User, exchSeg = setup.exchSeg, token = setup.token, status__in = ['COMPLETE','PARTIAL']).order_by('-updatedOn').first()
            if log:
                if setup.overridePrice > 0:
                    basePrice = setup.overridePrice
                    # setup.overridePrice = 0
                    # setup.save()
                    print(f'Override Price{basePrice}')
                else:                
                    basePrice = log.price
                    print(f'Base Price {basePrice} as per last Transaction')

                if log.orderType == 'SELL':
                    flagReverseTick = True
                    # flagReverseTick = False
                # currStock = log.currStock
            else:            
                # currStock = setup.initialStock
                if setup.overridePrice > 0:
                    basePrice = setup.overridePrice            
                else:
                    basePrice = setup.basePrice
                print(f'no prev record, setup base price {basePrice}')

                  
            if self.getStatus() == 'TERMINATE':
                return


            buyOnly = False
            sellOnly = False 
            if setup.currentStock >= setup.maximumStock:
                sellOnly = True                        
            if setup.currentStock <= setup.minimumStock :                        
                buyOnly = True

            try:                
                self.executeOrderPair(
                    self.User.id, setup.target, setup.exchSeg, setup.token, setup.dayOrders, 
                    basePrice, lotSize, tickSize, buyOnly, sellOnly, simulation, tickSizeSell, lotSizeSell, 
                    flagReverseTick, True, setup.orderCatagory, setup.gttBuyBuffer, setup.gttSellBuffer
                    )

            except Exception as exc:
                # self.Telegram.sendMessage(f"Error: Inital Order Palce")
                print(exc)
                continue
                
        # self.Telegram.sendMessage('Initial Order placed')
        print('Initial Order placed')

    def processOrderCallback(self, strategy):
        if self.requireOrderCallback:
            self.setupFrame = pd.DataFrame(self.ActiveScripts)
            psAccount = pdSeries(self.setupFrame)
            for accountId in psAccount.accountId:
                psExchange = pdSeries(self.setupFrame,'accountId',accountId)
                for exchange in psExchange.exchange:
                    # workerS1OrderCallback(strategy.code, str(accountId), exchange)
                    workerS1OrderCallback.delay(strategy.code, str(accountId), exchange)
            
        return True

    def processTickCallback(self):
        if self.requireTickCallback:
            pass

        return True

    def createOrderLog(self, userid, orderId, brokerAccountId, verboseOrder, status = ''):

        log = Strategy1Log.objects.filter(user_id = userid, target_id = brokerAccountId, orderId = orderId).first()
        if log:
            log.tradeDate   = datetime.now(pytz.timezone('Asia/Kolkata')) 
            log.quantity    = verboseOrder['quantity']
            log.price       = verboseOrder['price']
            if status != '':
                log.status      = status
            log.save()
            
        else:
            if status == '':
                status = 'OPEN'
            log = Strategy1Log(
                user_id         = userid,
                target_id       = brokerAccountId,  
                exchSeg         = verboseOrder['exchSeg'],
                token           = verboseOrder['token'],
                orderId         = orderId,
                tradeDate       = datetime.now(pytz.timezone('Asia/Kolkata')),
                quantity        = verboseOrder['quantity'],
                price           = verboseOrder['price'],
                orderType       = verboseOrder['tranType'],
                intraday        = True if verboseOrder['variety'] == 'NORMAL' else False,
                currStock       = 0,
                status          = status,
                orderCategory   = verboseOrder['orderCategory']
            )
            log.save()

        return log  


    def  executeOrderPair(self,
        userid, target, exchSeg, token, numberOfOrders, 
        basePrice,  lotSizeBuy,    tickSizeBuy,   
        buyOnly=False, sellOnly = False, simulation=False, tickSizeSell = 0, lotSizeSell = 0, 
        flagReverseTick = False, createLog = True,
        orderCatagory = 'Normal', gttBuyBuffer = 0, gttSellBuffer = 0
        ):

        # workerOrderPair(self.code,
        #     userid, target.id, exchSeg, token, numberOfOrders, 
        #     basePrice,  lotSizeBuy,    tickSizeBuy,  buyOnly, sellOnly, 
        #     simulation, tickSizeSell, lotSizeSell, 
        #     flagReverseTick, createLog,
        #     orderCatagory, gttBuyBuffer, gttSellBuffer
        # )
        workerOrderPair.delay(self.code,
            userid, target.id, exchSeg, token, numberOfOrders, 
            basePrice,  lotSizeBuy,    tickSizeBuy,  buyOnly, sellOnly, 
            simulation, tickSizeSell, lotSizeSell, 
            flagReverseTick, createLog,
            orderCatagory, gttBuyBuffer, gttSellBuffer
        )

@shared_task(bind=True)
def workerS1OrderCallback(self, strategyCode, accId, exchange):
    accountId = int(accId)
    ba = BrokerAccounts.objects.filter(id = accountId).first()
    if not ba:
        return None
    
    strategy = Strategy.getStrategyInstance(ba.user,strategyCode)
    brokerAccount = BrokerAccount(ba.user,accountId)
    brokerAccount.Connect(accountId,True)
    connObj = brokerAccount.getBrokerObject(accountId)
    if connObj is None:
        print('error connection')
           
    setup = strategy.Setups.filter(target_id = accountId).first()
    broker = Broker(brokerAccount.BrokerAccounts[0].broker.brokerId)
    PROCESS_QUEUE = f'{broker.getQueueId(brokerAccount.User.username,brokerAccount.BrokerAccounts[0].clientId,exchange,"O")}:{strategy.code}'
    queue = MessageQueue(PROCESS_QUEUE)

    while broker.isMarketOpen(exchange):    
        queue.setLastAccess()
        
        ord = queue.brpop()
        if ord == None:
            continue
        try:
            print(f'Read data {ord} for QID {PROCESS_QUEUE}')
            if ord.get('type','') == 'TERMINATE':
                queue.clearQueue()
                break

            buyOnly = False
            sellOnly = False

            logTrade = False
            flagReverseTick = False
            if ord['status'] in ['COMPLETE','PARTIAL']:
                if ord['status'] == 'COMPLETE':
                    logTrade = True
            else:                 
                continue
            setup = strategy.Setups.filter(exchSeg = ord['exchSeg'], token = ord['token'], target_id = accountId ).first() 

            logStock = Strategy1Log.objects.filter(user = strategy.User, exchSeg = ord['exchSeg'], token = ord['token'], status = 'COMPLETE').order_by('-updatedOn').first()
            if logStock:                                    
                currStock = logStock.currStock
            else:                            
                if setup:
                    currStock = setup.initialStock
                else:
                    currStock = 0

            currLog = Strategy1Log.objects.filter( target_id = accountId, orderId = ord['orderId']).first()
            if currLog:
                if currLog.status in ['COMPLETE']:
                    continue            
                if broker.canPlaceOrder(exchange) and  strategy.isActive == False:
                    continue

                lotSizeBuy = setup.lotSize
                lotSizeSell = setup.lotSizeSell
                basePrice = Decimal(ord['limitPrice'])
                if ord['tranType'] == 'BUY':                              

                    currStock += currLog.quantity
                    setup.currentStock += currLog.quantity

                else:
                    flagReverseTick = True

                    currStock -= currLog.quantity
                    setup.currentStock -= currLog.quantity


                currLog.status      = ord.get('status')
                # currLog.price       = ltp
                currLog.currStock   = currStock
                currLog.updatedOn   = datetime.now(pytz.timezone('Asia/Kolkata'))                            
                currLog.save()
                
                setup.overridePrice = basePrice
                setup.save()                
                message = f"{ord['tranType']}-{setup.exchSeg}:{ord['symbol']} - Qty ( {currLog.quantity} @ {basePrice} )"                                
                # strategy.Telegram.sendMessage(message)

                # if waitForMarketOpen(0, setup.exchSeg) == False:
                #     print(f'Market {setup.exchSeg} closed, terminating worker')
                #     # strategy.ConnectionObject.closeWebSocket(ws)
                #     strategy.setStatus('TERMINATE')
                #     return
                                
                if logTrade and setup:
                    if setup.currentStock >= setup.maximumStock:
                        sellOnly = True                        
                    if setup.currentStock <= setup.minimumStock :                        
                        buyOnly = True
                    # telegram.sendMessage('Trying to place subsequent order')
                    
                    # workerOrderPair(strategy.code, strategy.User.id, setup.target.id, setup.exchSeg, setup.token, 1, 
                    #                 basePrice, lotSizeBuy,setup.tickSize, 
                    #                 True, False, setup.simulate, setup.tickSizeSell, lotSizeSell, flagReverseTick)
                    
                    workerOrderPair.delay(strategy.code, strategy.User.id, setup.target.id, setup.exchSeg, setup.token, 1, 
                                    basePrice, lotSizeBuy,setup.tickSize, 
                                    buyOnly, sellOnly, setup.simulate, setup.tickSizeSell, setup.lotSizeSell, flagReverseTick)
                   
        except Exception as exc:
            print(exc)                
            # telegram.sendMessage('Error processing cycle order update callback')

def thread1TickCallback():
    pass

@shared_task(bind=True)
def  workerOrderPair(self,
    strategyCode, userid, targetId, exchSeg, token, numberOfOrders, 
    basePrice,  lotSizeBuy,    tickSizeBuy,   
    buyOnly=False, sellOnly = False, simulation=False, tickSizeSell = 0, lotSizeSell = 0, 
    flagReverseTick = False, createLog = True,
    orderCatagory = 'Normal', gttBuyBuffer = 0, gttSellBuffer = 0
    ):

    user = CustomUser.objects.filter(id = userid).first()
    strategy = Strategy.getStrategyInstance(user,strategyCode)
    brokerAccount = BrokerAccount(user, targetId)
    brokerAccount.Connect(targetId, True)
    # OrderCatagory = 'All', 'GTT','Normal'
    broker = Broker(brokerAccount.BrokerAccounts[0].broker.brokerId)
    if broker.canPlaceOrder(exchSeg) == False:    
        return []
        
    # conn = Connection.get('Connection')
    brokerObj = brokerAccount.getBrokerObject(targetId)

    lstOrd = []    
    if tickSizeSell == 0:
        tickSizeSell = tickSizeBuy

    if lotSizeSell == 0:
        lotSizeSell = lotSizeBuy


    orderId = ''
    # Check for any Open Orders
    checkLog = Strategy1Log.objects.filter(
                    user_id     = userid, 
                    target_id   = targetId, 
                    token       = token,
                    orderCategory = orderCatagory
                    ).exclude(status = 'COMPLETE')

    buyLog = checkLog.filter(orderType   = 'BUY')
    sellLog = checkLog.filter(orderType   = 'SELL')
    for i in range(int(numberOfOrders)):
        print('consecutive order loop')
        if flagReverseTick:
            buyPrice = round(float(basePrice) - ( float(tickSizeSell) * float(i+1) ), 2)
            sellPrice = round(float(basePrice) + ( float(tickSizeBuy) * float(i+1) ), 2)
        else:
            buyPrice = round(float(basePrice) - ( float(tickSizeBuy) * float(i+1) ), 2)
            sellPrice = round(float(basePrice) + ( float(tickSizeSell) * float(i+1) ), 2)

        if sellOnly == False:
            iBuyLog = len(buyLog)

            if i < iBuyLog:
                log = buyLog[i]
                lstOrder = brokerObj.readOrderBook(log.orderId, orderCatagory)
                if lstOrder[0]['status'] in ['OPEN']:
                    action = 'Update'                    
                    orderId = log.orderId
                else:
                    action = 'Create'
                    orderId = 0
            else:
                action = 'Create'
                orderId = 0
            # orderparams = prepareParams(
            #     action, token, exchSeg, 'BUY',buyPrice, lotSize, False, orderId)        
            print('buy order')
            # brokerObj

            # lstVerboseOrder = brokerObj.VerboseOrder(
            #     'NORMAL', exchSeg, token, '', 'BUY', 'LIMIT', 'DELIVERY', buyPrice, lotSizeBuy, 0, 'DAY', 0, 0, 0, orderId, orderCatagory, gttBuyBuffer, gttSellBuffer)
            # if type(lstVerboseOrder) != list:
            #     lstVerboseOrder = [lstVerboseOrder]
            
            
            Order = brokerAccount.submitOrder(action, targetId, 'NORMAL', exchSeg, token, '', 
                                        'BUY', 'LIMIT', 'DELIVERY', buyPrice, lotSizeBuy, 0, 'DAY', 0, 0, 0,orderId, simulation)

            if not isBlankOrNone(Order['orderId']):                
                orderId = Order.get('orderId','')
                lstOrderBook = brokerAccount.readOrderBook(targetId,orderId, orderCatagory)      
                if len(lstOrderBook) > 0:
                    # strategy.createOrderLog(strategy.User.id, orderId, target.id, Order, status = lstOrderBook[0].get('status',''))
                    strategy.createOrderLog(strategy.User.id, orderId, targetId, Order, status = 'OPEN')

                lstOrd.append(Order) 
            

        if buyOnly == False:
            iSellLog = len(sellLog)

            if i < iSellLog:
                log = sellLog[i]                
                lstOrder = brokerAccount.readOrderBook(targetId, log.orderId, OrderType = 'All')
                if lstOrder[0]['status'] in ['OPEN']:                
                    action = 'Update'
                    
                    orderId = log.orderId
                else:
                    action = 'Create'
                    orderId = 0
            else:
                action = 'Create'
                orderId = 0


            Order = brokerAccount.submitOrder(action, targetId, 'NORMAL', exchSeg, token, '', 
                                        'SELL', 'LIMIT', 'DELIVERY', sellPrice, lotSizeSell, 0, 'DAY', 0, 0, 0,orderId, simulation)
            

            if not isBlankOrNone(Order['orderId']):                
                orderId = Order.get('orderId','')
                # if lstOrder[0]['orderStatus'] == ['OPEN','PENDING','COMPLETE']:
                lstOrderBook = brokerAccount.readOrderBook(targetId,orderId, orderCatagory)      
                if len(lstOrderBook) > 0:
                    # strategy.createOrderLog(strategy.User.id, orderId, target.id, Order, status = lstOrderBook[0].get('status',''))
                    strategy.createOrderLog(strategy.User.id, orderId, targetId, Order, status = 'OPEN')

                lstOrd.append(Order)  

    # return lstOrd
