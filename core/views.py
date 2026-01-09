
from django.shortcuts import render

def home(request):
    return render(request, "index.html")

def organizations(request):
    return render(request, "organization.html")

def resume_tips(request):
    return render(request, "resume-tips.html")

def ats_guide(request):
    return render(request, "ats-guide.html")

def page(request, template_name):
    return render(request, template_name)

def register_choose(request):
    return render(request, "auth-register-choose.html")

def register_jobseeker(request):
    return render(request, "auth-register-jobseeker.html")

def register_hr(request):
    return render(request, "auth-register-hr.html")

def login_page(request):
    return render(request, "auth-login.html")   # or whatever your login template name is

