from trading.NorenRestApiPy.api_helper import NorenApiPy
from trading.models import BrokerAccounts
import pyotp
from trading.views.Strategies.strategyManager import StrategyManager
from django.http import HttpResponse
def getConnection(request):
    api = NorenApiPy(3)
    brokerAcc = BrokerAccounts.objects.filter(clientId = 'FA80457').first()
    if brokerAcc:
        if brokerAcc.acccessToken:
            login = api.set_session(
                userid = brokerAcc.clientId, password = brokerAcc.password, usertoken=brokerAcc.acccessToken)

        else:
            totp = pyotp.TOTP(brokerAcc.factor2Secret).now()
            login = api.login(
                userid = brokerAcc.clientId, password = brokerAcc.password, twoFA = totp, 
                vendor_code = brokerAcc.vendorCode, api_secret = brokerAcc.apiKey, imei='abc1234')
            if login:
                brokerAcc.acccessToken = login.get('susertoken')
                brokerAcc.save()

        quote = api.get_quotes('NSE','2885')
        print(quote)
        return api

def startStrategy(request):
    manager = StrategyManager(request.user)
    manager.initiate()
    manager.start()
    return HttpResponse('Done')
