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

