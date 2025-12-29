import os
from django.conf import settings
from django.shortcuts import render, redirect
from screening.forms import ResumeUploadForm
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import authenticate, login
from .nlp.screening import analyze_resume  # Your AI checker

def resume_upload(request):
    if request.method == 'POST':
        form = ResumeUploadForm(request.POST, request.FILES)
        if form.is_valid():
            resume_instance = form.save()  # saves the uploaded resume to media/

            resume_path = os.path.join(settings.MEDIA_ROOT, resume_instance.resume_file.name)

            # Run AI checker
            score, issues = analyze_resume(resume_path)

            return render(request, 'resume_upload.html', {
                'score': score,
                'issues': issues
            })
    else:
        form = ResumeUploadForm()

    return render(request, 'home.html', {'form': form})


# ========== Home Page ==========
def home(request):
    form = ResumeUploadForm()
    if request.method == 'POST':
        form = ResumeUploadForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('home')
    return render(request, 'home.html', {'form': form})

# ========== Login ==========
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

# ========== Signup ==========
def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'signup.html', {'form': form})
