from django.shortcuts import redirect
from django.http import JsonResponse

def home(request):
    """Refactored: Redirect to the decoupled frontend homepage."""
    return redirect('/pages/public/index.html')

def post_login_redirect(request):
    """Refactored: Redirect after login based on user role using pure JS/static logic."""
    if not request.user.is_authenticated:
        return redirect('/pages/public/login.html')
    
    if request.user.role == 'hr':
        return redirect('/pages/hr/hr_dashboard.html')
    elif request.user.role in ['admin', 'superuser']:
        return redirect('/sysadmin/')
    else:
        return redirect('/pages/jobseeker/jobseeker_dashboard.html')

def google_start(request, acct):
    """Bridge for Social Auth while using decoupled frontend."""
    if acct == "hr":
        return redirect('/pages/public/auth-register-hr.html')
    
    if acct not in ("jobseeker",):
        acct = "jobseeker"
        
    request.session["oauth_account_type"] = acct
    request.session.save()
    return redirect("/accounts/google/login/")

def mark_notifications_read(request):
    """Utility endpoint to mark read and redirect back."""
    if request.user.is_authenticated:
        request.user.notifications.filter(is_read=False).update(is_read=True)
    return redirect(request.META.get('HTTP_REFERER', '/'))

# All other views that were previously template-based are now served as static HTML 
# and interact with the API via DRF. The urls.py will handle the routing.