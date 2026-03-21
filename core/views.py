from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import get_user_model, authenticate, login as auth_login, logout
from django.utils.text import slugify
from .forms import (
    JobseekerRegisterForm, HRRegisterForm, LoginForm, ResumeUploadForm,
    EducationForm, ExperienceForm, ProjectForm, SkillForm
)
from .models import JobseekerProfile, HRProfile, Resume, Education, Experience, Project, Skill, ParsedResumeData, JobPost, ATSResult
from .utils import extract_text_from_pdf, extract_text_from_docx, parse_resume_text, calculate_ats_score
from django.contrib.auth.decorators import login_required
from .decorators import hr_required, jobseeker_required

User = get_user_model()


def home(request):
    return render(request, "index.html")

def organizations(request):
    return render(request, "organization.html")

@hr_required
def hr_candidate_detail(request):
    hr = request.user.hr_profile
    result_id = request.GET.get("result_id")
    
    # We fetch the ATSResult and ensure it belongs to a job post created by this HR
    result = get_object_or_404(ATSResult.objects.select_related('resume', 'job_post'), pk=result_id, job_post__hr=hr)
    
    return render(request, "pages/hr_candidate_detail.html", {
        "result": result,
    })

def resume_tips(request):
    return render(request, "resume-tips.html")

def ats_guide(request):
    return render(request, "ats-guide.html")

def page(request, template_name):
    return render(request, f"pages/{template_name}")


def register_choose(request):
    return render(request, "auth-register-choose.html")

@hr_required
def hr_resume_upload(request):
    hr = request.user.hr_profile
    job_posts = JobPost.objects.filter(hr=hr).order_by('-created_at')

    if request.method == "POST":
        job_id = request.POST.get("job_id")
        files = request.FILES.getlist("resumes")
        
        if not job_id:
            messages.error(request, "Please select a job post.")
            return redirect('hr_resume_upload')
            
        job_post = get_object_or_404(JobPost, pk=job_id, hr=hr)
        
        if not files:
            messages.error(request, "Please select at least one resume file.")
            return redirect('hr_resume_upload')

        success_count = 0
        from core.utils import calculate_ats_score, extract_text_from_pdf, extract_text_from_docx

        for f in files:
            # 1. Create Resume Object (Source: HR Bulk)
            resume = Resume.objects.create(
                jobseeker=None, # HR Bulk upload candidates are not yet users
                file=f,
                filename=f.name,
                source='HR Bulk'
            )
            
            # 2. Extract Text
            text = ""
            if f.name.endswith(".pdf"):
                text = extract_text_from_pdf(resume.file.path)
            elif f.name.endswith(".docx"):
                text = extract_text_from_docx(resume.file.path)
            
            if text:
                # 3. Analyze against the selected Job Post
                score, matched, missing, feedback = calculate_ats_score(text, job_post.requirements)
                
                # 4. Save Results
                ATSResult.objects.create(
                    resume=resume,
                    job_post=job_post,
                    score=score,
                    feedback=feedback,
                    matched_keywords=",".join(matched),
                    missing_keywords=",".join(missing)
                )
                success_count += 1
            else:
                # If extraction fails, we still have the resume object but no analysis
                pass

        messages.success(request, f"Successfully processed {success_count} resumes for '{job_post.title}'.")
        from django.urls import reverse
        return redirect(f"{reverse('hr_candidate_ranking')}?job_id={job_post.id}")

    return render(request, "pages/hr_resume_upload.html", {"job_posts": job_posts})

