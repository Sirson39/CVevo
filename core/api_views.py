from django.shortcuts import get_object_or_404
import json
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from rest_framework import viewsets, permissions, status, authentication
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import action

class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return  # To not perform the csrf check previously happening

from .utils import (
    extract_text_from_pdf, extract_text_from_docx,
    parse_resume_text, calculate_ats_score, calculate_general_score
)
from .models import (
    User, JobseekerProfile, HRProfile, JobPost, 
    Resume, ParsedResumeData, ATSResult, 
    Notification, SupportRequest, ContactMessage,
    Education, Experience, Project, Skill, Certificate, Reference
)
from .serializers import (
    UserSerializer, JobseekerProfileSerializer, HRProfileSerializer, 
    JobPostSerializer, ResumeSerializer, ATSResultSerializer, 
    NotificationSerializer, SupportRequestSerializer, ContactMessageSerializer
)
from .utils import extract_text_from_pdf, extract_text_from_docx, parse_resume_text

import json

# ==========================
# AUTH & USER VIEWS
# ==========================
@method_decorator(csrf_exempt, name='dispatch')
class AuthView(APIView):
    authentication_classes = (CsrfExemptSessionAuthentication,)
    permission_classes = [permissions.AllowAny]
    def post(self, request, *args, **kwargs):
        try:
            action_type = kwargs.get('action') or request.data.get('action') or request.query_params.get('action')
            
            if action_type == 'login':
                from django.contrib.auth import authenticate, login
                email = request.data.get('email')
                password = request.data.get('password')
                user = authenticate(request, username=email, password=password)
                if user:
                    login(request, user)
                    return Response({
                        'status': 'success', 
                        'user': {
                            'id': user.id,
                            'email': user.email,
                            'full_name': user.full_name,
                            'role': user.role
                        }
                    })
                return Response({'error': 'Invalid credentials'}, status=401)
            
            elif action_type == 'register-jobseeker':
                email = request.data.get('email')
                password = request.data.get('password')
                full_name = request.data.get('full_name')
                if User.objects.filter(email=email).exists():
                    return Response({'error': 'Email already exists'}, status=400)
                user = User.objects.create_user(email=email, password=password, full_name=full_name, role='jobseeker')
                JobseekerProfile.objects.get_or_create(user=user)
                from django.contrib.auth import login
                login(request, user)
                return Response({
                    'status': 'success', 
                    'user': {
                        'id': user.id,
                        'email': user.email,
                        'full_name': user.full_name,
                        'role': 'jobseeker'
                    }
                })

            elif action_type == 'register-hr':
                email = request.data.get('email')
                password = request.data.get('password')
                full_name = request.data.get('full_name')
                company = request.data.get('company', 'Company')
                if User.objects.filter(email=email).exists():
                    return Response({'error': 'Email already exists'}, status=400)
                role_title = request.data.get('role_title') or request.data.get('role') or 'HR Manager'
                user = User.objects.create_user(email=email, password=password, full_name=full_name, role='hr')
                HRProfile.objects.get_or_create(user=user, defaults={'full_name': full_name, 'company': company, 'role': role_title})
                from django.contrib.auth import login
                login(request, user)
                return Response({
                    'status': 'success', 
                    'user': {
                        'id': user.id,
                        'email': user.email,
                        'full_name': user.full_name,
                        'role': 'hr'
                    }
                })

            elif action_type == 'logout':
                from django.contrib.auth import logout
                logout(request)
                return Response({'status': 'success'})

            return Response({'error': 'Invalid action'}, status=400)
        except Exception as e:
            return Response({'error': str(e)}, status=500)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

@method_decorator(csrf_exempt, name='dispatch')
class UserMeView(APIView):
    authentication_classes = (CsrfExemptSessionAuthentication,)
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        data = {
            'id': user.id,
            'email': user.email,
            'full_name': user.full_name,
            'role': user.role
        }
        if user.role == 'hr' and hasattr(user, 'hr_profile'):
            data['company'] = user.hr_profile.company
        return Response(data)

    def patch(self, request):
        user = request.user
        full_name = request.data.get('full_name')
        password = request.data.get('password')

        if full_name:
            user.full_name = full_name
        if password:
            user.set_password(password)
        
        user.save()
        
        # Notify about profile change
        Notification.push(user, "Profile updated successfully.", icon="👤", notif_type="success")
        if password:
            Notification.push(user, "Security alert: Your password was changed.", icon="🔒", notif_type="warning")
        
        # Re-fetch data for response
        return self.get(request)

