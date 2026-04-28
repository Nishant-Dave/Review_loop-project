from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Count
from datetime import timedelta
from reviews.models import Feedback

class Command(BaseCommand):
    help = 'Generates a report of feedback from the last 24 hours'

    def handle(self, *args, **options):
        # Time 24 hours ago
        last_24_hours = timezone.now() - timedelta(hours=24)
        
        # Query feedback from the last 24 hours
        recent_feedback = Feedback.objects.filter(created_at__gte=last_24_hours)
        
        # Total count
        total_feedback = recent_feedback.count()
        
        self.stdout.write(f"- Total feedback: {total_feedback}")
        
        if total_feedback > 0:
            # Group by issue and count, ordering by the highest count
            # We exclude empty issues to focus on categorized problems
            issues = recent_feedback.exclude(issue='').values('issue').annotate(count=Count('id')).order_by('-count')
            
            for item in issues:
                self.stdout.write(f"- {item['issue']}: {item['count']}")
