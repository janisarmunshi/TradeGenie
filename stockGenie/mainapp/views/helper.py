from mainapp.models import DataModelSettings, CompanyMaster, CompanyGroup, UserCompanyAuth
from django.db.models import F, Q
from django.http import HttpResponse, JsonResponse
from json import loads as jsonloads

def get_Authorised_Company(user):
    lstCompany = lstCompGrp = []
    objUserAuth = UserCompanyAuth.objects.filter(user = user)
    if objUserAuth:
        for objAuth in objUserAuth:
            
            if objAuth.company:
                objcomp = CompanyMaster.objects.filter( id = objAuth.company_id )
                lstCompGrp = list(CompanyGroup.objects.filter( id = objAuth.companyGroup_id ).values())
                for obj in objcomp:
                    lstComp = {'id': obj.id , 'companyName': obj.companyName}
                    lstCompany.append(lstComp)

            else: 
                if objAuth.companyGroup_id:
                    lstCompany = list(CompanyMaster.objects.filter( companyGroup_id = objAuth.companyGroup_id ).values('id'))
                    lstCompGrp = list(CompanyGroup.objects.filter( id = objAuth.companyGroup_id ).values())
    else:
        lstCompGrp = list(CompanyGroup.objects.values())
        lstCompany = list(CompanyMaster.objects.values()) 
    
    return lstCompGrp, lstCompany    

def getApplicationData(request, datamodel, filter = {}, ModelLevel = '', orderByField = '', recordLimit = -1, unique = False, forUpdate = False, firstRecord = False, QFilter = Q()):

    q_objects, DMObj = createAppFilter(request,datamodel, filter, ModelLevel,QFilter)
    if orderByField == '' :
        orderByField = 'id'
        
    # if ModelLevel.upper() == 'ANY':
    #     objList, ModelLevel = get_DataModel_Generic(appContext,  dbModelName, filter, orderByField, unique)
   
    models = getModelObject(DMObj[0].application_id)
    objList = getAttrib(models, DMObj,q_objects,orderByField,firstRecord,forUpdate)

    return objList

def createAppFilter(request, datamodel, filter = {}, ModelLevel = '', QFilter = Q()):    
    lstGrpId = []
    compId = request.session.get('CompId',0)
    lstAuthCompGroup, lstAuthCompId = get_Authorised_Company(request.user)
    for itmGrp in lstAuthCompGroup:
        lstGrpId.append(itmGrp['id'])
    DMObj = getModelSettings(request, datamodel, None)

    if ModelLevel == '':        
        ModelLevel = DMObj[0].modelLevels

    q_objects = QFilter
   
               
    if ModelLevel == 'Company':
        
        q_objects = Q(company_id = compId)
        q_objects &= Q(company_id__in = lstGrpId)
        
    if ModelLevel == 'Group':

        q_objects = Q(company_Group_id__in = lstAuthCompGroup)

    if ModelLevel == 'Company OR Group':
        q_objects |= Q(company_id = compId)
        q_objects |= Q(company_Group_id__in = lstAuthCompGroup)


    if ModelLevel == 'Group OR Global':
        q_objects |= Q(company_Group_id__in = lstAuthCompGroup)
        q_objects |= Q(company_Group_id = None)
    
    if ModelLevel == 'Global': 
        q_objects = Q()

    if ModelLevel.upper() == 'USER': 
        q_objects = Q(user = request.user)

    if filter != {}:
        for key, value in filter.items():
            if key == 'id' and isNum(value) == False:
                pass
            else:
                q_objects &= Q(**{key: value})         
    if len(QFilter):
        q_objects &= QFilter

    return q_objects, DMObj

def getModelSettings(request, DataModel, HelpClass):
    DMObj = None
    try:
        if DataModel:
            DMSet = DataModelSettings.objects.filter(dataModel = DataModel)
        if HelpClass:
            DMSet = DataModelSettings.objects.filter(helpClass = HelpClass)

        if DMSet:
            DMObj = DMSet.filter(company_id = request.session.get('CompId',0))
            if not DMObj:
                compObj = CompanyMaster.objects.filter(id = request.session.get('CompId',0)).first()
                if compObj:
                    DMObj = DMSet.filter(companyGroup_id = compObj.companyGroup_id)

            if not DMObj:
                DMObj = DMSet.filter(companyGroup__isnull = True, company__isnull = True )

        return DMObj
    except:
        pass

def isNum(data):
    try:
        int(data)
        return True
    except ValueError:
        return False

def getModelObject(appId):
    if appId == 1:
        from mainapp import models
    if appId ==2:    
        from trading import models
    return models

def getAttrib(models, DMObj, q_objects,orderByField, firstRecord, forUpdate):
    
    if firstRecord:
        objList = getattr(models, DMObj[0].dbModel).objects.filter(q_objects).first() 
    else:
        if forUpdate:
            objList = getattr(models, DMObj[0].dbModel).objects.select_for_update().filter(q_objects).first()
        else:            
            objList = getattr(models, DMObj[0].dbModel).objects.order_by(orderByField).filter(q_objects)    

    if firstRecord:
        objList = getattr(models, DMObj[0].dbModel).objects.filter(q_objects).first() 
    else:
        if forUpdate:
            objList = getattr(models, DMObj[0].dbModel).objects.select_for_update().filter(q_objects).first()
        else:

            objList = getattr(models, DMObj[0].dbModel).objects.order_by(orderByField).filter(q_objects)    

    return objList
    
def helpData(request):
    if request.accepts('application/json') and request.method == 'GET' :
        helpClass = dataModel = ''
        fields = []
        filter = {}
        if 'Filters' in request.GET:
            filter = jsonloads(request.GET['Filters'])
                    
        if 'Model' in request.GET:
            dataModel = request.GET['Model']

        if 'Fields' in request.GET:
            fields = jsonloads(request.GET['Fields'])

        try:
            objHelp = getApplicationData(request,dataModel,filter)        
            if fields == []:
                return JsonResponse({ 'data': list(objHelp.values()) }, safe = False) 
            else:                
                return JsonResponse({ 'data': list(objHelp.values(*fields)) }, safe = False) 

        except:
            statusMsg = {'status': 400, 'msg': 'Internal Error' }
            return JsonResponse({ 'statusMsg': statusMsg }, safe = False)         

def helpHeader(request):
    if request.accepts('application/json') and request.method == 'GET' :
        helpClass = dataModel = ''
        filter = {}

        if 'Filters' in request.GET:
            filter = jsonloads(request.GET['Filters'])
                    
        if 'Model' in request.GET:
            dataModel = request.GET['Model']
            filter.update({'dataModel': dataModel})
            
        if 'helpClass' in request.GET:
            helpClass = request.GET['helpClass']


        lstColHeader = getApplicationData(request,'ColumnHeader',filter)
        # lstColHeader.order_by('-company_id','-companyGroup_id','columnSort')
        # lstColHeader.order_by('columnSort')
        # lstColHeader = getHelpHeader(appContext, helpClass, dataModel, filter)
        
        if lstColHeader: 
            return JsonResponse({ 'data': list(lstColHeader.order_by('columnSort').values()) }, safe = False) 
        else:
            statusMsg = {'status': 400, 'msg': 'Internal Error' }
            return JsonResponse({ 'statusMsg': statusMsg }, safe = False) 