# ==========================
# PROFILE & DASHBOARD
# ==========================
class JobseekerProfileViewSet(viewsets.ModelViewSet):
    queryset = JobseekerProfile.objects.all()
    serializer_class = JobseekerProfileSerializer
    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated: return JobseekerProfile.objects.none()
        if user.role == 'jobseeker': return JobseekerProfile.objects.filter(user=user)
        return super().get_queryset()

class HRProfileViewSet(viewsets.ModelViewSet):
    queryset = HRProfile.objects.all()
    serializer_class = HRProfileSerializer
    authentication_classes = (CsrfExemptSessionAuthentication,)
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated: return HRProfile.objects.none()
        if user.role == 'hr': return HRProfile.objects.filter(user=user)
        return HRProfile.objects.none()

    @action(detail=False, methods=['get', 'patch', 'put'])
    def me(self, request):
        profile = request.user.hr_profile
        if request.method == 'GET':
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        
        serializer = self.get_serializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            # Also update user.full_name if provided
            if 'full_name' in request.data:
                request.user.full_name = request.data['full_name']
                request.user.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

class JobseekerDashboardView(APIView):
    def get(self, request):
        from django.db.models import Avg
        from django.utils import timezone
        
        profile, _ = JobseekerProfile.objects.get_or_create(user=request.user)
        resumes_qs = Resume.objects.filter(jobseeker=profile).order_by('-uploaded_at')
        
        # 1. Stats
        avg_score_data = ATSResult.objects.filter(resume__jobseeker=profile).aggregate(Avg('score'))
        avg_score = round(avg_score_data['score__avg'] or 0, 1)
        
        now = timezone.now()
        total_scans_month = ATSResult.objects.filter(
            resume__jobseeker=profile, 
            analyzed_at__year=now.year, 
            analyzed_at__month=now.month
        ).count()
        
        strength_score = 0
        if profile.educations.exists(): strength_score += 25
        if profile.experiences.exists(): strength_score += 25
        if profile.skills.exists(): strength_score += 25
        if profile.projects.exists(): strength_score += 25
        
        strength_label = "Low"
        if strength_score >= 75: strength_label = "Advanced"
        elif strength_score >= 50: strength_label = "Improving"
        elif strength_score >= 25: strength_label = "Started"

        # 2. Add latest_score to each resume data
        recent_resumes_data = []
        for r in resumes_qs[:5]:
            r_data = ResumeSerializer(r).data
            latest_res = ATSResult.objects.filter(resume=r).order_by('-analyzed_at').first()
            r_data['latest_score'] = latest_res.score if latest_res else None
            # Formatting uploaded_at for JS
            r_data['uploaded_at'] = r.uploaded_at.strftime("%b %d, %Y")
            r_data['file_url'] = r.file.url
            recent_resumes_data.append(r_data)
        
        return Response({
            'full_name': profile.user.full_name,
            'email': profile.user.email,
            'avg_score': avg_score,
            'total_scans_month': total_scans_month,
            'strength_score': strength_score,
            'strength_label': strength_label,
            'resume_count': resumes_qs.count(),
            'resumes': recent_resumes_data
        })

