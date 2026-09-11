from django.shortcuts import render, redirect
from django.contrib.auth import logout as auth_logout

# Create your views here.


# http://localhost:8000/login/

def login(request):
    return render(request, 'login.html')


def logout(request):
    auth_logout(request)
    return redirect('chat')