@hr_required
def hr_candidate_ranking(request):
    hr = request.user.hr_profile
    job_id = request.GET.get("job_id")
    job_posts = JobPost.objects.filter(hr=hr).order_by('-created_at')
    
    selected_job = None
    results = []
    
    if job_id:
        selected_job = get_object_or_404(JobPost, pk=job_id, hr=hr)
        results = ATSResult.objects.filter(job_post=selected_job).select_related('resume', 'resume__jobseeker').order_by('-score')

    return render(request, "pages/hr_candidate_ranking.html", {
        "job_posts": job_posts,
        "selected_job": selected_job,
        "results": results,
    })


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
    is_auth = request.user.is_authenticated
    initial_data = {}
    if is_auth:
        initial_data = {
            "full_name": request.user.full_name,
            "email": request.user.email
        }

    if request.method == "POST":
        form = JobseekerRegisterForm(request.POST, user_is_authenticated=is_auth, initial=initial_data)
        if form.is_valid():
            full_name = form.cleaned_data["full_name"]
            
            if is_auth:
                user = request.user
                user.full_name = full_name
                user.role = "jobseeker"
                user.save()
                if not hasattr(user, "jobseeker_profile"):
                    JobseekerProfile.objects.create(user=user, full_name=full_name)
                    messages.success(request, "Jobseeker profile created successfully!")
                    return redirect("jobseeker_dashboard")
            else:
                email = form.cleaned_data["email"]
                user = User.objects.create_user(
                    email=email,
                    password=form.cleaned_data["password"],
                    full_name=full_name,
                    role="jobseeker"
                )
                JobseekerProfile.objects.create(user=user, full_name=full_name)
                messages.success(request, "Jobseeker account created. Please sign in.")
                return redirect("login")
    else:
        form = JobseekerRegisterForm(user_is_authenticated=is_auth, initial=initial_data)

    return render(request, "auth-register-jobseeker.html", {"form": form})


def register_hr(request):
    is_auth = request.user.is_authenticated
    initial_data = {}
    if is_auth:
        initial_data = {
            "full_name": request.user.full_name,
            "email": request.user.email
        }

    if request.method == "POST":
        form = HRRegisterForm(request.POST, user_is_authenticated=is_auth, initial=initial_data)
        if form.is_valid():
            full_name = form.cleaned_data["full_name"]
            company = form.cleaned_data["company"]
            role_title = form.cleaned_data["role"]

            if is_auth:
                # Based on rules, HR should NOT be using Google login (is_auth=True via Google)
                # But if they somehow get here, we can allow them to finish setup if they are role='hr'
                user = request.user
                user.full_name = full_name
                user.role = "hr"
                user.save()
                if not hasattr(user, "hr_profile"):
                    HRProfile.objects.create(
                        user=user,
                        full_name=full_name,
                        company=company,
                        role=role_title
                    )
                    messages.success(request, "HR profile created successfully!")
                    return redirect("hr_dashboard")
            else:
                email = form.cleaned_data["email"]
                user = User.objects.create_user(
                    email=email,
                    password=form.cleaned_data["password"],
                    full_name=full_name,
                    role="hr"
                )
                HRProfile.objects.create(
                    user=user,
                    full_name=full_name,
                    company=company,
                    role=role_title
                )
                messages.success(request, "HR account created. Please sign in.")
                return redirect("login")
    else:
        form = HRRegisterForm(user_is_authenticated=is_auth, initial=initial_data)

    return render(request, "auth-register-hr.html", {"form": form})


def login_page(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]
            remember = form.cleaned_data["remember"]
            
            user = authenticate(request, email=email, password=password)
            if user:
                auth_login(request, user)
                if not remember:
                    request.session.set_expiry(0)
                
                if user.role == "hr":
                    return redirect("hr_dashboard")
                else:
                    return redirect("jobseeker_dashboard")
            else:
                messages.error(request, "Invalid email or password.")
    else:
        form = LoginForm()

    return render(request, "auth-login.html", {"form": form})


def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect("login")


def google_start(request, acct):
    if acct == "hr":
        messages.error(request, "Google sign-in is not available for HR accounts.")
        return redirect("register_hr")
        
    if acct not in ("jobseeker",):
        acct = "jobseeker"
        
    request.session["oauth_account_type"] = acct
    request.session.save()
    return redirect("/accounts/google/login/")