@method_decorator(csrf_exempt, name='dispatch')
class HRDashboardView(APIView):
    authentication_classes = (CsrfExemptSessionAuthentication,)
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from django.db.models import Avg, Max, Count
        hr = request.user.hr_profile
        posts = JobPost.objects.filter(hr=hr)
        
        open_jobs_count = posts.filter(status='Open').count()
        total_candidates = ATSResult.objects.filter(job_post__hr=hr).count()
        shortlisted_count = ATSResult.objects.filter(job_post__hr=hr, status='Shortlisted').count()
        
        avg_score_data = ATSResult.objects.filter(job_post__hr=hr).aggregate(Avg('score'))
        avg_score = round(avg_score_data['score__avg'] or 0, 1)

        # Active jobs list with candidate counts and top scores
        active_jobs_data = []
        for job in posts.filter(status='Open')[:5]:
            stats = ATSResult.objects.filter(job_post=job).aggregate(
                count=Count('id'),
                max_score=Max('score')
            )
            active_jobs_data.append({
                'id': job.id,
                'title': job.title,
                'status': job.status,
                'candidate_count': stats['count'] or 0,
                'top_score': round(stats['max_score'] or 0, 0)
            })

        # Mock funnel data (or calculate if status tracking is real)
        interviewing_count = ATSResult.objects.filter(job_post__hr=hr, status='Interviewing').count()
        funnel = {
            'apps': 100 if total_candidates > 0 else 0,
            'screening': round((shortlisted_count / total_candidates * 100), 0) if total_candidates > 0 else 0,
            'interviewing': round((interviewing_count / total_candidates * 100), 0) if total_candidates > 0 else 0,
        }

        return Response({
            'company_name': hr.company or "HR Overview",
            'user_name': request.user.full_name,
            'user_role': getattr(hr, 'role', 'HR Manager'),
            'user_email': request.user.email,
            'open_jobs_count': open_jobs_count,
            'total_candidates': total_candidates,
            'shortlisted_count': shortlisted_count,
            'avg_score': avg_score,
            'active_jobs': active_jobs_data,
            'funnel': funnel
        })

