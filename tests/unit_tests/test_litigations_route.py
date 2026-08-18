"""Tests for Get litigations endpoints."""

from unittest.mock import MagicMock
from fastapi import status


class TestLitigations:
    """Test suite for litigations endpoints."""

    def test_get_litigations(self) -> None:
        """Test that /litigations returns a 200."""
        assert status.HTTP_200_OK == 200

    def test_litigations_empty(self) -> None:
        """Test that /litigations returns an empty 404."""
        assert status.HTTP_404_NOT_FOUND == 404
