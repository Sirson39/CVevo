from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from .forms import SignupForm, LoginForm, ResumeUploadForm
from .models import UploadedResume, UserProfile, ScreeningResult
from django.contrib.auth.decorators import login_required
from django.conf import settings
from .models import JobDescription
from .forms import JobDescriptionForm
from main.nlp.job_matcher import match_resume_to_job  # your file
import os
import json
import csv
from django.http import HttpResponse

from main.nlp.screening import analyze_resume  # Your AI code


# --- Signup ---
def user_signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()

            user.userprofile.user_type = form.cleaned_data['user_type']
            user.userprofile.save()

            login(request, user)
            return redirect('home')
    else:
        form = SignupForm()
    return render(request, 'signup.html', {'form': form})



@login_required
def export_csv(request):
    if request.user.userprofile.user_type != 'org':
        return redirect('home')

    results = ScreeningResult.objects.filter(organization=request.user)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="screening_results.csv"'

    writer = csv.writer(response)
    writer.writerow(['Resume', 'Score', 'Matched Skills', 'Missing Skills', 'Date'])

    for r in results:
        writer.writerow([
            r.resume.user.username,
            r.matched_score,
            r.matched_skills,
            r.missing_skills,
            r.analyzed_at
        ])

    return response


# --- Login ---
def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password']
            )
            if user:
                login(request, user)
                return redirect('home')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})


@login_required
def user_dashboard(request):
    if request.user.userprofile.user_type != 'normal':
        return redirect('home')

    resumes = UploadedResume.objects.filter(user=request.user).order_by('-uploaded_at')
    return render(request, 'user_dashboard.html', {'resumes': resumes})



# --- Logout ---
def user_logout(request):
    logout(request)
    return redirect('home')


# --- Home Upload Page ---
@login_required
def home(request):
    form = ResumeUploadForm()
    return render(request, 'home.html', {'form': form})


@login_required
def match_history(request):
    if request.user.userprofile.user_type != 'org':
        return redirect('home')

    matches = ScreeningResult.objects.filter(organization=request.user).order_by('-analyzed_at')

    return render(request, 'match_history.html', {'matches': matches})


# --- Upload and Analyze Resume ---
@login_required
def resume_upload(request):
    if request.method == 'POST':
        form = ResumeUploadForm(request.POST, request.FILES)
        if form.is_valid():
            resume = form.save(commit=False)
            resume.user = request.user
            resume.save()

            resume_path = os.path.join(settings.MEDIA_ROOT, resume.file.name)

            score, issues = analyze_resume(resume_path)

            resume.score = score
            resume.issues = json.dumps(issues)
            resume.save()

            return render(request, 'screen_result.html', {
                'score': score,
                'issues': issues
            })

    else:
        form = ResumeUploadForm()
    return render(request, 'home.html', {'form': form})


# --- Dashboard for Org ---
@login_required
def org_dashboard(request):
    if request.user.userprofile.user_type != 'org':
        return redirect('home')

    resumes = UploadedResume.objects.all().order_by('-uploaded_at')
    return render(request, 'org_dashboard.html', {'resumes': resumes})


# Upload Job Description
@login_required
def upload_job_description(request):
    if request.user.userprofile.user_type != 'org':
        return redirect('home')

    if request.method == 'POST':
        form = JobDescriptionForm(request.POST, request.FILES)
        if form.is_valid():
            jd = form.save(commit=False)
            jd.organization = request.user
            jd.save()

            jd_path = os.path.join(settings.MEDIA_ROOT, jd.file.name)

            with open(jd_path, 'r', encoding='utf-8', errors='ignore') as f:
                jd_text = f.read().lower()

            jd.extracted_text = jd_text
            jd.save()

            # 🧠 Match uploaded resumes to this job
            all_resumes = UploadedResume.objects.all()
            results = []

            for resume in all_resumes:
                resume_path = os.path.join(settings.MEDIA_ROOT, resume.file.name)
                match_score, matched, missing = match_resume_to_job(resume_path, jd_text)

                # Save result to DB
                ScreeningResult.objects.create(
                    organization=request.user,
                    resume=resume,
                    matched_score=match_score,
                    matched_skills=", ".join(matched),
                    missing_skills=", ".join(missing),
                )

                results.append({
                    'resume': resume,
                    'score': match_score,
                    'matched': matched,
                    'missing': missing,
                })

                

            return render(request, 'match_result.html', {
                'job': jd,
                'results': results
            })

    else:
        form = JobDescriptionForm()

    return render(request, 'upload_jd.html', {'form': form})
