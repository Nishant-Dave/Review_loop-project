from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from .models import Feedback

def get_daily_feedback_stats(cafe=None):
    """
    Returns a structured summary of feedback from the last 24 hours:
    - Total feedback count
    - Positive count (rating >= 4)
    - Negative count (rating < 4)
    - Most common issue
    """
    time_threshold = timezone.now() - timedelta(hours=24)
    qs = Feedback.objects.filter(created_at__gte=time_threshold)
    
    if cafe:
        qs = qs.filter(cafe=cafe)
        
    total_count = qs.count()
    positive_count = qs.filter(rating__gte=4).count()
    negative_count = qs.filter(rating__lt=4).count()
    
    # Exclude empty or null issues, group by issue, and count
    top_issue_data = (qs.exclude(issue='')
                        .exclude(issue__isnull=True)
                        .values('issue')
                        .annotate(count=Count('id'))
                        .order_by('-count')
                        .first())
                        
    most_common_issue = None
    if top_issue_data:
        most_common_issue = f"{top_issue_data['issue']} ({top_issue_data['count']} reports)"
        
    return {
        'total_today': total_count,
        'positive': positive_count,
        'negative': negative_count,
        'top_issue': most_common_issue or "No issues reported"
    }

