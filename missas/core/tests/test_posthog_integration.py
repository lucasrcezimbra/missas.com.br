from django.test import TestCase


class PosthogIntegrationTest(TestCase):
    def test_posthog_script_included_in_homepage(self):
        """Test that PostHog analytics script is included in the homepage."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

        # Check that PostHog initialization script is present
        self.assertContains(response, "posthog.init")
        self.assertContains(response, "phc_D2o38Ed19YLVZLhRKvKU0Gj5B5dsDLXohBipBUOOlW4")
        self.assertContains(response, "https://us.i.posthog.com")

    def test_posthog_script_included_in_all_pages(self):
        """Test that PostHog script is included in other pages that extend base.html."""
        # Test state page (if it exists)
        response = self.client.get("/rio-grande-do-norte/")
        if response.status_code == 200:
            self.assertContains(response, "posthog.init")
