"""Tests for SQLite database layer."""

import pytest
import os
from src.database import init_db, add_inventory, list_inventories, delete_inventory, find_inventory_by_model, save_audit_history, list_audit_history
from src.config import DB_PATH


@pytest.fixture(autouse=True)
def setup_db():
    if DB_PATH.exists():
        DB_PATH.unlink()
    init_db()
    yield
    if DB_PATH.exists():
        DB_PATH.unlink()


class TestDatabase:
    def test_add_and_list_inventory(self):
        pk = add_inventory("Test Switch", vendor="TestCorp", category="network", eol="2025", eol_status="Active")
        assert pk > 0
        items = list_inventories()
        assert len(items) >= 1
        assert any(i["model"] == "Test Switch" for i in items)

    def test_find_by_model(self):
        add_inventory("Cisco Catalyst 9300", vendor="Cisco")
        found = find_inventory_by_model("Cisco Catalyst 9300")
        assert found is not None
        assert found["vendor"] == "Cisco"

    def test_find_by_partial_model(self):
        add_inventory("Huawei S6730-H24X6C", vendor="Huawei")
        found = find_inventory_by_model("S6730")
        assert found is not None

    def test_delete_inventory(self):
        pk = add_inventory("ToDelete", vendor="Test")
        assert delete_inventory(pk) is True
        assert delete_inventory(99999) is False

    def test_list_by_category(self):
        add_inventory("Server", category="server")
        add_inventory("Switch", category="network")
        items = list_inventories(category="network")
        assert all(i["category"] == "network" for i in items)

    def test_audit_history(self):
        save_audit_history("test.md", "test prompt", devices_count=5, eol_critical=2)
        history = list_audit_history()
        assert len(history) >= 1
        assert history[0]["report_file"] == "test.md"