@login_required
def post_login_redirect(request):
    u = request.user
    if hasattr(u, "hr_profile"):
        return redirect("/hr/dashboard/")
    if hasattr(u, "jobseeker_profile"):
        return redirect("/jobseeker/dashboard/")
    
    # Fallback if profile doesn't exist yet
    messages.info(request, "Please select your account type to complete your setup.")
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

    # Split name for templates that need it
    name_parts = profile.full_name.split(' ')
    first_name = name_parts[0] if name_parts else ""
    last_name = name_parts[-1] if len(name_parts) > 1 else ""

    return render(request, "pages/resume_builder.html", {
        "educations": educations,
        "experiences": experiences,
        "projects": projects,
        "skills": skills,
        "first_name": first_name,
        "last_name": last_name,
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
                matched_keywords=",".join(matched),
                missing_keywords=",".join(missing)
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


@jobseeker_required
def select_template(request, template_name):
    valid_templates = [
        't1_kelly', 't2_howard', 't3_samantha_beige', 't4_samantha_white', 't5_jessie',
        't6_taylor', 't7_blue_jessie', 't8_sebastian', 't9_travis', 't10_daniel',
        't11_mira', 't12_travis_v2', 't13_kelly_v2', 't14_wes', 't15_matthew',
        't16_james', 't17_james_navy', 't18_james_sidebar', 't19_daryl', 't20_wes_v2',
        't21_daryl_clean', 't22_samantha_blue', 't23_olivia_pink'
    ]
    if template_name in valid_templates:
        profile = request.user.jobseeker_profile
        profile.selected_template = template_name
        profile.save()
        
        # Cleaner display name for messages
        display_name = template_name.split('_', 1)[-1].replace('_', ' ').title()
        messages.success(request, f"Template '{display_name}' selected successfully.")
    else:
        messages.error(request, "Invalid template selection.")
    return redirect('resume_builder')

# Protected HR Views
@hr_required
def hr_dashboard(request):
    hr = request.user.hr_profile
    
    # 1. Dashboard Stats
    open_jobs_count = JobPost.objects.filter(hr=hr, status='Open').count()
    
    # Total unique candidates who applied for this HR's jobs
    total_candidates = ATSResult.objects.filter(job_post__hr=hr).values('resume').distinct().count()
    
    # Calculate average ATS score across all results for this HR
    from django.db.models import Avg, Count, Max
    avg_score_data = ATSResult.objects.filter(job_post__hr=hr).aggregate(Avg('score'))
    avg_score = round(avg_score_data['score__avg'] or 0, 1)
    
    # Shortlisted (Score >= 80)
    shortlisted_count = ATSResult.objects.filter(job_post__hr=hr, score__gte=80).values('resume').distinct().count()

    # 2. Active Job Posts Table
    active_jobs = JobPost.objects.filter(hr=hr).annotate(
        candidate_count=Count('ats_results', distinct=True),
        top_score=Max('ats_results__score')
    ).order_by('-created_at')[:5]

    return render(request, "pages/hr_dashboard.html", {
        "open_jobs_count": open_jobs_count,
        "total_candidates": total_candidates,
        "avg_score": avg_score,
        "shortlisted_count": shortlisted_count,
        "active_jobs": active_jobs,
    })

@hr_required
def hr_create_job(request):
    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        requirements = request.POST.get("requirements")
        
        if title and description:
            JobPost.objects.create(
                hr=request.user.hr_profile,
                title=title,
                description=description,
                requirements=requirements
            )
            messages.success(request, f"Job post '{title}' created successfully!")
            return redirect('hr_dashboard')
        else:
            messages.error(request, "Title and Description are required.")

    return render(request, "pages/hr_create_job.html")

@hr_required
def hr_manage_jobs(request):
    hr = request.user.hr_profile
    from django.db.models import Count, Max
    jobs = JobPost.objects.filter(hr=hr).annotate(
        candidate_count=Count('ats_results', distinct=True),
        top_score=Max('ats_results__score')
    ).order_by('-created_at')
    
    return render(request, "pages/hr_manage_jobs.html", {"jobs": jobs})

@hr_required
def hr_delete_job(request, job_id):
    job = get_object_or_404(JobPost, pk=job_id, hr=request.user.hr_profile)
    if request.method == "POST":
        title = job.title
        job.delete()
        messages.success(request, f"Job '{title}' deleted successfully.")
    return redirect('hr_manage_jobs')