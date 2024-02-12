from trading.views.Strategies.strategy1 import Strategy1
from trading.views.Strategies.strategy import Strategy
from trading.views.Entities.brokerAccount import BrokerAccount
from mainapp.views.utils import getUniqueStruct, getItemByKey
from trading.models import Strategis

# activeScript = {
#     'accountId' : setup.target.id,
#     'brokerId': setup.target.broker.brokerId,
#     'exchange': setup.exchSeg,
#     'token': setup.token,
#     'symbol': setup.symbol
# }


class StrategyManager():
    def __init__(self, user) -> None:
        self.User = user        

    def getActiveStrategies(self):
        lstActiveStrategies = []
        lstActiveScripts = []

        strategies = Strategis.objects.filter(user = self.User)
        for strat in strategies:
            strategy = Strategy.getStrategyInstance(self.User, strat.code)
            if strategy:
                if strategy.isActive:
                    lstActiveStrategies.append(strategy)
       
            
        for strategy in lstActiveStrategies:
            for script in strategy.ActiveScripts:
                if script not in lstActiveScripts:
                    lstActiveScripts.append(script)
        
        
        self.ActiveStrategies = lstActiveStrategies
        self.ActiveScripts = lstActiveScripts

        return lstActiveStrategies

    def subscribeWebSockets(self):
        lstTicks = self.TicksForCallback
        lstUnique = getUniqueStruct(lstTicks) #accountId
        for strategy in self.ActiveStrategies:
            for accountId in strategy.ActiveAccounts:
                brokerObj = self.brokerAccount.getBrokerObject(accountId)
                brokerObj.subscribeWebSockets(strategy.requireOrderCallback, getItemByKey(lstUnique,'accountId', accountId))

    
    def initiate(self):
        lstTicks = []
        lstTickForCallback = []
        self.getActiveStrategies()
        brokerAcc = BrokerAccount(self.User)
        brokerAcc.Connect()
        self.brokerAccount = brokerAcc
        for strategy in self.ActiveStrategies:
            strategy.initiate()
            ticks = strategy.getScriptForTickCallback()
            for tick in ticks:
                lstTicks.append(tick)
        self.TicksForCallback = lstTicks
        self.subscribeWebSockets()        
    
    def start(self):

        for strategy in self.ActiveStrategies:
            strategy.start(self.brokerAccount)

        



