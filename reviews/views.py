import logging
import io
import os
import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, FileResponse
from django.db.models import Avg, Count, Q
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

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
                    
                    # Extract optional follow-up details (only saved if BOTH mobile and consent are provided for low ratings 1 or 2)
                    mobile = request.POST.get('customer_mobile', '').strip()
                    consent = 'consent_to_contact' in request.POST
                    if feedback.rating <= 2 and mobile and consent:
                        feedback.customer_mobile = mobile
                        feedback.consent_to_contact = True
                    else:
                        feedback.customer_mobile = None
                        feedback.consent_to_contact = False
                    
                    # Trigger AI sentiment & response analysis if rating is 3 or below and comment is provided
                    if feedback.rating <= 3 and feedback.comment:
                        try:
                            from .services.ai_review_analysis import analyze_negative_feedback
                            ai_data = analyze_negative_feedback(feedback)
                            feedback.ai_sentiment = ai_data.get('sentiment')
                            feedback.ai_emotion = ai_data.get('emotion')
                            feedback.ai_urgency = ai_data.get('urgency')
                            feedback.ai_reply_1 = ai_data.get('reply_1')
                            feedback.ai_reply_2 = ai_data.get('reply_2')
                            feedback.ai_reply_3 = ai_data.get('reply_3')
                        except Exception as ai_err:
                            logger.error(f"Gracefully caught error calling AI analysis service: {ai_err}")
                            
                    feedback.save()
                    logger.info(f"Detailed feedback updated for cafe '{cafe.slug}': rating={feedback.rating}, issue='{feedback.issue}', contact={feedback.consent_to_contact}")
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


