from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from reviews.models import Cafe, Feedback

class AnalyticsDashboardTests(TestCase):
    def setUp(self):
        # Create a test staff user and a non-staff user
        self.staff_user = User.objects.create_user(
            username='staff', 
            password='password123', 
            is_staff=True
        )
        self.regular_user = User.objects.create_user(
            username='regular', 
            password='password123', 
            is_staff=False
        )

        # Create two test cafes
        self.cafe_a = Cafe.objects.create(
            name="Cafe Alpha",
            slug="cafe-alpha",
            google_review_link="https://google.com/review-a"
        )
        self.cafe_b = Cafe.objects.create(
            name="Cafe Beta",
            slug="cafe-beta",
            google_review_link="https://google.com/review-b"
        )

        # Create feedbacks for Cafe Alpha
        # 2 Positive, 1 Negative
        Feedback.objects.create(cafe=self.cafe_a, rating=5, issue=None, comment="Great food!")
        Feedback.objects.create(cafe=self.cafe_a, rating=4, issue=None, comment="Nice place.")
        Feedback.objects.create(cafe=self.cafe_a, rating=2, issue="Service", comment="Very slow service.")

        # Create feedbacks for Cafe Beta
        # 1 Positive, 1 Negative
        Feedback.objects.create(cafe=self.cafe_b, rating=4, issue=None, comment="Decent.")
        Feedback.objects.create(cafe=self.cafe_b, rating=3, issue="Food", comment="Cold burger.")

        self.url = reverse('analytics_dashboard_view')

    def test_anonymous_user_redirected_to_login(self):
        """Anonymous users must be redirected to the login page."""
        response = self.client.get(self.url)
        self.assertNotEqual(response.status_code, 200)
        self.assertIn('login', response.url)

    def test_regular_user_redirected_or_forbidden(self):
        """Non-staff users must not have access to the analytics dashboard."""
        self.client.login(username='regular', password='password123')
        response = self.client.get(self.url)
        self.assertNotEqual(response.status_code, 200)
        self.assertIn('login', response.url)

    def test_staff_user_can_access_dashboard_all_cafes(self):
        """Staff users can access the dashboard, seeing aggregate statistics for all cafes."""
        self.client.login(username='staff', password='password123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        
        # Check context calculations
        self.assertEqual(response.context['total_feedback'], 5)
        self.assertEqual(response.context['positive_feedback'], 3)
        self.assertEqual(response.context['negative_feedback'], 2)
        self.assertAlmostEqual(response.context['positive_percentage'], 60.0)
        
        # Check issue counts
        self.assertEqual(response.context['issue_counts']['Service'], 1)
        self.assertEqual(response.context['issue_counts']['Food'], 1)
        self.assertEqual(response.context['issue_counts']['Delay'], 0)
        self.assertEqual(response.context['issue_counts']['Cleanliness'], 0)

        # Check top complaint calculation
        self.assertIn(response.context['top_complaint'], ['Service (1)', 'Food (1)'])

        # Check that both cafes are returned in cafe_data
        self.assertEqual(len(response.context['cafe_data']), 2)

        # Check rendered content (dropdown selector is present)
        self.assertContains(response, 'Select Cafe:')
        self.assertContains(response, 'value="all"')
        self.assertContains(response, 'value="cafe-alpha"')
        self.assertContains(response, 'value="cafe-beta"')

    def test_staff_user_filter_by_specific_cafe(self):
        """Filtering by a specific cafe slug updates all context metrics for that cafe only."""
        self.client.login(username='staff', password='password123')
        
        # Filter by Cafe Alpha
        response = self.client.get(self.url, {'cafe': 'cafe-alpha'})
        self.assertEqual(response.status_code, 200)
        
        # Verify cafe alpha metrics only
        self.assertEqual(response.context['total_feedback'], 3)
        self.assertEqual(response.context['positive_feedback'], 2)
        self.assertEqual(response.context['negative_feedback'], 1)
        self.assertAlmostEqual(response.context['positive_percentage'], 66.7)
        self.assertEqual(response.context['issue_counts']['Service'], 1)
        self.assertEqual(response.context['issue_counts']['Food'], 0)
        self.assertEqual(response.context['selected_slug'], 'cafe-alpha')
        self.assertEqual(response.context['top_complaint'], 'Service (1)')
        
        # Verify cafe_data contains only the selected cafe
        self.assertEqual(len(response.context['cafe_data']), 1)
        self.assertEqual(response.context['cafe_data'][0]['slug'], 'cafe-alpha')

        # Filter by Cafe Beta
        response = self.client.get(self.url, {'cafe': 'cafe-beta'})
        self.assertEqual(response.status_code, 200)
        
        # Verify cafe beta metrics only
        self.assertEqual(response.context['total_feedback'], 2)
        self.assertEqual(response.context['positive_feedback'], 1)
        self.assertEqual(response.context['negative_feedback'], 1)
        self.assertAlmostEqual(response.context['positive_percentage'], 50.0)
        self.assertEqual(response.context['issue_counts']['Service'], 0)
        self.assertEqual(response.context['issue_counts']['Food'], 1)
        self.assertEqual(response.context['selected_slug'], 'cafe-beta')
        self.assertEqual(response.context['top_complaint'], 'Food (1)')

        # Verify cafe_data contains only the selected cafe
        self.assertEqual(len(response.context['cafe_data']), 1)
        self.assertEqual(response.context['cafe_data'][0]['slug'], 'cafe-beta')

    def test_home_page_anonymous_user_sees_login_button(self):
        """Anonymous guests should see the Admin Login button pointing to the admin login page."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '🔐 Admin Login')
        self.assertContains(response, '/admin/login/')
        self.assertNotContains(response, '📊 Analytics Dashboard')

    def test_home_page_authenticated_user_sees_analytics_button(self):
        """Logged-in users should see the Analytics Dashboard button pointing to the analytics page."""
        self.client.login(username='staff', password='password123')
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '📊 Analytics Dashboard')
        self.assertContains(response, '/analytics/')
        self.assertNotContains(response, '🔐 Admin Login')


class PDFQRPosterTests(TestCase):
    def setUp(self):
        self.cafe = Cafe.objects.create(
            name="Poster Cafe",
            slug="poster-cafe",
            tagline="Best Coffee in Town",
            google_review_link="https://google.com/review"
        )
        self.url = reverse('download_qr_poster', kwargs={'slug': self.cafe.slug})

    def test_download_poster_success(self):
        """A valid cafe slug returns a downloadable PDF poster."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn('poster-cafe_qr_poster.pdf', response['Content-Disposition'])

    def test_download_poster_404_not_found(self):
        """A non-existent slug returns 404."""
        url_invalid = reverse('download_qr_poster', kwargs={'slug': 'non-existent-cafe'})
        response = self.client.get(url_invalid)
        self.assertEqual(response.status_code, 404)


class LowRatingFeedbackTests(TestCase):
    def setUp(self):
        self.cafe = Cafe.objects.create(
            name="Feedback Cafe",
            slug="feedback-cafe",
            google_review_link="https://google.com/review"
        )
        self.cafe_url = reverse('cafe_view', kwargs={'slug': self.cafe.slug})

    def test_low_rating_saves_mobile_and_consent(self):
        """Submit rating 2, then submit feedback with mobile and consent. Ensure it saves successfully."""
        # Step 1: Submit 2-star rating
        response = self.client.post(self.cafe_url, {'rating': '2'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Would you like us to personally follow up?')
        self.assertContains(response, 'Mobile number (optional)')
        
        # Check that a feedback row was created in step 1
        feedback = Feedback.objects.first()
        self.assertEqual(feedback.rating, 2)
        self.assertIsNone(feedback.customer_mobile)
        
        # Step 2: Submit detailed feedback form with contact info
        response = self.client.post(self.cafe_url, {
            'is_feedback': 'true',
            'feedback_id': str(feedback.id),
            'issue': 'Service',
            'comment': 'Slow service.',
            'customer_mobile': '1234567890',
            'consent_to_contact': 'on'
        })
        # Should redirect to thank you page
        self.assertRedirects(response, '/thank-you/')
        
        # Refresh and verify it saved successfully
        feedback.refresh_from_db()
        self.assertEqual(feedback.issue, 'Service')
        self.assertEqual(feedback.comment, 'Slow service.')
        self.assertEqual(feedback.customer_mobile, '1234567890')
        self.assertEqual(feedback.consent_to_contact, True)
        
        # Verify that AI sentiment analysis fields were triggered and populated
        self.assertEqual(feedback.ai_sentiment, "Negative")
        self.assertEqual(feedback.ai_emotion, "Disappointed")
        self.assertEqual(feedback.ai_urgency, "Medium")
        self.assertIsNotNone(feedback.ai_reply_1)
        self.assertIsNotNone(feedback.ai_reply_2)
        self.assertIsNotNone(feedback.ai_reply_3)

    def test_mid_rating_does_not_save_mobile_and_consent(self):
        """Submit rating 3. The follow-up UI should not be present, and posting contact info should be ignored."""
        # Step 1: Submit 3-star rating
        response = self.client.post(self.cafe_url, {'rating': '3'})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Would you like us to personally follow up?')
        
        feedback = Feedback.objects.first()
        self.assertEqual(feedback.rating, 3)
        
        # Step 2: Submit detailed feedback form, attempt to inject contact info
        response = self.client.post(self.cafe_url, {
            'is_feedback': 'true',
            'feedback_id': str(feedback.id),
            'issue': 'Food',
            'comment': 'Cold food.',
            'customer_mobile': '1234567890',
            'consent_to_contact': 'on'
        })
        self.assertRedirects(response, '/thank-you/')
        
        # Refresh and verify it did NOT save contact details (empty/default)
        feedback.refresh_from_db()
        self.assertEqual(feedback.issue, 'Food')
        self.assertEqual(feedback.comment, 'Cold food.')
        self.assertIsNone(feedback.customer_mobile)
        self.assertEqual(feedback.consent_to_contact, False)

    def test_low_rating_safety_checks_require_both_mobile_and_consent(self):
        """Submit rating 2. Posting only one of mobile or consent must NOT save the details."""
        # Case A: Mobile provided, but consent unchecked
        self.client.post(self.cafe_url, {'rating': '2'})
        feedback_a = Feedback.objects.order_by('-created_at').first()
        self.client.post(self.cafe_url, {
            'is_feedback': 'true',
            'feedback_id': str(feedback_a.id),
            'issue': 'Service',
            'comment': 'Unchecked consent.',
            'customer_mobile': '9876543210'
            # 'consent_to_contact' is omitted (unchecked)
        })
        feedback_a.refresh_from_db()
        self.assertIsNone(feedback_a.customer_mobile)
        self.assertEqual(feedback_a.consent_to_contact, False)

        # Case B: Consent checked, but mobile number blank
        self.client.post(self.cafe_url, {'rating': '2'})
        feedback_b = Feedback.objects.order_by('-created_at').first()
        self.client.post(self.cafe_url, {
            'is_feedback': 'true',
            'feedback_id': str(feedback_b.id),
            'issue': 'Cleanliness',
            'comment': 'Blank mobile.',
            'customer_mobile': '   ', # Whitespace / blank
            'consent_to_contact': 'on'
        })
        feedback_b.refresh_from_db()
        self.assertIsNone(feedback_b.customer_mobile)
        self.assertEqual(feedback_b.consent_to_contact, False)


from unittest.mock import patch, MagicMock
from reviews.services.ai_review_analysis import analyze_negative_feedback

class AINegativeFeedbackAnalysisTests(TestCase):
    def setUp(self):
        self.cafe = Cafe.objects.create(
            name="Mock Cafe",
            slug="mock-cafe",
            google_review_link="https://google.com/review"
        )
        self.feedback = Feedback.objects.create(
            cafe=self.cafe,
            rating=1,
            issue="Food",
            comment="Cold food and bad experience."
        )

    @patch('reviews.services.ai_review_analysis.Groq')
    @patch.dict('os.environ', {'GROQ_API_KEY': 'mock-api-key-12345'})
    def test_analyze_negative_feedback_success(self, mock_groq):
        """Test successful Groq API analysis returns correct JSON keys."""
        # Setup mock client response
        mock_client = MagicMock()
        mock_completion = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        
        mock_message.content = '{"sentiment": "Negative", "emotion": "Frustrated", "urgency": "High", "reply_1": "Sorry A", "reply_2": "Sorry B", "reply_3": "Sorry C"}'
        mock_choice.message = mock_message
        mock_completion.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_completion
        mock_groq.return_value = mock_client

        # Call the function
        result = analyze_negative_feedback(self.feedback)

        # Assertions
        self.assertEqual(result["sentiment"], "Negative")
        self.assertEqual(result["emotion"], "Frustrated")
        self.assertEqual(result["urgency"], "High")
        self.assertEqual(result["reply_1"], "Sorry A")
        self.assertEqual(result["reply_2"], "Sorry B")
        self.assertEqual(result["reply_3"], "Sorry C")
        mock_groq.assert_called_once_with(api_key="mock-api-key-12345")

    @patch('reviews.services.ai_review_analysis.Groq')
    @patch.dict('os.environ', {'GROQ_API_KEY': 'mock-api-key-12345'})
    def test_analyze_negative_feedback_api_error_returns_fallback(self, mock_groq):
        """Test that any Groq API exception is handled gracefully by returning fallback dict."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API error or timeout")
        mock_groq.return_value = mock_client

        # Call function
        result = analyze_negative_feedback(self.feedback)

        # Assertions
        self.assertEqual(result["sentiment"], "Negative")
        self.assertEqual(result["emotion"], "Disappointed")
        self.assertEqual(result["urgency"], "Medium")
        self.assertIn("sorry", result["reply_2"].lower())

    @patch('reviews.services.ai_review_analysis.os.getenv')
    def test_analyze_negative_feedback_no_api_key_returns_fallback(self, mock_getenv):
        """Test that if the GROQ_API_KEY is not defined, it returns the fallback dict without calling Groq."""
        # Ensure os.getenv('GROQ_API_KEY') returns None or empty
        mock_getenv.return_value = None

        with patch('reviews.services.ai_review_analysis.settings', spec=[]):
            result = analyze_negative_feedback(self.feedback)

        # Assertions
        self.assertEqual(result["sentiment"], "Negative")
        self.assertEqual(result["emotion"], "Disappointed")
        self.assertIn("apologize", result["reply_1"].lower())


from django.contrib import admin
from reviews.admin import FeedbackAdmin

class AdminActionTests(TestCase):
    def setUp(self):
        self.cafe = Cafe.objects.create(
            name="Action Cafe",
            slug="action-cafe",
            google_review_link="https://google.com/review"
        )
        self.feedback_1 = Feedback.objects.create(
            cafe=self.cafe,
            rating=1,
            issue="Service",
            comment="Terrible delay."
        )
        self.feedback_2 = Feedback.objects.create(
            cafe=self.cafe,
            rating=5,  # positive - should be skipped
            comment="Awesome!"
        )
        self.model_admin = FeedbackAdmin(Feedback, admin.site)

    @patch('reviews.admin.FeedbackAdmin.message_user')
    @patch('reviews.services.ai_review_analysis.os.getenv')
    def test_regenerate_ai_replies_action(self, mock_getenv, mock_message):
        """Verify that the custom admin action successfully analyzes low rating entries and skips positive ones."""
        mock_getenv.return_value = None  # force fallback to avoid calling API
        
        # Instantiate queryset containing both entries
        queryset = Feedback.objects.all()
        
        # Call action
        self.model_admin.regenerate_ai_replies(None, queryset)
        
        # Refresh from db
        self.feedback_1.refresh_from_db()
        self.feedback_2.refresh_from_db()
        
        # Feedback 1 (low rating) should have AI fields populated
        self.assertEqual(self.feedback_1.ai_sentiment, "Negative")
        self.assertEqual(self.feedback_1.ai_emotion, "Disappointed")
        
        # Feedback 2 (high rating) should NOT have AI fields populated
        self.assertIsNone(self.feedback_2.ai_sentiment)
        
        # Verify action output messages were sent
        mock_message.assert_called_once()


