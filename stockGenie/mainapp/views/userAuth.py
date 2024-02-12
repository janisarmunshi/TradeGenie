from django.shortcuts import render, redirect
from rest_framework.exceptions import AuthenticationFailed
from mainapp.models import CustomUser, userAuthorization
from django.dispatch import Signal

user_logged_out = Signal()
# Create your views here.


def login(request):
    username = request.POST.get('username')
    if username:
        password = request.POST.get('password')        
        try:
            cu = CustomUser(username=username, password=password)                       
            user = cu.authenticate(request)
            # if user.user_type == 0 and 'backoffice' not in request.path:                
            #     user = None

            # if user.user_type == 1 and 'selfcare' not in request.path:                
            #     user = None

        except AuthenticationFailed:
            context = {'err': 'Invalid Credentials'}
            return render(request, 'mainapp/login.html', context)
                    
        if user:
            user.login(request, user)                                        
            # request.session['USER_TYPE'] = user.user_type
            return redirect('/backoffice/')    
        else:
            context = {'err': 'Invalid Credentials or not valid'}
            return render(request, 'mainapp/login.html', context)

    return render(request, 'mainapp/login.html', context)

def logout(request):
    do_logout(request)
    return render(request, 'mainapp/home.html')  

def privacyPolicy(request):
    return render(request, 'mainapp/privacy.html')

def deleteAccount(request):
    # return render(request, 'mainapp/home.html')  
    request.session['DEL_ACC'] = 'X'
    return redirect('/selfcare/login')

def do_logout(request):
    """
    Remove the authenticated user's ID from the request and flush their session
    data.
    """
    # Dispatch the signal before the user is logged out so the receivers have a
    # chance to find out *who* logged out.
    user = getattr(request, "user", None)
    if not getattr(user, "is_authenticated", True):
        user = None
    user_logged_out.send(sender=user.__class__, request=request, user=user)
    request.session.flush()
    if hasattr(request, "user"):
        from django.contrib.auth.models import AnonymousUser

        request.user = AnonymousUser()    
    