# ==========================
# JOB MANAGEMENT
# ==========================
class JobPostViewSet(viewsets.ModelViewSet):
    queryset = JobPost.objects.all()
    serializer_class = JobPostSerializer
    authentication_classes = (CsrfExemptSessionAuthentication,)
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'hr_profile'):
            return JobPost.objects.filter(hr=user.hr_profile).order_by('-created_at')
        # Jobseekers can see all open jobs
        return JobPost.objects.filter(status='Open').order_by('-created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({'jobs': serializer.data})

        if hasattr(self.request.user, 'hr_profile'):
            serializer.save(hr=self.request.user.hr_profile)
            Notification.push(self.request.user, f"Job Post '{serializer.validated_data.get('title')}' is now live.", icon="💼", notif_type="success")
        else:
            raise serializer.ValidationError({"error": "Only HR users can post jobs."})

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response({'error': serializer.errors}, status=400)
        self.perform_create(serializer)
        return Response({'message': 'Job posted successfully!', 'data': serializer.data}, status=201)

# ==========================
# RESUME & BUILDER
# ==========================
class ResumeViewSet(viewsets.ModelViewSet):
    queryset = Resume.objects.all()
    serializer_class = ResumeSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated: return Resume.objects.none()
        if user.role == 'jobseeker': return Resume.objects.filter(jobseeker__user=user)
        return super().get_queryset()

    def perform_create(self, serializer):
        resume = serializer.save(jobseeker=self.request.user.jobseeker_profile)
        # Auto-parse logic
        try:
            file_path = resume.file.path
            ext = file_path.split('.')[-1].lower()
            text = extract_text_from_pdf(file_path) if ext == 'pdf' else extract_text_from_docx(file_path)
            if text:
                parsed = parse_resume_text(text)
                ParsedResumeData.objects.create(resume=resume, extracted_text=text, **parsed)
        except Exception as e:
            print("Auto-parse error:", e)
        
        Notification.push(self.request.user, f"Resume '{resume.filename}' uploaded and parsed.", icon="📄", notif_type="success")

    def perform_destroy(self, instance):
        filename = instance.filename
        user = self.request.user
        instance.delete()
        Notification.push(user, f"Resume '{filename}' has been deleted.", icon="🗑️", notif_type="warning")

from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

@method_decorator(csrf_exempt, name='dispatch')
class ResumeBuilderView(APIView):
    authentication_classes = (CsrfExemptSessionAuthentication,)
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    def get(self, request):
        profile, _ = JobseekerProfile.objects.get_or_create(user=request.user)
        # Using Serializers for full nested data
        serializer = JobseekerProfileSerializer(profile)
        data = serializer.data
        return Response({
            'profile': data,
            'skills': data.get('skills', []),
            'experiences': data.get('experiences', []),
            'educations': data.get('educations', []),
            'projects': data.get('projects', []),
            'certificates': data.get('certificates', []),
            'references': data.get('references', []),
            'selected_template': profile.selected_template or 't1_kelly'
        })
    def patch(self, request):
        profile, _ = JobseekerProfile.objects.get_or_create(user=request.user)
        serializer = JobseekerProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ==========================
# ANALYSIS & RESULTS
# ==========================
@method_decorator(csrf_exempt, name='dispatch')
class QuickAnalysisView(APIView):
    authentication_classes = (CsrfExemptSessionAuthentication,)
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        try:
            resume_id = request.data.get('resume_id')
            job_description = request.data.get('job_description')
            job_id = request.data.get('job_id')
            job_title_input = request.data.get('job_title')
            
            if job_id and (not job_description or job_description == 'FETCH_FROM_JOB'):
                job = get_object_or_404(JobPost, id=job_id)
                job_description = job.description

            if not resume_id or not job_description:
                return Response({'error': 'Missing fields'}, status=400)
            
            resume = get_object_or_404(Resume, id=resume_id, jobseeker__user=request.user)
            
            # Notify Analysis Start
            Notification.push(request.user, "ATS Analysis started. Scanning your resume... 🔍", icon="🕵️", notif_type="info")

            # 1. Get Resume Text
            parsed_data = getattr(resume, 'parsed_data', None)
            text = parsed_data.extracted_text if parsed_data else ""
            if not text:
                ext = resume.filename.split('.')[-1].lower()
                text = extract_text_from_pdf(resume.file.path) if ext == 'pdf' else extract_text_from_docx(resume.file.path)

            if not text:
                return Response({'error': 'Text extraction failed'}, status=400)

            # 2. Run Real ATS Analysis
            analysis = calculate_ats_score(text, job_description)
            
            # 3. Save Result
            full_breakdown = {
                'pillars': analysis.get('pillars', {}),
                'suggestions': analysis.get('suggestions', [])
            }
            
            print(f"DEBUG: ATS Match -> {analysis.get('matched_keywords')}")
            print(f"DEBUG: ATS Missing -> {analysis.get('missing_skills')}")
            result = ATSResult.objects.create(
                resume=resume,
                job_post=JobPost.objects.filter(id=job_id).first() if job_id else None,
                custom_job_title=job_title_input or ("Quick Scan" if not job_id else ""),
                score=analysis.get('ats_score', 0),
                feedback=analysis.get('feedback', ""),
                matched_keywords=",".join(analysis.get('matched_keywords', [])),
                missing_keywords=",".join(analysis.get('missing_skills', [])),
                score_breakdown=json.dumps(full_breakdown)
            )
            print(f"DEBUG: Result ID {result.id} Saved with Match KWs: {result.matched_keywords}")
            
            # Notify User
            job_name = job_title_input or (result.job_post.title if result.job_post else "Quick Scan")
            Notification.push(request.user, f"ATS Analysis complete for '{job_name}'. Score: {result.score}%", icon="📊", notif_type="success")
            
            return Response(ATSResultSerializer(result).data)
        except Exception as e:
            return Response({'error': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class GeneralAnalysisView(APIView):
    authentication_classes = (CsrfExemptSessionAuthentication,)
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request, resume_id):
        resume = get_object_or_404(Resume, id=resume_id, jobseeker__user=request.user)
        
        # Notify Analysis Start
        Notification.push(request.user, "General Quality Scan initiated. ✨", icon="📈", notif_type="info")

        # 1. Get Text
        parsed_data = getattr(resume, 'parsed_data', None)
        text = parsed_data.extracted_text if parsed_data else ""
        if not text:
            ext = resume.filename.split('.')[-1].lower()
            text = extract_text_from_pdf(resume.file.path) if ext == 'pdf' else extract_text_from_docx(resume.file.path)

        if not text:
            return Response({'error': 'No text found'}, status=400)

        # 2. Run Real General Quality Scan
        scan = calculate_general_score(text, resume.file.size, resume.filename.split('.')[-1])
        
        # Save to history so it appears in dashboard
        full_breakdown = {
            'pillars': scan.get('breakdown', {}),
            'suggestions': scan.get('suggestions', [])
        }
        
        result = ATSResult.objects.create(
            resume=resume,
            custom_job_title="General Quality Scan",
            score=scan.get('quality_score', 0),
            feedback=scan.get('summary', "Review complete."),
            matched_keywords=",".join(scan.get('found_keywords', [])),
            missing_keywords=",".join(scan.get('missing_keywords', [])),
            score_breakdown=json.dumps(full_breakdown)
        )
        
        # Notify User
        Notification.push(request.user, f"General Quality Scan complete. Quality Score: {result.score}%", icon="✨", notif_type="info")

        return Response(ATSResultSerializer(result).data)

@method_decorator(csrf_exempt, name='dispatch')
class ResumeBuilderActionView(APIView):
    authentication_classes = (CsrfExemptSessionAuthentication,)
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, category):
        # Ensure we get the correct profile object
        profile, _ = JobseekerProfile.objects.get_or_create(user=request.user)
        data = request.data
        
        if category == 'skills':
            item = Skill.objects.create(
                profile=profile, 
                name=data.get('name'), 
                skill_type=data.get('skill_type', 'Technical'), 
                level=data.get('level', 'Intermediate')
            )
            return Response({'id': item.id, 'name': item.name, 'status': 'added'})
            
        elif category == 'experiences':
            item = Experience.objects.create(
                profile=profile, 
                company=data.get('company'), 
                position=data.get('position'), 
                start_date=data.get('start_date') or None, 
                end_date=data.get('end_date') or None, 
                description=data.get('description', '')
            )
            return Response({'status': 'added', 'id': item.id})
            
        elif category == 'educations':
            item = Education.objects.create(
                profile=profile, 
                institution=data.get('institution'), 
                degree=data.get('degree'), 
                start_date=data.get('start_date') or None, 
                end_date=data.get('end_date') or None
            )
            return Response({'status': 'added', 'id': item.id})
            
        elif category == 'projects':
            item = Project.objects.create(
                profile=profile, 
                title=data.get('title'), 
                description=data.get('description'), 
                link=data.get('link', '')
            )
            return Response({'status': 'added', 'id': item.id})
            
        elif category == 'certificates':
            item = Certificate.objects.create(
                profile=profile, 
                name=data.get('name'), 
                issuer=data.get('issuer'), 
                date_obtained=data.get('date_obtained') or None, 
                link=data.get('link', '')
            )
            return Response({'status': 'added', 'id': item.id})
            
        elif category == 'references':
            item = Reference.objects.create(
                profile=profile, 
                name=data.get('name'), 
                relationship=data.get('relationship'), 
                company=data.get('company'), 
                phone=data.get('phone', ''), 
                email=data.get('email', '')
            )
            return Response({'status': 'added', 'id': item.id})
            
        return Response({'error': 'Invalid category'}, status=400)

    def delete(self, request, category, pk):
        profile, _ = JobseekerProfile.objects.get_or_create(user=request.user)
        
        # Safe deletion map
        model_map = {
            'skills': Skill, 'experiences': Experience, 'educations': Education,
            'projects': Project, 'certificates': Certificate, 'references': Reference
        }
        
        model = model_map.get(category)
        if model:
            # Crucial: verify ownership before deleting
            item = get_object_or_404(model, id=pk, profile=profile)
            item.delete()
            return Response({'status': 'deleted'})
        return Response({'error': 'Invalid category'}, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class TemplateGalleryView(APIView):
    authentication_classes = (CsrfExemptSessionAuthentication,)
    permission_classes = [permissions.AllowAny] # Allow check inside
    
    def get(self, request):
        if not request.user.is_authenticated:
            return Response({'error': 'Not authenticated'}, status=401)
        profile, _ = JobseekerProfile.objects.get_or_create(user=request.user)
        templates = [
            {'code': 't1_kelly', 'name': 'Modern Professional', 'tagline': 'Clean, sharp, and high-impact.'},
            {'code': 't2_howard', 'name': 'Executive Slate', 'tagline': 'Sophisticated dark accents.'},
            {'code': 't3_samantha_beige', 'name': 'Creative Beige', 'tagline': 'Warm and approachable design.'},
            {'code': 't4_samantha_white', 'name': 'Minimalist Pure', 'tagline': 'Ultra-clean white space.'},
            {'code': 't5_jessie', 'name': 'The Jessie', 'tagline': 'Bold sidebar with clear headers.'},
            {'code': 't6_taylor', 'name': 'Classic Chrono', 'tagline': 'Timeless professional layout.'},
            {'code': 't7_blue_jessie', 'name': 'Oceanic Jessie', 'tagline': 'The Jessie in fresh blue colors.'},
            {'code': 't8_sebastian', 'name': 'Compact Bold', 'tagline': 'Maximizes space for high achievers.'},
            {'code': 't11_mira', 'name': 'Mira Modern', 'tagline': 'Stylish and contemporary.'},
            {'code': 't14_wes', 'name': 'The Wes', 'tagline': 'Professional grid-based utility.'},
            {'code': 't19_daryl', 'name': 'Daryl Clean', 'tagline': 'Sleek and easy to read for ATS.'},
            {'code': 't20_wes_v2', 'name': 'Wes Refined', 'tagline': 'Updated version of the classic Wes.'},
            {'code': 't22_samantha_blue', 'name': 'Executive Blue', 'tagline': 'Commanding samantha blue layout.'},
            {'code': 't23_olivia_pink', 'name': 'Olivia Creative', 'tagline': 'Vibrant and modern pink accents.'},
        ]
        return Response({
            'templates': templates,
            'selected_template': profile.selected_template or 't1_kelly'
        })

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'error': 'Not logged in'}, status=401)
            
        profile, _ = JobseekerProfile.objects.get_or_create(user=request.user)
        # Handle both variations of the field name just in case
        template_code = request.data.get('template_code') or request.data.get('selected_template')
        
        if not template_code:
            return Response({'error': 'No template code provided'}, status=400)
            
        profile.selected_template = template_code
        profile.save()
        return Response({'status': 'success', 'selected': template_code})

