from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from .models import Feedback

def get_daily_issue_summary(cafe=None):
    """
    Counts feedback from the last 24 hours, groups by issue,
    and returns a summary string of the top issue.
    """
    time_threshold = timezone.now() - timedelta(hours=24)
    qs = Feedback.objects.filter(created_at__gte=time_threshold)
    
    if cafe:
        qs = qs.filter(cafe=cafe)
        
    # Exclude empty or null issues, group by issue, and count
    top_issue = (qs.exclude(issue='')
                   .exclude(issue__isnull=True)
                   .values('issue')
                   .annotate(count=Count('id'))
                   .order_by('-count')
                   .first())
                   
    if top_issue:
        return f"Top issue: {top_issue['issue']} ({top_issue['count']} complaints)"
    return "No issues reported in the last 24 hours."
