"""Tests for EOL database and lookup."""

import pytest
from src.eol import EOL_DATABASE, lookup_eol


class TestEOL:
    def test_database_has_entries(self):
        assert len(EOL_DATABASE) > 0

    def test_all_entries_have_required_keys(self):
        required = {"eol", "status", "note"}
        for key, value in EOL_DATABASE.items():
            assert required.issubset(value.keys()), f"{key} missing keys"

    def test_lookup_by_hostname(self):
        result = lookup_eol(hostname="core-asa5516-x")
        assert result["status"] in ("EOSL", "End-of-Sale", "Актуальное", "Требуется проверка")

    def test_lookup_by_model(self):
        result = lookup_eol(model="Cisco ASA 5516-X")
        assert result["status"] == "End-of-Sale"

    def test_lookup_no_match(self):
        result = lookup_eol(hostname="nonexistent-router")
        assert result["status"] == "Требуется проверка"
