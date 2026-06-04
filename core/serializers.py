from rest_framework import serializers
from .models import (
    User, JobseekerProfile, Education, Experience, Project, Skill, 
    Certificate, Reference, HRProfile, JobPost, Resume, ParsedResumeData, 
    ATSResult, Notification, ContactMessage, SupportRequest
)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'role', 'is_verified']

class EducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Education
        fields = '__all__'
        extra_kwargs = {'profile': {'required': False}}

class ExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Experience
        fields = '__all__'
        extra_kwargs = {'profile': {'required': False}}

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = '__all__'
        extra_kwargs = {'profile': {'required': False}}

class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = '__all__'
        extra_kwargs = {'profile': {'required': False}}

class CertificateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certificate
        fields = '__all__'
        extra_kwargs = {'profile': {'required': False}}

class ReferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reference
        fields = '__all__'
        extra_kwargs = {'profile': {'required': False}}

class JobseekerProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField(source='user.full_name')
    email = serializers.ReadOnlyField(source='user.email')
    educations = EducationSerializer(many=True, read_only=True)
    experiences = ExperienceSerializer(many=True, read_only=True)
    projects = ProjectSerializer(many=True, read_only=True)
    skills = SkillSerializer(many=True, read_only=True)
    certificates = CertificateSerializer(many=True, read_only=True)
    references = ReferenceSerializer(many=True, read_only=True)

    class Meta:
        model = JobseekerProfile
        fields = '__all__'

    def update(self, instance, validated_data):
        # 1. Update User fields if present
        user_instance = instance.user
        full_name = self.initial_data.get('full_name')
        email = self.initial_data.get('email')
        
        updated_user = False
        if full_name:
            user_instance.full_name = full_name
            updated_user = True
        if email:
            user_instance.email = email
            updated_user = True
        if updated_user:
            user_instance.save()
            
        # 2. Update Profile fields
        return super().update(instance, validated_data)

class HRProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = HRProfile
        fields = '__all__'

class JobPostSerializer(serializers.ModelSerializer):
    candidate_count = serializers.SerializerMethodField()
    top_score = serializers.SerializerMethodField()
    is_expired = serializers.ReadOnlyField()
    company_name = serializers.CharField(source='hr.company', read_only=True)

    class Meta:
        model = JobPost
        fields = '__all__'
        read_only_fields = ('hr',)

    def get_candidate_count(self, obj):
        return obj.ats_results.count()

    def get_top_score(self, obj):
        from django.db.models import Max
        top = obj.ats_results.aggregate(Max('score'))['score__max']
        return round(top, 1) if top else 0

    def validate_deadline(self, value):
        if value == "":
            return None
        return value

class ParsedResumeDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParsedResumeData
        fields = '__all__'

class ResumeSerializer(serializers.ModelSerializer):
    parsed_data = ParsedResumeDataSerializer(read_only=True)
    file_size = serializers.SerializerMethodField()

    class Meta:
        model = Resume
        fields = '__all__'

    def get_file_size(self, obj):
        try:
            return obj.file.size
        except:
            return 0

class ATSResultSerializer(serializers.ModelSerializer):
    resume = ResumeSerializer(read_only=True)
    job_post = JobPostSerializer(read_only=True)
    job_title = serializers.SerializerMethodField()
    company_name = serializers.SerializerMethodField()
    formatted_date = serializers.SerializerMethodField()
    suggestions = serializers.SerializerMethodField()
    pillars = serializers.SerializerMethodField()
    matched_list = serializers.SerializerMethodField()
    missing_list = serializers.SerializerMethodField()
    strengths = serializers.SerializerMethodField()
    recommendations = serializers.SerializerMethodField()

    class Meta:
        model = ATSResult
        fields = [
            'id', 'resume', 'job_post', 'custom_job_title', 'score', 
            'feedback', 'analyzed_at', 'status', 'score_breakdown',
            'matched_list', 'missing_list', 
            'job_title', 'company_name', 'formatted_date', 'suggestions', 'pillars',
            'strengths', 'recommendations'
        ]

    def get_job_title(self, obj):
        if obj.job_post:
            return obj.job_post.title
        return obj.custom_job_title or "Quick ATS Scan"

    def get_company_name(self, obj):
        if obj.job_post:
            return obj.job_post.hr.company
        return "Internal Verification"

    def get_formatted_date(self, obj):
        return obj.analyzed_at.strftime("%b %d, %Y")

    def get_matched_list(self, obj):
        if not obj.matched_keywords: return []
        # Support both comma-separated and semicolon-separated as a safety net
        keywords = obj.matched_keywords.replace(';', ',').split(',')
        return [k.strip() for k in keywords if k.strip()]

    def _fallback_breakdown(self, obj):
        """
        Rebuild a breakdown for older ATS results that were saved before
        score_breakdown was populated consistently.
        """
        try:
            from .utils import calculate_ats_score, extract_text_from_pdf, extract_text_from_docx
        except Exception:
            return {}

        resume = getattr(obj, "resume", None)
        job_post = getattr(obj, "job_post", None)
        if not resume:
            return {}

        parsed_data = getattr(resume, "parsed_data", None)
        text = getattr(parsed_data, "extracted_text", "") if parsed_data else ""

        if not text:
            try:
                ext = (resume.filename or "").split(".")[-1].lower()
                file_path = resume.file.path
                text = extract_text_from_pdf(file_path) if ext == "pdf" else extract_text_from_docx(file_path)
            except Exception:
                text = ""

        if not text:
            return {}

        jd_fields = None
        jd_text = ""
        if job_post:
            jd_fields = {
                "title": job_post.title or "",
                "description": job_post.description or "",
                "required_skills": job_post.required_skills or "",
                "experience_requirements": job_post.experience_requirements or "",
                "education_requirements": job_post.education_requirements or "",
                "tools_and_technologies": job_post.tools_and_technologies or "",
                "requirements": job_post.requirements or "",
            }
            jd_text = job_post.requirements or job_post.description or ""

        analysis = calculate_ats_score(text, jd_text, jd_fields=jd_fields)
        return {
            "pillars": analysis.get("pillars", {}),
            "suggestions": analysis.get("suggestions", []),
            "strengths": analysis.get("strengths", []),
            "recommendations": analysis.get("weaknesses", []),
        }

    def get_missing_list(self, obj):
        if not obj.missing_keywords: return []
        keywords = obj.missing_keywords.replace(';', ',').split(',')
        return [k.strip() for k in keywords if k.strip()]

    def get_suggestions(self, obj):
        try:
            import json
            data = json.loads(obj.score_breakdown)
            return data.get('suggestions', [])
        except:
            return []

    def get_pillars(self, obj):
        try:
            import json
            data = json.loads(obj.score_breakdown)
            pillars = data.get('pillars', data) # Fallback to entire object if no pillars key
            if pillars:
                return pillars
        except:
            pass

        fallback = self._fallback_breakdown(obj)
        if fallback.get("pillars"):
            return fallback["pillars"]
        return {}

    def get_strengths(self, obj):
        try:
            import json
            data = json.loads(obj.score_breakdown)
            return data.get('strengths', [])
        except:
            fallback = self._fallback_breakdown(obj)
            return fallback.get("strengths", [])

    def get_recommendations(self, obj):
        try:
            import json
            data = json.loads(obj.score_breakdown)
            return data.get('recommendations', [])
        except:
            fallback = self._fallback_breakdown(obj)
            return fallback.get("recommendations", [])

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'

class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = '__all__'

class SupportRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportRequest
        fields = '__all__'
