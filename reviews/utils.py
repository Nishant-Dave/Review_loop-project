from django.db.models import Count

def get_top_issue(queryset):
    """
    Takes a feedback queryset and returns the most common issue.
    """
    top_issue = queryset.exclude(issue='').values('issue').annotate(count=Count('id')).order_by('-count').first()
    
    if top_issue:
        return f"Top issue today: {top_issue['issue']} ({top_issue['count']} complaints)"
    return "No issues reported today."
