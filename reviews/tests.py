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
