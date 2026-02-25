"""JsonStorageのテスト."""

import json
from pathlib import Path

import pytest

from study_python.repositories.json_storage import JsonStorage


@pytest.fixture
def storage(tmp_path: Path) -> JsonStorage:
    return JsonStorage(tmp_path / "test.json")


class TestJsonStorageLoad:
    """loadメソッドのテスト."""

    def test_load_nonexistent_file_returns_empty(self, storage):
        assert storage.load() == []

    def test_load_existing_file(self, storage):
        data = [{"id": "1", "name": "test"}]
        storage.file_path.write_text(
            json.dumps(data, ensure_ascii=False), encoding="utf-8"
        )
        result = storage.load()
        assert result == data

    def test_load_empty_json_array(self, storage):
        storage.file_path.write_text("[]", encoding="utf-8")
        assert storage.load() == []

    def test_load_invalid_json_returns_empty(self, storage):
        storage.file_path.write_text("invalid json", encoding="utf-8")
        assert storage.load() == []

    def test_load_multiple_items(self, storage):
        data = [{"id": "1"}, {"id": "2"}, {"id": "3"}]
        storage.file_path.write_text(
            json.dumps(data, ensure_ascii=False), encoding="utf-8"
        )
        result = storage.load()
        assert len(result) == 3


class TestJsonStorageSave:
    """saveメソッドのテスト."""

    def test_save_creates_file(self, storage):
        storage.save([{"id": "1"}])
        assert storage.file_path.exists()

    def test_save_creates_parent_directories(self, tmp_path):
        deep_path = tmp_path / "a" / "b" / "c" / "test.json"
        storage = JsonStorage(deep_path)
        storage.save([{"id": "1"}])
        assert deep_path.exists()

    def test_save_and_load_roundtrip(self, storage):
        data = [
            {"id": "1", "name": "テスト1"},
            {"id": "2", "name": "テスト2"},
        ]
        storage.save(data)
        loaded = storage.load()
        assert loaded == data

    def test_save_overwrites_existing(self, storage):
        storage.save([{"id": "1"}])
        storage.save([{"id": "2"}])
        loaded = storage.load()
        assert len(loaded) == 1
        assert loaded[0]["id"] == "2"

    def test_save_empty_list(self, storage):
        storage.save([])
        loaded = storage.load()
        assert loaded == []

    def test_save_japanese_text(self, storage):
        data = [{"name": "日本語テスト", "desc": "これはテストです"}]
        storage.save(data)
        loaded = storage.load()
        assert loaded[0]["name"] == "日本語テスト"
