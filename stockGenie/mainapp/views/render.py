from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
# from mainapp.models import User
import jwt, datetime
from django.http import JsonResponse, HttpResponse
from django.shortcuts import redirect
from mainapp.views.exception import CustomException
# from mainapp.Managers.managers import UserManager

from django.contrib.auth import login

# Create your views here.
def doLogout(request):
    logout(request)
    return redirect('home')

def index(request):    
    return render(request, 'mainapp/index.html')

def home(request):    
    return render(request, 'mainapp/home.html')

def showLogin(request):
    username = request.POST.get('username')
    if username:
        password = request.POST.get('password')
        # cu = CustomUser(username=username, password=password)
        # cu = user(username=username, password=password)
        try:
            user = authenticate(username=username, password = password)
        except AuthenticationFailed:
            context = {'err': 'Invalid Credentials'}
            return render(request, 'mainapp/login.html', context)
                    
        if user:
            login(request, user)
            # request.session['AUTH_COMPANIES'] = authComp
            # return redirect('/admin')
            # return render(request, 'mainapp/login.html', context)
            return redirect('index')
        else:
            context = {'err': 'Invalid Credentials'}
            return render(request, 'mainapp/login.html', context)
    return render(request, 'mainapp/login.html')

def test(request):
    # u = CustomUser(username='admin',password ='$Fusion@3108')
    u = user(username='admin',password ='$Fusion@3108')
    user = u.authenticate(request)
    if user:
        u.login(request)
        return redirect('/admin')

    return HttpResponse(False)



# class LoginView(APIView):
#     def post(self, request):
#         username = request.data['username']
#         password = request.data['password']
#         um = User(username,password)
#         if um.authenticate():
#             token = um.createJWT()
#             response = Response()
#             response.set_cookie(key='jwt', value=token, httponly=True)
#             response.data = {
#                 'jwt': token
#             }
#             return response