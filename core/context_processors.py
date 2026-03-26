from .models import Notification

def notifications_processor(request):
    if request.user.is_authenticated:
        qs = Notification.objects.filter(user=request.user).order_by("-created_at")[:4]
        unread_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()

        return {
            "user_notifications": qs,
            "unread_notifications_count": unread_count,
        }

    return {
        "user_notifications": [],
        "unread_notifications_count": 0,
    }