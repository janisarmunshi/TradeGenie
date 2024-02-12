from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth import authenticate, login
import datetime, jwt, os
from mainapp.Managers.managers import UserManager
from rest_framework.exceptions import AuthenticationFailed
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete, pre_save
from mainapp.views.storage import OverwriteStorage

# Create your models here.
def username_based_gsheetauth_upload_to(instance, filename):
    return f"files/{instance.user.username}_gsheetauth.json"

class CustomUser(AbstractBaseUser):
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=128, null=True)
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    createdDate = models.DateTimeField(auto_now_add=True)
    modifiedDate = models.DateTimeField(auto_now=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    user_type = models.IntegerField(default=0) #0-backoffice, 1-User
    sync_id     = models.IntegerField(null=False, blank=False, default=0)
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['first_name','last_name']
    

    objects = UserManager()

    def __str__(self):
        return self.username

    def has_module_perms(self, app_label):
        return True

    def has_perm(self, perm, obj=None):
        return True

    def getUser(self, username = None):
        if username is not None:
            self.username = username
        self.user = CustomUser.objects.filter(username=self.username).first()
        return self.user

    def authenticate(self, request, username=None, password=None):
        if username is not None:
            self.username = username
        if password is not None:
            self.password = password

        user = CustomUser.objects.filter(username=self.username).first()
        if user is None:
            raise AuthenticationFailed('User not found!')
            # return {'err':'User not found!'}

        user = authenticate(request, username=self.username,
                                    password=self.password)
        
        # if not CustomUser.check_password(self, self.password):
        #     raise AuthenticationFailed('Incorrect password!')
        if not user:
            raise AuthenticationFailed('Incorrect password!')
            # return {'err':'Incorrect password!'}
        
        self.user = user
        return user
    
    def createJWT(self, username=None):
        if username is not None:
            self.username = username
        payload = {
            'username': self.username,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=60),
            'iat': datetime.datetime.utcnow()
        }

        token = jwt.encode(payload, os.environ.get('SECRET_KEY'), algorithm='HS256') #.decode('utf-8')
        self.JWT = token
        return token
    
    def login(self, request, user=None):
        if user is not None:
            self.user = user
        try:
            res = login(request, self.user)
            return True
        except:
            return False

class BaseModel(models.Model):
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=False, blank=True, null=True)
    created_by = models.ForeignKey(CustomUser,on_delete=models.DO_NOTHING, default=1, related_name = '%(app_label)s_%(class)s_created')
    modified_by = models.ForeignKey(CustomUser,on_delete=models.DO_NOTHING, blank=True, null=True, related_name = '%(app_label)s_%(class)s_updated')    
    class Meta:
        abstract = True

@receiver(post_save,sender = CustomUser)
def signal_user_save(sender,**kwargs):
    print('request finished')

@receiver(post_delete, sender = CustomUser)
def signal_user_delete(sender,**kwargs):
    print('user Deleted')

@receiver(pre_save, sender = CustomUser)
def signal_user_presave(sender,**kwargs):
    print('Pre Save')


class UserProfile(models.Model):
    user = models.ForeignKey(CustomUser,on_delete=models.DO_NOTHING, related_name = '%(app_label)s_%(class)s_profile')    
    isAdmin = models.BooleanField(blank=True, null=True)    
    isTOTP = models.BooleanField(blank=True, null=True)    
    autoTOTP = models.BooleanField(blank=True, null=True,default=None)
    secret  = models.CharField(max_length=64, default='',null=True,blank=True)
    isActive = models.BooleanField(blank=True, null=True,default=None)
    def __str__(self):
        return self.user.username

class UserSocialProfile(models.Model):
    user        = models.ForeignKey(CustomUser,on_delete=models.DO_NOTHING, related_name = '%(app_label)s_%(class)s_social')    
    telegramId  = models.BigIntegerField()

    def __str__(self):
        return self.user.username

class UserSecurityProfile(models.Model):
    user        = models.ForeignKey(CustomUser,on_delete=models.DO_NOTHING, related_name = '%(app_label)s_%(class)s_social')    
    secretKey   = models.CharField(max_length=64, default='',null=True,blank=True)    
    randomIV    = models.BinaryField(max_length=16)
    gsheetauth  = models.FileField(max_length=None, storage=OverwriteStorage(), upload_to=username_based_gsheetauth_upload_to,default='',null=True)
    
    def __str__(self):
        return self.user.username