def download_qr_poster_view(request, slug):
    cafe = get_object_or_404(Cafe, slug=slug)
    
    buffer = io.BytesIO()
    
    # Page setup: A4 format with precise boundaries to prevent overflow
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    # ----------------------------------------------------
    # Premium Typography & Styling Config
    # ----------------------------------------------------
    title_style = ParagraphStyle(
        'PremiumPosterTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=32,
        leading=38,
        alignment=1, # Centered
        textColor=colors.HexColor('#0F172A'), # Slate 900
        spaceAfter=0
    )
    
    tagline_style = ParagraphStyle(
        'PremiumPosterTagline',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=15,
        leading=19,
        alignment=1, # Centered
        textColor=colors.HexColor('#475569'), # Slate 600
        spaceAfter=0
    )
    
    heading_style = ParagraphStyle(
        'PremiumPosterHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        alignment=1, # Centered
        textColor=colors.HexColor('#1E293B'), # Slate 800
        spaceAfter=0
    )
    
    stars_style = ParagraphStyle(
        'PremiumPosterStars',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=22,
        leading=26,
        alignment=1, # Centered
        textColor=colors.HexColor('#F59E0B'), # Gold Star color
        spaceAfter=0
    )
    
    cta_style = ParagraphStyle(
        'PremiumPosterCTA',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=19,
        leading=23,
        alignment=1, # Centered
        textColor=colors.HexColor('#0F172A'), # Slate 900
        spaceAfter=0
    )
    
    footer_style = ParagraphStyle(
        'PremiumPosterFooter',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=11,
        leading=15,
        alignment=1, # Centered
        textColor=colors.HexColor('#94A3B8'), # Slate 400
        spaceAfter=0
    )
    
    qr_label_style = ParagraphStyle(
        'PremiumPosterQRLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        alignment=1, # Centered
        textColor=colors.HexColor('#64748B'), # Slate 500
        spaceAfter=0
    )
    
    # ----------------------------------------------------
    # Component Building (Poster Card Internals)
    # ----------------------------------------------------
    card_elements = []
    
    # 1. Cafe Logo (centered & scaled elegantly, utilizing stream for cloud storage compatibility)
    if cafe.logo:
        try:
            logo_img = Image(io.BytesIO(cafe.logo.read()), width=1.1*inch, height=1.1*inch)
            logo_img.hAlign = 'CENTER'
            card_elements.append(logo_img)
            card_elements.append(Spacer(1, 12))
        except Exception:
            pass
    else:
        card_elements.append(Spacer(1, 15))
            
    # 2. Cafe Name (bold, uppercase, centered)
    card_elements.append(Paragraph(cafe.name.upper(), title_style))
    card_elements.append(Spacer(1, 8))
    
    # 3. Cafe Tagline (if it exists, italicized, centered)
    if cafe.tagline:
        card_elements.append(Paragraph(cafe.tagline, tagline_style))
        card_elements.append(Spacer(1, 12))
    
    # Minimalist Gold Accent Line
    separator_table = Table([['']], colWidths=[60], rowHeights=[1])
    separator_table.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, -1), 2, colors.HexColor('#D97706')), # Rich Gold
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
    ]))
    separator_table.hAlign = 'CENTER'
    card_elements.append(separator_table)
    card_elements.append(Spacer(1, 20))
    
    # 4. Big QR Code Container (neatly framed card-in-card with camera label)
    if cafe.qr_code:
        try:
            qr_img = Image(io.BytesIO(cafe.qr_code.read()), width=2.8*inch, height=2.8*inch)
            qr_img.hAlign = 'CENTER'
            
            # QR content holds scan label, spacer, and image
            qr_container_elements = [
                Paragraph("SCAN WITH PHONE CAMERA", qr_label_style),
                Spacer(1, 10),
                qr_img
            ]
            
            # Table representing the framed container card
            qr_frame = Table([[qr_container_elements]], colWidths=[250], rowHeights=[245])
            qr_frame.setStyle(TableStyle([
                ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#E2E8F0')), # Soft Slate border
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')), # Very light Slate backdrop
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 15),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
            ]))
            qr_frame.hAlign = 'CENTER'
            card_elements.append(qr_frame)
            card_elements.append(Spacer(1, 25))
        except Exception:
            card_elements.append(Paragraph("<font color='red'>QR Code not found</font>", footer_style))
            card_elements.append(Spacer(1, 20))
    else:
        card_elements.append(Paragraph("<font color='red'>QR Code not generated</font>", footer_style))
        card_elements.append(Spacer(1, 20))
        
    # 5. Heading: Loved your experience?
    card_elements.append(Paragraph("Loved your experience?", heading_style))
    card_elements.append(Spacer(1, 8))
    
    # 6. Elegant Golden Rating Star Row Accent
    card_elements.append(Paragraph("&#9733; &#9733; &#9733; &#9733; &#9733;", stars_style))
    card_elements.append(Spacer(1, 10))
    
    # 7. CTA: Scan & review us
    card_elements.append(Paragraph("Scan & review us", cta_style))
    card_elements.append(Spacer(1, 12))
    
    # 8. Footer: It takes less than 10 seconds
    card_elements.append(Paragraph("It takes less than 10 seconds", footer_style))
    
    # ----------------------------------------------------
    # High-End Dual Framing Layout
    # ----------------------------------------------------
    # Inner border table (Gold accent border)
    inner_card = Table([[card_elements]], colWidths=[476], rowHeights=[716])
    inner_card.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#F59E0B')), # Elegant Gold inner border
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FFFFFF')),
        ('TOPPADDING', (0, 0), (-1, -1), 30),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 30),
        ('LEFTPADDING', (0, 0), (-1, -1), 25),
        ('RIGHTPADDING', (0, 0), (-1, -1), 25),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    # Outer border table (Dark Slate main frame)
    outer_card = Table([[inner_card]], colWidths=[500], rowHeights=[740])
    outer_card.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 2.5, colors.HexColor('#0F172A')), # Dark Slate outer frame
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FFFFFF')),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(outer_card)
    
    # Build document
    doc.build(story)
    
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f"{cafe.slug}_qr_poster.pdf")
