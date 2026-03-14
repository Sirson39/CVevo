# core/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.contrib.auth import authenticate, login as auth_login
from .forms import (
    JobseekerRegisterForm, HRRegisterForm, ResumeUploadForm,
    EducationForm, ExperienceForm, ProjectForm, SkillForm
)
from .models import JobseekerProfile, HRProfile, Resume, Education, Experience, Project, Skill, ParsedResumeData, JobPost, ATSResult
from .utils import extract_text_from_pdf, extract_text_from_docx, parse_resume_text, calculate_ats_score
from django.contrib.auth.decorators import login_required
from .decorators import hr_required, jobseeker_required


def home(request):
    return render(request, "index.html")

def organizations(request):
    return render(request, "organization.html")

def resume_tips(request):
    return render(request, "resume-tips.html")

def ats_guide(request):
    return render(request, "ats-guide.html")

def page(request, template_name):
    return render(request, f"pages/{template_name}")


def register_choose(request):
    return render(request, "auth-register-choose.html")

def help_support(request):
    return render(request, "pages/help_support.html")


def _unique_username_from_email(email: str) -> str:
    base = slugify(email.split("@")[0]) or "user"
    username = base
    i = 1
    while User.objects.filter(username=username).exists():
        i += 1
        username = f"{base}{i}"
    return username


def register_jobseeker(request):
    if request.method == "POST":
        form = JobseekerRegisterForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            user = User.objects.create_user(
                username=_unique_username_from_email(email),
                email=email,
                password=form.cleaned_data["password"],
            )
            JobseekerProfile.objects.create(
                user=user,
                full_name=form.cleaned_data["full_name"]
            )

            messages.success(request, "Jobseeker account created. Please sign in.")
            return redirect("login")
    else:
        form = JobseekerRegisterForm()

    return render(request, "auth-register-jobseeker.html", {"form": form})


def register_hr(request):
    if request.method == "POST":
        form = HRRegisterForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            user = User.objects.create_user(
                username=_unique_username_from_email(email),
                email=email,
                password=form.cleaned_data["password"],
            )
            HRProfile.objects.create(
                user=user,
                full_name=form.cleaned_data["full_name"],
                company=form.cleaned_data["company"],
                role=form.cleaned_data["role"],
            )

            messages.success(request, "HR account created. Please sign in.")
            return redirect("login")
    else:
        form = HRRegisterForm()

    return render(request, "auth-register-hr.html", {"form": form})


