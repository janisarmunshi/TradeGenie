from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import render, redirect

class AuthRequiredMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.user.id is None and request.path not in ['/login','/admin/','/','/favicon.ico']:
            # return HttpResponseRedirect(reverse('login')) # or http response            
            return redirect('login')