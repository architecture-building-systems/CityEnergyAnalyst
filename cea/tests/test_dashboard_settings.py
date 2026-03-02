"""Tests for CORS validation in cea.interfaces.dashboard.settings.Settings"""

import pytest
from unittest.mock import patch
from pydantic import ValidationError

from cea.interfaces.dashboard.settings import Settings


def make_settings(**kwargs):
    """Create a Settings instance with non-CORS validators patched out."""
    with patch.object(Settings, "validate_non_local_mode", lambda self: self), \
         patch.object(Settings, "validate_multi_worker_mode", lambda self: self):
        return Settings(**kwargs)


class TestWildcardOrigin:
    def test_wildcard_allowed_in_local_mode(self):
        s = make_settings(local=True, cors_origin="*")
        assert s.cors_origin == "*"

    def test_wildcard_with_whitespace_treated_as_wildcard_local(self):
        # " * " should normalise to "*" and pass in local mode
        make_settings(local=True, cors_origin=" * ")

    def test_wildcard_rejected_in_non_local_mode(self):
        with pytest.raises(ValidationError, match="not allowed in non-local mode"):
            make_settings(local=False, cors_origin="*")

    def test_wildcard_with_whitespace_rejected_in_non_local_mode(self):
        with pytest.raises(ValidationError, match="not allowed in non-local mode"):
            make_settings(local=False, cors_origin=" * ")


class TestValidSingleOrigins:
    def test_http_hostname_only(self):
        make_settings(cors_origin="http://localhost")

    def test_https_hostname_only(self):
        make_settings(cors_origin="https://example.com")

    def test_http_with_port(self):
        make_settings(cors_origin="http://localhost:5050")

    def test_https_with_port(self):
        make_settings(cors_origin="https://example.com:8443")

    def test_subdomain_with_port(self):
        make_settings(cors_origin="https://app.example.com:3000")


class TestPortGroupRegression:
    """Regression: ':' was inside the hostname char-class, letting the hostname
    consume the port separator and breaking port-only validation."""

    def test_non_numeric_port_rejected(self):
        with pytest.raises(ValidationError, match="Invalid CORS origin format"):
            make_settings(cors_origin="http://localhost:abc")

    def test_port_with_letters_rejected(self):
        with pytest.raises(ValidationError, match="Invalid CORS origin format"):
            make_settings(cors_origin="http://localhost:PORT")


class TestMultipleOrigins:
    def test_comma_separated_valid_origins(self):
        make_settings(cors_origin="http://localhost:3000,https://example.com")

    def test_whitespace_around_commas_stripped(self):
        make_settings(cors_origin=" http://localhost:3000 , https://example.com ")

    def test_one_invalid_origin_in_list_raises(self):
        with pytest.raises(ValidationError, match="Invalid CORS origin format"):
            make_settings(cors_origin="http://localhost:3000,not-a-url")


class TestInvalidFormats:
    def test_missing_scheme_rejected(self):
        with pytest.raises(ValidationError):
            make_settings(cors_origin="localhost:3000")

    def test_ftp_scheme_rejected(self):
        with pytest.raises(ValidationError):
            make_settings(cors_origin="ftp://localhost:3000")

    def test_bare_string_rejected(self):
        with pytest.raises(ValidationError):
            make_settings(cors_origin="not-an-origin")

    def test_trailing_slash_rejected(self):
        with pytest.raises(ValidationError):
            make_settings(cors_origin="http://localhost:3000/")

    def test_path_component_rejected(self):
        with pytest.raises(ValidationError):
            make_settings(cors_origin="http://localhost:3000/path")