def login_page(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")
        remember = request.POST.get("remember")  # "on" if checked

        # find user by email (because we created username automatically)
        try:
            user_obj = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            user_obj = None

        user = None
        if user_obj:
            user = authenticate(request, username=user_obj.username, password=password)

        if user is None:
            return render(request, "auth-login.html", {"login_error": "Invalid email or password."})

        # login success
        auth_login(request, user)

        # session expiry (Remember me)
        if not remember:
            request.session.set_expiry(0)  # expires when browser closes

        # redirect based on profile
        if hasattr(user, "hr_profile"):
            return redirect("/hr/dashboard/")
        if hasattr(user, "jobseeker_profile"):
            return redirect("/jobseeker/dashboard/")

        return redirect("home")

    return render(request, "auth-login.html")

def google_start(request, acct):
    if acct not in ("hr", "jobseeker"):
        acct = "jobseeker"
    request.session["oauth_account_type"] = acct
    return redirect("/accounts/google/login/")


    return redirect("/register/")


@login_required
def post_login_redirect(request):
    u = request.user
    if hasattr(u, "hr_profile"):
        return redirect("/hr/dashboard/")
    if hasattr(u, "jobseeker_profile"):
        return redirect("/jobseeker/dashboard/")
    return redirect("/register/")


@jobseeker_required
def resume_builder(request):
    profile = request.user.jobseeker_profile
    if request.method == "POST":
        # Handle profile info (Contact / Summary)
        profile.full_name = request.POST.get("full_name", profile.full_name)
        profile.phone = request.POST.get("phone", profile.phone)
        profile.location = request.POST.get("location", profile.location)
        profile.linkedin = request.POST.get("linkedin", profile.linkedin)
        profile.portfolio = request.POST.get("portfolio", profile.portfolio)
        profile.summary = request.POST.get("summary", profile.summary)
        profile.save()
        messages.success(request, "Profile updated.")
        return redirect('resume_builder')

    educations = profile.educations.all()
    experiences = profile.experiences.all()
    projects = profile.projects.all()
    skills = profile.skills.all()

    return render(request, "pages/resume_builder.html", {
        "educations": educations,
        "experiences": experiences,
        "projects": projects,
        "skills": skills,
    })


@jobseeker_required
def add_education(request):
    if request.method == "POST":
        form = EducationForm(request.POST)
        if form.is_valid():
            edu = form.save(commit=False)
            edu.profile = request.user.jobseeker_profile
            edu.save()
            messages.success(request, "Education added.")
    return redirect('resume_builder')


@jobseeker_required
def delete_education(request, pk):
    edu = get_object_or_404(Education, pk=pk, profile=request.user.jobseeker_profile)
    edu.delete()
    messages.success(request, "Education deleted.")
    return redirect('resume_builder')


@jobseeker_required
def add_experience(request):
    if request.method == "POST":
        form = ExperienceForm(request.POST)
        if form.is_valid():
            exp = form.save(commit=False)
            exp.profile = request.user.jobseeker_profile
            exp.save()
            messages.success(request, "Experience added.")
    return redirect('resume_builder')


@jobseeker_required
def delete_experience(request, pk):
    exp = get_object_or_404(Experience, pk=pk, profile=request.user.jobseeker_profile)
    exp.delete()
    messages.success(request, "Experience deleted.")
    return redirect('resume_builder')


@jobseeker_required
def add_project(request):
    if request.method == "POST":
        form = ProjectForm(request.POST)
        if form.is_valid():
            proj = form.save(commit=False)
            proj.profile = request.user.jobseeker_profile
            proj.save()
            messages.success(request, "Project added.")
    return redirect('resume_builder')


@jobseeker_required
def delete_project(request, pk):
    proj = get_object_or_404(Project, pk=pk, profile=request.user.jobseeker_profile)
    proj.delete()
    messages.success(request, "Project deleted.")
    return redirect('resume_builder')


@jobseeker_required
def add_skill(request):
    if request.method == "POST":
        form = SkillForm(request.POST)
        if form.is_valid():
            skill = form.save(commit=False)
            skill.profile = request.user.jobseeker_profile
            skill.save()
            messages.success(request, "Skill added.")
    return redirect('resume_builder')


@jobseeker_required
def delete_skill(request, pk):
    skill = get_object_or_404(Skill, pk=pk, profile=request.user.jobseeker_profile)
    skill.delete()
    messages.success(request, "Skill deleted.")
    return redirect('resume_builder')


@jobseeker_required
def analyze_resume(request, resume_id):
    resume = get_object_or_404(Resume, pk=resume_id, jobseeker=request.user.jobseeker_profile)
    job_posts = JobPost.objects.all().order_by('-created_at')

    if request.method == "POST":
        job_id = request.POST.get("job_id")
        job_post = get_object_or_404(JobPost, pk=job_id)

        # Get parsed text
        parsed_data = getattr(resume, 'parsed_data', None)
        if not parsed_data:
            from .utils import extract_text_from_pdf, extract_text_from_docx
            file_path = resume.file.path
            ext = resume.filename.split('.')[-1].lower()
            text = ""
            if ext == 'pdf': text = extract_text_from_pdf(file_path)
            elif ext == 'docx': text = extract_text_from_docx(file_path)
            
            if text:
                parsed_data = ParsedResumeData.objects.create(
                    resume=resume,
                    extracted_text=text
                )
        
        if parsed_data:
            score, matched, missing, feedback = calculate_ats_score(
                parsed_data.extracted_text, 
                job_post.requirements
            )

            ATSResult.objects.create(
                resume=resume,
                job_post=job_post,
                score=score,
                feedback=feedback,
                matched_keywords=", ".join(matched),
                missing_keywords=", ".join(missing)
            )
            messages.success(request, f"Analysis complete for {job_post.title}. Score: {score}%")
            return redirect('analysis_results')
        else:
            messages.error(request, "Could not extract text for analysis.")

    return render(request, "pages/analyze_resume.html", {
        "resume": resume,
        "job_posts": job_posts
    })


@jobseeker_required
def analysis_results(request):
    results = ATSResult.objects.filter(resume__jobseeker=request.user.jobseeker_profile).order_by('-analyzed_at')
    return render(request, "pages/analysis_results.html", {"results": results})


# Protected Jobseeker Views
@jobseeker_required
def jobseeker_dashboard(request):
    resumes = request.user.jobseeker_profile.resumes.all().order_by('-uploaded_at')
    return render(request, "pages/jobseeker_dashboard.html", {"resumes": resumes})

@jobseeker_required
def resume_upload(request):
    if request.method == "POST":
        form = ResumeUploadForm(request.POST, request.FILES)
        if form.is_valid():
            resume_file = request.FILES['resume_file']
            resume = Resume.objects.create(
                jobseeker=request.user.jobseeker_profile,
                file=resume_file,
                filename=resume_file.name
            )
            
            # --- Trigger Parsing ---
            file_path = resume.file.path
            ext = resume.filename.split('.')[-1].lower()
            text = ""
            if ext == 'pdf':
                text = extract_text_from_pdf(file_path)
            elif ext == 'docx':
                text = extract_text_from_docx(file_path)
            
            if text:
                parsed_sections = parse_resume_text(text)
                ParsedResumeData.objects.create(
                    resume=resume,
                    extracted_text=text,
                    skills=parsed_sections.get("skills", ""),
                    experience=parsed_sections.get("experience", ""),
                    education=parsed_sections.get("education", ""),
                )
            # -----------------------

            messages.success(request, f"Resume '{resume_file.name}' uploaded and parsed successfully.")
            return redirect('jobseeker_dashboard')
    else:
        form = ResumeUploadForm()
    
    resumes = request.user.jobseeker_profile.resumes.all().order_by('-uploaded_at')
    return render(request, "pages/resume_upload.html", {"form": form, "resumes": resumes})

@jobseeker_required
def resume_delete(request, pk):
    resume = get_object_or_404(Resume, pk=pk, jobseeker=request.user.jobseeker_profile)
    filename = resume.filename
    resume.delete()
    messages.success(request, f"Resume '{filename}' deleted.")
    return redirect('resume_upload')


# Protected HR Views
@hr_required
def hr_dashboard(request):
    return render(request, "pages/hr_dashboard.html")

@hr_required
def hr_create_job(request):
    return render(request, "pages/hr_create_job.html")

@hr_required
def hr_manage_jobs(request):
    return render(request, "pages/hr_manage_jobs.html")