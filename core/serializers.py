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
    summary = serializers.CharField(source='bio', allow_blank=True, required=False)
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

    class Meta:
        model = ATSResult
        fields = [
            'id', 'resume', 'job_post', 'custom_job_title', 'score', 
            'feedback', 'analyzed_at', 'status', 'score_breakdown',
            'matched_list', 'missing_list', 
            'job_title', 'company_name', 'formatted_date', 'suggestions', 'pillars'
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
            return data.get('pillars', data) # Fallback to entire object if no pillars key
        except:
            return {}

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
