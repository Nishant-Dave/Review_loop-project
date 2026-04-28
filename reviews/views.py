from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from .models import Cafe, Feedback

def cafe_view(request, slug):
    cafe = get_object_or_404(Cafe, slug=slug)
    
    if request.method == 'POST':
        # Check if this is the second step (submitting the detailed feedback)
        if request.POST.get('is_feedback'):
            rating = int(request.POST.get('rating', 0))
            issue = request.POST.get('issue', '')
            comment = request.POST.get('comment', '')
            Feedback.objects.create(
                cafe=cafe,
                rating=rating,
                issue=issue,
                comment=comment
            )
            return redirect('/thank-you/')
            
        # First step: User clicked a rating button
        rating = int(request.POST.get('rating', 0))
        
        if rating >= 4:
            return redirect(cafe.google_review_link)
        else:
            return render(request, 'reviews/cafe.html', {
                'cafe': cafe,
                'show_feedback_form': True,
                'selected_rating': rating
            })
            
    return render(request, 'reviews/cafe.html', {'cafe': cafe})

def thank_you_view(request):
    return render(request, 'reviews/thank_you.html')

