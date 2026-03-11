"""Tests for Flask web routes and API endpoints."""


class TestWebRoutes:
    """Tests for the web UI routes."""

    def test_home_page(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert b"OCR" in response.data

    def test_about_page(self, client):
        response = client.get("/about/")
        assert response.status_code == 200
        assert b"About" in response.data


class TestAPIRoutes:
    """Tests for the REST API routes."""

    def test_api_get_info(self, client):
        response = client.get("/api/v1/")
        assert response.status_code == 200
        data = response.get_json()
        assert "service" in data
        assert "version" in data
        assert "supported_languages" in data

    def test_api_post_no_file(self, client):
        response = client.post("/api/v1/")
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
