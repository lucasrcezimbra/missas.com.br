"""Test ALLOWED_HOSTS configuration for Render preview deployments."""

from django.test import TestCase


class AllowedHostsTest(TestCase):
    """Test that ALLOWED_HOSTS correctly handles Render preview deployments."""

    def test_custom_allowed_hosts_class_functionality(self):
        """Test the CustomAllowedHosts class functionality directly."""
        # Import and test the class directly

        from missas.settings import CustomAllowedHosts

        # Create an instance with test base hosts
        base_hosts = ["example.com", "www.example.com"]
        custom_hosts = CustomAllowedHosts(base_hosts)

        # Test base hosts
        self.assertIn("example.com", custom_hosts)
        self.assertIn("www.example.com", custom_hosts)

        # Test preview deployment hosts
        preview_hosts = [
            "missas-pr-1.onrender.com",
            "missas-pr-42.onrender.com",
            "missas-pr-185.onrender.com",
            "missas-pr-999.onrender.com",
        ]

        for host in preview_hosts:
            with self.subTest(host=host):
                self.assertIn(host, custom_hosts)

        # Test invalid hosts
        invalid_hosts = [
            "example.net",
            "missas-pr-abc.onrender.com",  # Non-numeric
            "missas-pr-.onrender.com",  # Empty number
            "missas-pr-123.example.com",  # Wrong domain
            "evil.com",
        ]

        for host in invalid_hosts:
            with self.subTest(host=host):
                self.assertNotIn(host, custom_hosts)

    def test_custom_allowed_hosts_is_list_compatible(self):
        """Test that CustomAllowedHosts is compatible with Django's expectations."""
        from missas.settings import CustomAllowedHosts

        base_hosts = ["example.com"]
        custom_hosts = CustomAllowedHosts(base_hosts)

        # Test that it's list-like
        self.assertTrue(hasattr(custom_hosts, "__iter__"))
        self.assertTrue(hasattr(custom_hosts, "__contains__"))
        self.assertIsInstance(custom_hosts, list)

        # Test that we can iterate over it
        host_list = list(custom_hosts)
        self.assertEqual(host_list, base_hosts)

    def test_preview_pattern_regex(self):
        """Test the regex pattern used for preview deployments."""
        import re

        # This is the pattern used in the code
        pattern = re.compile(r"^missas-pr-\d+\.onrender\.com$")

        # Valid patterns
        valid_hosts = [
            "missas-pr-1.onrender.com",
            "missas-pr-185.onrender.com",
            "missas-pr-999.onrender.com",
        ]

        for host in valid_hosts:
            with self.subTest(host=host):
                self.assertTrue(pattern.match(host))

        # Invalid patterns
        invalid_hosts = [
            "missas-pr-abc.onrender.com",  # Non-numeric
            "missas-pr-.onrender.com",  # Empty number
            "missas-pr-123.example.com",  # Wrong domain
            "missas-123.onrender.com",  # Missing 'pr-'
        ]

        for host in invalid_hosts:
            with self.subTest(host=host):
                self.assertFalse(pattern.match(host))