# ==========================
# UTILITY VIEWS
# ==========================
class ATSResultViewSet(viewsets.ModelViewSet):
    queryset = ATSResult.objects.all()
    serializer_class = ATSResultSerializer
    authentication_classes = (CsrfExemptSessionAuthentication,)
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated: return ATSResult.objects.none()
        return ATSResult.objects.filter(resume__jobseeker__user=user).order_by('-analyzed_at')

class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user) if self.request.user.is_authenticated else Notification.objects.none()

class SupportRequestViewSet(viewsets.ModelViewSet):
    queryset = SupportRequest.objects.all()
    serializer_class = SupportRequestSerializer

# ==========================
# HR SPECIFIC VIEWS
# ==========================
@method_decorator(csrf_exempt, name='dispatch')
class HRUpdateStatusView(APIView):
    authentication_classes = (CsrfExemptSessionAuthentication,)
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if not hasattr(request.user, 'hr_profile'):
            return Response({'error': 'Only HR users can update status'}, status=403)
            
        result_id = request.data.get('result_id')
        action = request.data.get('action') # shortlist, interview, reject
        
        result = get_object_or_404(ATSResult, id=result_id, job_post__hr=request.user.hr_profile)
        
        status_map = {
            'shortlist': 'Shortlisted',
            'interview': 'Interviewing',
            'reject': 'Rejected'
        }
        
        new_status = status_map.get(action)
        if new_status:
            result.status = new_status
            result.save()
            return Response({'status': 'success', 'new_status': new_status})
        
        return Response({'error': 'Invalid action'}, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class HRBulkUploadView(APIView):
    authentication_classes = (CsrfExemptSessionAuthentication,)
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if not hasattr(request.user, 'hr_profile'):
            return Response({'error': 'Only HR users can perform bulk upload'}, status=403)
            
        job_id = request.data.get('job_id')
        resumes = request.FILES.getlist('resumes')
        
        if not job_id or not resumes:
            return Response({'error': 'Job ID and resumes are required'}, status=400)
            
        job = get_object_or_404(JobPost, id=job_id, hr=request.user.hr_profile)
        
        results = []
        for file in resumes:
            # 1. Save Resume (Transient Jobseeker for bulk upload)
            # In a real app, we might create a shadow jobseeker or just save the file
            resume = Resume.objects.create(
                file=file,
                filename=file.name
            )
            
            # 2. Extract Text
            ext = file.name.split('.')[-1].lower()
            text = ""
            try:
                if ext == 'pdf': text = extract_text_from_pdf(resume.file.path)
                else: text = extract_text_from_docx(resume.file.path)
            except: pass

            if text:
                # 3. Analyze against job requirements
                analysis = calculate_ats_score(text, job.requirements or job.description)
                
                # Combine breakdown for storage
                full_breakdown = {
                    'pillars': analysis.get('pillars', {}),
                    'suggestions': analysis.get('suggestions', [])
                }
                
                res = ATSResult.objects.create(
                    resume=resume,
                    job_post=job,
                    score=analysis.get('ats_score', 0),
                    feedback=analysis.get('feedback', ""),
                    matched_keywords=",".join(analysis.get('matched_keywords', [])),
                    missing_keywords=",".join(analysis.get('missing_skills', [])),
                    score_breakdown=json.dumps(full_breakdown)
                )
                results.append({'filename': file.name, 'score': res.score, 'status': 'success'})
            else:
                results.append({'filename': file.name, 'status': 'error', 'message': 'Could not extract text'})

        return Response({
            'status': 'success', 
            'results': results, 
            'redirect_job_id': job_id,
            'message': f'Successfully processed {len(results)} resumes.'
        })

class ContactMessageViewSet(viewsets.ModelViewSet):
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageSerializer

@method_decorator(csrf_exempt, name='dispatch')
class HRCandidateRankingView(APIView):
    authentication_classes = (CsrfExemptSessionAuthentication,)
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not hasattr(request.user, 'hr_profile'):
            return Response({'error': 'Unauthorized'}, status=403)
            
        hr = request.user.hr_profile
        job_posts = JobPost.objects.filter(hr=hr)
        
        job_id = request.query_params.get('job_id')
        min_score = request.query_params.get('min_score')
        
        data = {
            'job_posts': JobPostSerializer(job_posts, many=True).data,
            'selected_job': None,
            'results': []
        }
        
        if job_id:
            job = get_object_or_404(JobPost, id=job_id, hr=hr)
            data['selected_job'] = JobPostSerializer(job).data
            # Add helper fields for keywords
            data['selected_job']['required_skills'] = job.required_skills.split(',') if job.required_skills else []
            data['selected_job']['requirements_keywords'] = job.requirements.split(',') if job.requirements else []
            
            results = ATSResult.objects.filter(job_post=job)
            if min_score:
                results = results.filter(score__gte=min_score)
            
            results = results.order_by('-score')
            
            res_data = []
            for r in results:
                res_data.append({
                    'id': r.id,
                    'candidate_name': r.resume.jobseeker.full_name if r.resume.jobseeker else f"Candidate #{r.id}",
                    'resume_filename': r.resume.filename,
                    'status': r.status,
                    'score': r.score
                })
            data['results'] = res_data
            
        return Response(data)

@method_decorator(csrf_exempt, name='dispatch')
class HRCandidateDetailView(APIView):
    authentication_classes = (CsrfExemptSessionAuthentication,)
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        result_id = request.query_params.get('result_id')
        result = get_object_or_404(ATSResult, id=result_id, job_post__hr=request.user.hr_profile)
        
        return Response({
            'result': {
                'id': result.id,
                'status': result.status,
                'score': result.score,
                'concise_feedback': result.feedback,
                'matched_list': result.matched_keywords.split(',') if result.matched_keywords else [],
                'missing_list': result.missing_keywords.split(',') if result.missing_keywords else [],
                'candidate_name': result.resume.jobseeker.full_name if result.resume.jobseeker else f"Candidate #{result.id}",
                'resume': {
                    'filename': result.resume.filename,
                    'uploaded_at': result.resume.uploaded_at.strftime('%b %d, %Y'),
                    'file_url': result.resume.file.url
                },
                'job_post': {
                    'id': result.job_post.id,
                    'title': result.job_post.title,
                    'company': result.job_post.hr.company,
                    'requirements': result.job_post.requirements
                }
            }
        })
