import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from .models import Cafe, Feedback

logger = logging.getLogger('reviews')

def cafe_view(request, slug):
    try:
        cafe = Cafe.objects.get(slug=slug)
    except Cafe.DoesNotExist:
        logger.warning(f"Cafe not found for slug: {slug}")
        return render(request, 'reviews/404.html', status=404)
    
    if request.method == 'POST':
        # Check if this is the second step (submitting the detailed feedback)
        if request.POST.get('is_feedback'):
            feedback_id = request.POST.get('feedback_id')
            # Safely check if feedback_id is valid and exists
            if feedback_id and str(feedback_id).isdigit():
                feedback = Feedback.objects.filter(id=feedback_id, cafe=cafe).first()
                if feedback:
                    feedback.issue = request.POST.get('issue', '')
                    feedback.comment = request.POST.get('comment', '')
                    feedback.save()
                    logger.info(f"Detailed feedback updated for cafe '{cafe.slug}': rating={feedback.rating}, issue='{feedback.issue}'")
                else:
                    logger.warning(f"Feedback ID {feedback_id} not found for cafe '{cafe.slug}' during update.")
            else:
                logger.error(f"Invalid or missing feedback_id '{feedback_id}' for cafe '{cafe.slug}'")
            
            request.session['flash_success'] = True
            return redirect('/thank-you/')
            
        # First step: User clicked a rating button
        raw_rating = request.POST.get('rating')
        if not raw_rating:
            logger.warning(f"Submission missing rating for cafe '{cafe.slug}'")
            return render(request, 'reviews/cafe.html', {'cafe': cafe, 'error': 'Please tap a star to leave a rating.'})

        try:
            rating = int(raw_rating)
        except ValueError as e:
            logger.error(f"Error parsing rating '{raw_rating}' for cafe '{cafe.slug}': {e}")
            return render(request, 'reviews/cafe.html', {'cafe': cafe, 'error': 'Invalid data provided. Please try again.'})
            
        if not (1 <= rating <= 5):
            logger.warning(f"Invalid rating value {rating} for cafe '{cafe.slug}'")
            return render(request, 'reviews/cafe.html', {'cafe': cafe, 'error': 'Rating must be between 1 and 5.'})
        
        # Save the feedback immediately for ALL ratings
        feedback = Feedback.objects.create(cafe=cafe, rating=rating)
        logger.info(f"New feedback created for cafe '{cafe.slug}': rating={rating}, is_positive={feedback.is_positive}")
        
        if rating >= 4:
            return render(request, 'reviews/cafe.html', {
                'cafe': cafe,
                'show_google_review_prompt': True,
            })
        else:
            return render(request, 'reviews/cafe.html', {
                'cafe': cafe,
                'show_feedback_form': True,
                'selected_rating': rating,
                'feedback_id': feedback.id
            })
            
    return render(request, 'reviews/cafe.html', {'cafe': cafe})

def thank_you_view(request):
    show_flash = request.session.pop('flash_success', False)
    return render(request, 'reviews/thank_you.html', {'show_flash': show_flash})

def cafes_list_view(request):
    cafes = Cafe.objects.all()
    return render(request, 'reviews/cafes_list.html', {'cafes': cafes})


from django.db.models import Avg, Count, Q
from django.contrib.admin.views.decorators import staff_member_required

def home_view(request):
    cafes = Cafe.objects.all()
    return render(request, 'reviews/home.html', {'cafes': cafes})

@staff_member_required
def analytics_dashboard_view(request):
    selected_slug = request.GET.get('cafe')
    cafes_list = Cafe.objects.all()
    
    feedbacks = Feedback.objects.all()
    if selected_slug and selected_slug != 'all':
        feedbacks = feedbacks.filter(cafe__slug=selected_slug)
        
    total_cafes = cafes_list.count()
    total_feedback = feedbacks.count()
    positive_feedback = feedbacks.filter(rating__gte=4).count()
    negative_feedback = feedbacks.filter(rating__lte=3).count()
    
    avg_rating = feedbacks.aggregate(Avg('rating'))['rating__avg'] or 0.0
    
    positive_percentage = ((positive_feedback / total_feedback) * 100) if total_feedback > 0 else 0.0
    
    # Ratings distribution
    ratings_dist = feedbacks.values('rating').annotate(count=Count('id')).order_by('-rating')
    ratings_dict = {i: 0 for i in range(1, 6)}
    for r in ratings_dist:
        ratings_dict[r['rating']] = r['count']
        
    # Issues breakdown
    issues_dist = feedbacks.exclude(issue__isnull=True).exclude(issue='').values('issue').annotate(count=Count('id')).order_by('-count')
    
    top_complaint = "None"
    if issues_dist.exists():
        first_issue = issues_dist[0]
        top_complaint = f"{first_issue['issue']} ({first_issue['count']})"
    
    issue_counts = {
        'Food': feedbacks.filter(issue='Food').count(),
        'Service': feedbacks.filter(issue='Service').count(),
        'Delay': feedbacks.filter(issue='Delay').count(),
        'Cleanliness': feedbacks.filter(issue='Cleanliness').count(),
    }
    
    # Cafe-specific stats
    if selected_slug and selected_slug != 'all':
        cafes_stats = Cafe.objects.filter(slug=selected_slug).annotate(
            feedback_count=Count('feedback'),
            avg_rating=Avg('feedback__rating'),
            positive_count=Count('feedback', filter=Q(feedback__is_positive=True))
        )
    else:
        cafes_stats = Cafe.objects.annotate(
            feedback_count=Count('feedback'),
            avg_rating=Avg('feedback__rating'),
            positive_count=Count('feedback', filter=Q(feedback__is_positive=True))
        )
    
    cafe_data = []
    for c in cafes_stats:
        pos_rate = (c.positive_count / c.feedback_count * 100) if c.feedback_count > 0 else 0.0
        cafe_data.append({
            'name': c.name,
            'slug': c.slug,
            'feedback_count': c.feedback_count,
            'avg_rating': round(c.avg_rating, 2) if c.avg_rating else 0.0,
            'positive_rate': round(pos_rate, 1),
            'logo': c.logo.url if c.logo else None
        })
        
    # Recent feedbacks
    recent_feedbacks = feedbacks.select_related('cafe').order_by('-created_at')[:10]
    
    context = {
        'total_cafes': total_cafes,
        'total_feedback': total_feedback,
        'positive_feedback': positive_feedback,
        'negative_feedback': negative_feedback,
        'avg_rating': round(avg_rating, 2),
        'positive_percentage': round(positive_percentage, 1),
        'ratings_dist': ratings_dict,
        'issues_dist': issues_dist,
        'issue_counts': issue_counts,
        'top_complaint': top_complaint,
        'cafe_data': cafe_data,
        'recent_feedbacks': recent_feedbacks,
        'cafes_list': cafes_list,
        'selected_slug': selected_slug or 'all',
    }
    return render(request, 'reviews/analytics.html', context)
