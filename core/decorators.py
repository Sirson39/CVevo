from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def hr_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.role != 'hr':
            messages.error(request, "Access denied. HR account required.")
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def jobseeker_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.role != 'jobseeker':
            messages.error(request, "Access denied. Jobseeker account required.")
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('admin_login')
        if request.user.role != 'admin' and not request.user.is_staff:
            messages.error(request, "Access denied. Administrator privileges required.")
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view