class ColumnHeader(models.Model):
    dataModel       = models.CharField(max_length=40)
    columnSort     = models.IntegerField(default=0)
    columnHeader   = models.CharField(max_length=40)
    columnLable    = models.CharField(max_length=30,default="Column Header")
    columnclass    = models.CharField(max_length=100,default="")
    columnDefault  = models.CharField(max_length=1, null=True, blank=True, default='')
    datalistReturn = models.CharField(max_length=1, null=True, blank=True, default='')
    
    def __str__(self):
        return self.dataModel + '(' + self.columnHeader + ')' 

class ColumnListing(models.Model):
    tableName      = models.CharField(max_length=40)
    columnSort     = models.IntegerField(default=0)
    columnHeader   = models.CharField(max_length=40)
    columnLable    = models.CharField(max_length=30,default="Column Header")
    
    def __str__(self):
        return self.columnHeader #+ '(' + self.table_name + ')'

class Application(models.Model):
    appName     = models.CharField(max_length=40)
    def __str__(self):
        return self.appName 

class ApplicationAuthorized(models.Model):
    user        = models.ForeignKey(CustomUser,on_delete=models.DO_NOTHING, related_name = '%(app_label)s_%(class)s_Application')    
    application = models.ForeignKey(Application,on_delete=models.DO_NOTHING, related_name = '%(app_label)s_%(class)s_AppAuth')    
    def __str__(self):
        return self.user.username + '-' + self.application.appName

class CompanyGroup(models.Model):
    group_Name = models.CharField(max_length=100)
    def __str__(self):
        return self.group_Name

class CompanyMaster(BaseModel):
    companyGroup   = models.ForeignKey(CompanyGroup,on_delete=models.CASCADE,default='') 
    companyName    = models.CharField(max_length=200)
    estblish_Date   = models.DateField(default='1900-01-01')
    address1        = models.CharField(max_length=80, default='') 
    address2        = models.CharField(max_length=80, default='')
    city            = models.CharField(max_length=80, default='')
    state           = models.CharField(max_length=80, default='')
    country         = models.CharField(max_length=80, default='')
    zipcode         = models.CharField(max_length=8, default='')
    phone           = models.CharField(max_length=15, default='')
    gstin           = models.CharField(max_length=40, default='')
    cstin           = models.CharField(max_length=40, default='')
     
    def __str__(self):
        return self.companyName 
    
class UserCompanyAuth(BaseModel):
    user            = models.ForeignKey(CustomUser,on_delete=models.DO_NOTHING, related_name = '%(app_label)s_%(class)s_company')
    companyGroup   = models.ForeignKey(CompanyGroup,on_delete=models.CASCADE, null=True, blank=True, default='')
    company         = models.ForeignKey(CompanyMaster,on_delete=models.CASCADE, null=True, blank=True, default='')

class DataModelSettings(models.Model):    
    companyGroup    = models.ForeignKey(CompanyGroup,on_delete=models.CASCADE, null=True, blank=True, default='')
    company         = models.ForeignKey(CompanyMaster,on_delete=models.CASCADE, null=True, blank=True, default='')
    helpClass       = models.CharField(max_length=40, null=True, blank=True, default='')
    dataModel       = models.CharField(max_length=40, null=True, blank=True, default='', unique=True)
    dbModel         = models.CharField(max_length=40, null=True, blank=True, default='')
    filter          = models.CharField(max_length=200, null=True, blank=True, default='')
    modelLevels     = models.CharField(max_length=50, null=True, blank=True, default='')
    application     = models.ForeignKey(Application,on_delete=models.CASCADE, null=True, blank=True, default='')
    orderByField    = models.CharField(max_length=40, null=True, blank=True, default='')
    unique          = models.CharField(max_length=1, null=True, blank=True, default='')
    firstRecord     = models.CharField(max_length=1, null=True, blank=True, default='')
    def __str__(self):
        return self.dataModel  + '-' + self.helpClass 
    

class DocumentSrNo(models.Model):
    docType = models.CharField(max_length=16)
    finYear = models.CharField(max_length=4)
    prefix = models.CharField(max_length=16, default="")
    startSrNo = models.IntegerField()
    endSrNo = models.IntegerField()
    currSrNo = models.IntegerField()

class ApplicationParameters(models.Model):
    paramKey    = models.CharField(max_length=80, null=False, blank=False)
    paramValue  = models.CharField(max_length=80, null=False, blank=False)
    paramDesc   = models.TextField(max_length=2000, null=True, blank=True)
    def __str__(self):
        return self.application.appName + '-' + self.paramKey
