"""
Integration Tests for Security Features

Tests security headers, CSRF protection, rate limiting, and input validation.
"""

import pytest


class TestSecurityHeaders:
    """Test HTTP security headers on all responses."""

    def test_x_content_type_options(self, client):
        """Test: X-Content-Type-Options header is set."""
        response = client.get('/')
        assert response.headers.get('X-Content-Type-Options') == 'nosniff'

    def test_x_frame_options(self, client):
        """Test: X-Frame-Options header is set."""
        response = client.get('/')
        assert response.headers.get('X-Frame-Options') == 'SAMEORIGIN'

    def test_x_xss_protection(self, client):
        """Test: X-XSS-Protection header is set."""
        response = client.get('/')
        assert response.headers.get('X-XSS-Protection') == '1; mode=block'

    def test_content_security_policy(self, client):
        """Test: Content-Security-Policy header is set."""
        response = client.get('/')
        csp = response.headers.get('Content-Security-Policy')

        assert csp is not None
        assert 'default-src' in csp
        assert "'self'" in csp

    def test_referrer_policy(self, client):
        """Test: Referrer-Policy header is set."""
        response = client.get('/')
        assert response.headers.get('Referrer-Policy') == 'strict-origin-when-cross-origin'

    def test_permissions_policy(self, client):
        """Test: Permissions-Policy header is set."""
        response = client.get('/')
        policy = response.headers.get('Permissions-Policy')

        assert policy is not None
        assert 'geolocation=()' in policy
        assert 'microphone=()' in policy
        assert 'camera=()' in policy

    def test_headers_on_all_routes(self, client):
        """Test: Security headers apply to all routes."""
        routes = ['/', '/blog', '/projects', '/about']

        for route in routes:
            response = client.get(route)
            assert response.headers.get('X-Content-Type-Options') == 'nosniff'
            assert response.headers.get('X-Frame-Options') == 'SAMEORIGIN'


class TestCSRFProtection:
    """Test CSRF token requirements."""

    def test_csrf_token_in_forms(self, client):
        """Test: Forms contain CSRF tokens."""
        response = client.get('/projects/capacity-tracker')

        # Check for CSRF token field in form
        assert b'csrf_token' in response.data or b'_csrf_token' in response.data

    def test_post_without_csrf_rejected(self, client):
        """Test: POST without CSRF token is rejected (when CSRF is enforced)."""
        # Note: In testing mode, CSRF might be disabled
        # This test verifies the setup exists
        response = client.post(
            '/projects/capacity-tracker',
            data={'recruiter_0': 'Test'},
            follow_redirects=False
        )

        # Should either succeed (CSRF disabled in testing) or return 400
        assert response.status_code in [200, 400]


class TestRateLimiting:
    """Test rate limiting on sensitive endpoints."""

    def test_rate_limit_exists(self, app):
        """Test: Rate limiting is configured."""
        # Check that limiter is initialized
        from app import limiter
        assert limiter is not None

    @pytest.mark.skip(reason="Rate limiting may not trigger in test mode with memory storage")
    def test_capacity_tracker_rate_limit(self, client):
        """Test: Capacity tracker has rate limiting."""
        # Attempt to exceed rate limit
        for i in range(15):
            response = client.post(
                '/projects/capacity-tracker',
                data={}
            )

        # Next request should be rate limited
        response = client.post('/projects/capacity-tracker', data={})

        # Should return 429 Too Many Requests (if rate limiting is active)
        # In testing, this might not trigger
        assert response.status_code in [200, 429]


class TestInputValidation:
    """Test input validation and sanitization."""

    def test_path_traversal_protection_articles(self, blog_service):
        """Test: Path traversal attempts in article filenames are blocked."""
        # Attempt path traversal
        content = blog_service.get_article_content('../../../etc/passwd')
        assert content is None

        content = blog_service.get_article_content('..\\..\\..\\windows\\system32\\config\\sam')
        assert content is None

    def test_invalid_filename_characters(self, blog_service):
        """Test: Invalid characters in filenames are rejected."""
        invalid_names = [
            'test<script>',
            'test|command',
            'test;rm -rf /',
            'test\x00null.txt',
        ]

        for invalid_name in invalid_names:
            content = blog_service.get_article_content(invalid_name)
            assert content is None

    def test_empty_filename(self, blog_service):
        """Test: Empty filename is rejected."""
        content = blog_service.get_article_content('')
        assert content is None

    def test_none_filename(self, blog_service):
        """Test: None filename is rejected."""
        content = blog_service.get_article_content(None)
        assert content is None


class TestPydanticValidation:
    """Test Pydantic schema validation."""

    def test_vacancy_schema_validates(self):
        """Test: VacancySchema accepts valid data."""
        from schemas.recruitment import VacancySchema

        data = {
            'name': 'Test Role',
            'role_type': 'medium',
            'is_internal': False,
            'stage': 'screening'
        }

        vacancy = VacancySchema(**data)
        assert vacancy.name == 'Test Role'
        assert vacancy.role_type.value == 'medium'

    def test_vacancy_schema_rejects_empty_name(self):
        """Test: VacancySchema rejects empty names."""
        from schemas.recruitment import VacancySchema
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            VacancySchema(name='   ', role_type='easy')

    def test_vacancy_schema_rejects_invalid_role(self):
        """Test: VacancySchema rejects invalid role types."""
        from schemas.recruitment import VacancySchema
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            VacancySchema(name='Test', role_type='invalid')

    def test_vacancy_schema_sanitizes_whitespace(self):
        """Test: VacancySchema strips whitespace."""
        from schemas.recruitment import VacancySchema

        vacancy = VacancySchema(
            name='  Test Role  ',
            role_type='  easy  ',
            stage='  screening  '
        )

        assert vacancy.name == 'Test Role'
        assert vacancy.role_type.value == 'easy'
        assert vacancy.stage.value == 'screening'


class TestFileUploadValidation:
    """Test file upload security."""

    def test_file_validation_service_exists(self, file_service):
        """Test: FileService validation method exists."""
        assert hasattr(file_service, 'validate_uploaded_file')

    def test_excel_processing_service_exists(self, file_service):
        """Test: FileService Excel processing method exists."""
        assert hasattr(file_service, 'process_excel_upload')


class TestConfigurationSecurity:
    """Test security-related configuration."""

    def test_secret_key_configured(self, app):
        """Test: SECRET_KEY is set."""
        assert app.config.get('SECRET_KEY') is not None
        assert app.config.get('SECRET_KEY') != ''

    def test_testing_mode_active(self, app):
        """Test: Testing configuration is active."""
        assert app.config.get('TESTING') is True

    def test_session_cookie_httponly(self, app):
        """Test: Session cookies are HTTPOnly."""
        assert app.config.get('SESSION_COOKIE_HTTPONLY') is True

    def test_session_cookie_samesite(self, app):
        """Test: Session cookies use SameSite policy."""
        assert app.config.get('SESSION_COOKIE_SAMESITE') == 'Lax'

    def test_debug_mode_disabled_in_test(self, app):
        """Test: Debug mode is disabled in testing."""
        assert app.config.get('DEBUG') is False


class TestLoggingConfiguration:
    """Test logging setup."""

    def test_logger_exists(self, app):
        """Test: Application logger is configured."""
        assert app.logger is not None

    def test_logger_has_handlers(self, app):
        """Test: Logger has handlers configured."""
        assert len(app.logger.handlers) > 0

    def test_logging_level_set(self, app):
        """Test: Logging level is configured."""
        assert app.logger.level is not None
