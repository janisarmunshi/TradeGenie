# from trading.views.broker import Broker
from trading.models import BrokerAccounts

from trading.views.Entities.Brokers.broker import Broker
from trading.views.Entities.Brokers.bnrathi import BNRathi
from django.db.models import Q
from mainapp.views.logger import logging
import datetime

class BrokerAccount():
    # create object for each broker accounts and store as class variable
    def __init__(self, user, accountId=None) -> None:
        qFilter = Q(user = user)
        if accountId:
            qFilter &= Q(id = accountId)
        self.User = user        
        self.BrokerAccounts = BrokerAccounts.objects.filter(qFilter)
        self.AccountId = accountId
        

    def getAccountByClientId(self, clientId):
        return self.BrokerAccount.filter(clientId = clientId)
    
    def getAccountByNickName(self, nickName):
        return self.BrokerAccount.filter(nickName = nickName)

    def getAccount(self, accountId=None):
        if accountId is None:
            accountId = self.AccountId
        if accountId:
            return self.BrokerAccounts.filter(id = accountId)
        else:
            return self.BrokerAccounts

    def setDefaultAccountId(self, accountId) -> None:
        self.AccountId = accountId
        self.BrokerAccount = self.getAccount(accountId)

    @property
    def DefaultAccount(self):
        return self.BrokerAccount.filter(id = self.AccountId)

    # def getTOTP(self, accountId = None) -> int:
    #     account = self.getAccount(accountId)
    #     if account:
    #         totp = pyotp.TOTP(account.factor2Secret)
    #         return totp.now()
    #     else:
    #         raise Exception('No Default/Specific Account found ')
    
    def Connect(self, accountId=None, sessionOnly = False):
        logging.debug(f'connection attempted for Account Id {accountId}')
        lstBrokerObject = []
        accounts = self.getAccount(accountId)
        for account in accounts:
            if account.broker.brokerId in [Broker.BNRATHI, Broker.FINVASIA]:
                brokerObject = BNRathi(account.broker.brokerId,account.id)
                brokerObject.getConnectionObject(sessionOnly)
                lstBrokerObject.append(brokerObject)
        if len(lstBrokerObject) > 0:
            logging.debug(f'connection successfull for Account Id {accountId}')
        else:
            logging.debug(f'connection was not made for Account Id {accountId}')
            
        self.BrokerObjets = lstBrokerObject

    def getBrokerObject(self,accountId):
        if self.BrokerObjets == None:
            raise Exception('No Broker Objects, did you call Connect to get the broker objects?')
        for object in self.BrokerObjets:
            if object.Account.id == accountId:
                return object


    def readOrderBook(self, accountId, orderId='', OrderType = 'All'):
        # OrderType = 'All', 'GTT','Normal'
        brokerObj = self.getBrokerObject(accountId)
        lstOrderBook = []

        orderBook = brokerObj.readOrderBook(orderId, OrderType)
        for order in orderBook:
            lstOrderBook.append(order)

        self.orderBook = lstOrderBook
        return lstOrderBook                
    
    def VerboseOrder(
            self, variety, exchange, token, symbol, tranType, priceType, prodType, price, quantity, 
            disclQty, validity = 'DAY', stopPrice = 0, stopLoss = 0, takeProfit = 0, orderId ='', orderCatoery = 'Normal', gttBuyBuffer = 0, gttSellBuffer = 0):
        lstVerbose = []
        for obj in self.BrokerObjets:                    
            lstOrder = obj.VerboseOrder(
                variety, exchange, token, symbol, tranType, priceType, prodType, price, quantity, disclQty, validity, stopPrice, stopLoss, takeProfit, orderId,
                orderCatoery, gttBuyBuffer, gttSellBuffer
                )
            for order in lstOrder:
                lstVerbose.append(order)
        return lstVerbose    
    
    def StarndardOrder(
            self, variety, exchange, token, symbol, tranType, priceType, prodType, price, quantity, 
            disclQty, validity = 'DAY', stopPrice = 0, stopLoss = 0, takeProfit = 0, orderId ='', 
            orderCategory = 'Normal', gttBuyBuffer = 0, gttSellBuffer = 0):
        broker = Broker(0)
        script = broker.getScript(exchange, token, symbol)
        
        if script == None:
            return
        
        if ( exchange == 'CDS' or exchange == 'MCX') and prodType == 'DELIVERY':
            prodType = 'MARGIN'

        tsymb = script.symbol

        # if priceType == 'MARKET':
        #     price = 0
                    
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
        
        return order



    def submitOrder(self, action, accountId, variety, exchange, token, symbol, tranType, priceType, prodType, price, quantity, 
                        disclQty, validity = 'DAY', stopPrice = 0, stopLoss = 0, takeProfit = 0, orderId ='', simulation = False,
                        orderCatoery = 'Normal', gttBuyBuffer = 0, gttSellBuffer = 0):

        standardOrder = self.StarndardOrder(
                                variety, exchange, token, symbol, tranType, priceType, prodType, price, quantity, 
                                disclQty, validity, 0, stopLoss, takeProfit, orderId, 
                                orderCatoery, gttBuyBuffer, gttSellBuffer)        
        if simulation:

            orderId = datetime.now().strftime('%Y%m%d%H%M%S%f')
            standardOrder['orderId'] = orderId
            standardOrder['status'] = 'OPEN'            
            
        else:
            brokerObj = self.getBrokerObject(accountId)
            lstStandardOrder = [standardOrder]
            lstOrderParam = brokerObj.prepareOrderParams(action, lstStandardOrder)
            
            broker = Broker(brokerObj.BrokerId)
            if broker.canPlaceOrder(exchange) == False:
                return []


            if action.upper() == 'CREATE':                       
                lstOrd = brokerObj.createOrders(lstOrderParam)
                if lstOrd:
                    orderId = lstOrd[0]['orderId']
                    standardOrder['orderId'] = orderId
                    standardOrder['status'] = 'OPEN'

            if action.upper() in ['MODIFY','UPDATE','CHANGE']:                       
                lstOrd = brokerObj.modifyOrders(lstOrderParam)
                if lstOrd:
                    orderId = lstOrd[0]['orderId']
                    standardOrder['orderId'] = orderId
                    standardOrder['status'] = 'OPEN'
                
        return standardOrder