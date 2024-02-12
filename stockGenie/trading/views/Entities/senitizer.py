from mainapp.models import CustomUser
from trading.models import BrokerAccounts
from django.db.models import Q
from django.http import HttpResponse
from celery import shared_task
import redis
class Senitizer():
    def __init__(self,user, accountId=0):
        self.User = user
        self.accountId = accountId

    def resetSession(self, accountId = 0):
        qFilt = Q(user = self.User)
        accId = 0
        if self.accountId > 0:
            accId = self.accountId
        if accountId > 0:
            accId = accountId
        if accId > 0:
            qFilt &= Q(id = accId)
        
        accounts = BrokerAccounts.objects.filter(qFilt)
        for account in accounts:
            account.acccessToken = None
            account.feedToken = None
            account.reqToken = None
            account.save()
            print(f'Sessions cleared for {account.clientId}')

    def clearKeys(self):
        r = redis.Redis()
        for key in r.scan_iter("user:*"):
            # delete the key
            r.delete(key)    
        print('Redis Que Keys are cleared')    

@shared_task(bind=True)
def workerSenitization(self):
    users = CustomUser.objects.all()
    for user in users:
        senitizer = Senitizer(user)
        senitizer.resetSession()
        senitizer.clearKeys()
    print('Worker completed reset Session')

def reqSenitization(request):
    workerSenitization()
    return HttpResponse('Senitization completed')


