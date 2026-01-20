"""
Integration Tests for Routes

Tests the Flask blueprints and route handlers to ensure proper HTTP
responses and template rendering.
"""

import pytest


class TestMainRoutes:
    """Test main blueprint routes."""

    def test_homepage_loads(self, client):
        """Test: Homepage returns 200 OK."""
        response = client.get('/')
        assert response.status_code == 200

    def test_homepage_contains_title(self, client):
        """Test: Homepage contains site title."""
        response = client.get('/')
        assert b"Newton's Repository" in response.data

    def test_about_page_loads(self, client):
        """Test: About page returns 200 OK."""
        response = client.get('/about')
        assert response.status_code == 200

    def test_404_page(self, client):
        """Test: Non-existent page returns 404."""
        response = client.get('/nonexistent-page')
        assert response.status_code == 404


class TestBlogRoutes:
    """Test blog blueprint routes."""

    def test_blog_home_loads(self, client):
        """Test: Blog home page returns 200 OK."""
        response = client.get('/blog')
        assert response.status_code == 200

    def test_blog_home_shows_categories(self, client):
        """Test: Blog home shows category information."""
        response = client.get('/blog')
        assert b'Morecambe' in response.data or b'Blog' in response.data

    def test_blog_category_loads(self, client):
        """Test: Blog category page returns 200 OK."""
        response = client.get('/blog/morecambe-fm26')
        assert response.status_code == 200

    def test_invalid_category_404(self, client):
        """Test: Invalid category returns 404."""
        response = client.get('/blog/nonexistent-category')
        assert response.status_code == 404

    def test_article_page_loads(self, client):
        """Test: Article page returns 200 OK."""
        response = client.get('/blog/morecambe-fm26/the-journey-begins')
        assert response.status_code == 200

    def test_invalid_article_404(self, client):
        """Test: Invalid article returns 404."""
        response = client.get('/blog/morecambe-fm26/nonexistent-article')
        assert response.status_code == 404

    def test_legacy_redirect(self, client):
        """Test: Legacy article URL redirects to new URL."""
        response = client.get('/blog/article/the-journey-begins', follow_redirects=False)
        assert response.status_code == 302  # Redirect


class TestProjectsRoutes:
    """Test projects blueprint routes."""

    def test_projects_home_loads(self, client):
        """Test: Projects page returns 200 OK."""
        response = client.get('/projects')
        assert response.status_code == 200

    def test_projects_shows_capacity_tracker(self, client):
        """Test: Projects page mentions capacity tracker."""
        response = client.get('/projects')
        assert b'Capacity Tracker' in response.data or b'Recruitment' in response.data

    def test_capacity_tracker_get(self, client):
        """Test: Capacity tracker form loads."""
        response = client.get('/projects/capacity-tracker')
        assert response.status_code == 200

    def test_capacity_tracker_post_empty(self, client):
        """Test: Empty POST returns form (no errors)."""
        response = client.post('/projects/capacity-tracker', data={})
        assert response.status_code == 200

    def test_template_download(self, client):
        """Test: Excel template download works."""
        response = client.get('/projects/capacity-tracker/download-template')
        assert response.status_code == 200
        assert response.content_type == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'


class TestBlueprintEndpoints:
    """Test that blueprint endpoints are properly registered."""

    def test_main_blueprint_registered(self, app):
        """Test: main blueprint is registered."""
        assert 'main.home' in [rule.endpoint for rule in app.url_map.iter_rules()]
        assert 'main.about' in [rule.endpoint for rule in app.url_map.iter_rules()]

    def test_blog_blueprint_registered(self, app):
        """Test: blog blueprint is registered with /blog prefix."""
        endpoints = [rule.endpoint for rule in app.url_map.iter_rules()]
        assert 'blog.blog_home' in endpoints
        assert 'blog.blog_category' in endpoints
        assert 'blog.article' in endpoints

    def test_projects_blueprint_registered(self, app):
        """Test: projects blueprint is registered with /projects prefix."""
        endpoints = [rule.endpoint for rule in app.url_map.iter_rules()]
        assert 'projects.projects_home' in endpoints
        assert 'projects.capacity_tracker' in endpoints
        assert 'projects.download_capacity_template' in endpoints


class TestURLBuilding:
    """Test Flask url_for with blueprints."""

    def test_url_for_main_home(self, app):
        """Test: url_for works with main.home."""
        with app.test_request_context():
            from flask import url_for
            url = url_for('main.home')
            assert url == '/'

    def test_url_for_blog_home(self, app):
        """Test: url_for works with blog.blog_home."""
        with app.test_request_context():
            from flask import url_for
            url = url_for('blog.blog_home')
            assert url == '/blog'

    def test_url_for_blog_category(self, app):
        """Test: url_for works with blog.blog_category."""
        with app.test_request_context():
            from flask import url_for
            url = url_for('blog.blog_category', category_id='test')
            assert url == '/blog/test'

    def test_url_for_projects(self, app):
        """Test: url_for works with projects.projects_home."""
        with app.test_request_context():
            from flask import url_for
            url = url_for('projects.projects_home')
            assert url == '/projects'


class TestResponseHeaders:
    """Test HTTP response headers."""

    def test_content_type_html(self, client):
        """Test: HTML pages return correct content type."""
        response = client.get('/')
        assert 'text/html' in response.content_type

    def test_charset_utf8(self, client):
        """Test: Responses use UTF-8 encoding."""
        response = client.get('/')
        assert 'charset=utf-8' in response.content_type.lower()
