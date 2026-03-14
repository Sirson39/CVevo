from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def hr_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not hasattr(request.user, 'hr_profile'):
            messages.error(request, "Access denied. HR account required.")
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def jobseeker_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not hasattr(request.user, 'jobseeker_profile'):
            messages.error(request, "Access denied. Jobseeker account required.")
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view