"""DataExportServiceのテスト."""

import json
import zipfile
from pathlib import Path

import pytest

from study_python.services.data_export_service import DataExportService


class TestDataExportService:
    """DataExportServiceのテスト."""

    def test_data_dir_property(self, tmp_path: Path):
        """data_dirプロパティが正しい値を返す."""
        service = DataExportService(tmp_path)
        assert service.data_dir == tmp_path

    def test_get_exportable_files_empty(self, tmp_path: Path):
        """空ディレクトリではファイルなし."""
        service = DataExportService(tmp_path)
        assert service.get_exportable_files() == []

    def test_get_exportable_files_with_data(self, tmp_path: Path):
        """データファイルがある場合はリストに含まれる."""
        (tmp_path / "goals.json").write_text("[]", encoding="utf-8")
        (tmp_path / "tasks.json").write_text("[]", encoding="utf-8")
        service = DataExportService(tmp_path)
        files = service.get_exportable_files()
        assert len(files) == 2
        names = {f.name for f in files}
        assert names == {"goals.json", "tasks.json"}

    def test_get_exportable_files_ignores_unknown(self, tmp_path: Path):
        """対象外ファイルは含まれない."""
        (tmp_path / "goals.json").write_text("[]", encoding="utf-8")
        (tmp_path / "other.txt").write_text("hello", encoding="utf-8")
        service = DataExportService(tmp_path)
        files = service.get_exportable_files()
        assert len(files) == 1
        assert files[0].name == "goals.json"

    def test_export_data_creates_zip(self, tmp_path: Path):
        """エクスポートでZIPが作成される."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "goals.json").write_text('[{"id": "1"}]', encoding="utf-8")
        (data_dir / "tasks.json").write_text("[]", encoding="utf-8")

        service = DataExportService(data_dir)
        output = tmp_path / "backup.zip"
        count = service.export_data(output)

        assert count == 2
        assert output.exists()

    def test_export_data_zip_contents(self, tmp_path: Path):
        """ZIPに正しいファイルが含まれる."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "goals.json").write_text('[{"id": "1"}]', encoding="utf-8")

        service = DataExportService(data_dir)
        output = tmp_path / "backup.zip"
        service.export_data(output)

        with zipfile.ZipFile(output, "r") as zf:
            assert "goals.json" in zf.namelist()
            content = json.loads(zf.read("goals.json").decode("utf-8"))
            assert content == [{"id": "1"}]

    def test_export_data_empty_returns_zero(self, tmp_path: Path):
        """データなしではエクスポート数0."""
        service = DataExportService(tmp_path)
        output = tmp_path / "backup.zip"
        count = service.export_data(output)
        assert count == 0
        assert not output.exists()

    def test_export_data_creates_parent_dir(self, tmp_path: Path):
        """出力先の親ディレクトリが自動作成される."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "goals.json").write_text("[]", encoding="utf-8")

        service = DataExportService(data_dir)
        output = tmp_path / "subdir" / "backup.zip"
        count = service.export_data(output)

        assert count == 1
        assert output.exists()

    def test_import_data_restores_files(self, tmp_path: Path):
        """インポートでファイルが復元される."""
        # ZIP作成
        zip_path = tmp_path / "backup.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("goals.json", '[{"id": "test"}]')
            zf.writestr("tasks.json", "[]")

        target_dir = tmp_path / "restored"
        service = DataExportService(target_dir)
        count = service.import_data(zip_path)

        assert count == 2
        assert (target_dir / "goals.json").exists()
        content = json.loads((target_dir / "goals.json").read_text(encoding="utf-8"))
        assert content == [{"id": "test"}]

    def test_import_data_file_not_found(self, tmp_path: Path):
        """存在しないZIPでFileNotFoundError."""
        service = DataExportService(tmp_path)
        with pytest.raises(FileNotFoundError):
            service.import_data(tmp_path / "nonexistent.zip")

    def test_import_data_bad_zip(self, tmp_path: Path):
        """不正ZIPでBadZipFile."""
        bad_zip = tmp_path / "bad.zip"
        bad_zip.write_text("not a zip", encoding="utf-8")
        service = DataExportService(tmp_path)
        with pytest.raises(zipfile.BadZipFile):
            service.import_data(bad_zip)

    def test_import_data_no_valid_files(self, tmp_path: Path):
        """有効ファイルなしでValueError."""
        zip_path = tmp_path / "empty.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("readme.txt", "hello")

        service = DataExportService(tmp_path)
        with pytest.raises(ValueError, match="有効なデータファイル"):
            service.import_data(zip_path)

    def test_import_data_invalid_json(self, tmp_path: Path):
        """不正JSONでValueError."""
        zip_path = tmp_path / "invalid.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("goals.json", "not json!!!")

        service = DataExportService(tmp_path / "target")
        with pytest.raises(ValueError, match="不正なJSON"):
            service.import_data(zip_path)

    def test_import_data_creates_target_dir(self, tmp_path: Path):
        """インポート先ディレクトリが自動作成される."""
        zip_path = tmp_path / "backup.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("goals.json", "[]")

        target_dir = tmp_path / "new_dir"
        service = DataExportService(target_dir)
        service.import_data(zip_path)
        assert target_dir.exists()

    def test_validate_zip_returns_valid_names(self, tmp_path: Path):
        """validate_zipが有効ファイル名を返す."""
        zip_path = tmp_path / "backup.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("goals.json", "[]")
            zf.writestr("tasks.json", "[]")
            zf.writestr("readme.txt", "hello")

        service = DataExportService(tmp_path)
        valid = service.validate_zip(zip_path)
        assert set(valid) == {"goals.json", "tasks.json"}

    def test_validate_zip_file_not_found(self, tmp_path: Path):
        """存在しないZIPでFileNotFoundError."""
        service = DataExportService(tmp_path)
        with pytest.raises(FileNotFoundError):
            service.validate_zip(tmp_path / "nonexistent.zip")

    def test_roundtrip_export_import(self, tmp_path: Path):
        """エクスポート→インポートでデータが一致する."""
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        original_data = [{"id": "g1", "name": "Goal 1"}]
        (source_dir / "goals.json").write_text(
            json.dumps(original_data, ensure_ascii=False), encoding="utf-8"
        )
        (source_dir / "settings.json").write_text('{"theme": "dark"}', encoding="utf-8")

        # エクスポート
        export_service = DataExportService(source_dir)
        zip_path = tmp_path / "backup.zip"
        export_service.export_data(zip_path)

        # 別ディレクトリにインポート
        target_dir = tmp_path / "target"
        import_service = DataExportService(target_dir)
        import_service.import_data(zip_path)

        # データ一致確認
        imported = json.loads((target_dir / "goals.json").read_text(encoding="utf-8"))
        assert imported == original_data
        settings = json.loads(
            (target_dir / "settings.json").read_text(encoding="utf-8")
        )
        assert settings == {"theme": "dark"}

    def test_import_only_valid_files(self, tmp_path: Path):
        """ZIPに無関係なファイルがあっても有効ファイルのみインポートされる."""
        zip_path = tmp_path / "mixed.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("goals.json", "[]")
            zf.writestr("readme.txt", "hello")
            zf.writestr("malicious.exe", "bad")

        target_dir = tmp_path / "target"
        service = DataExportService(target_dir)
        count = service.import_data(zip_path)

        assert count == 1
        assert (target_dir / "goals.json").exists()
        assert not (target_dir / "readme.txt").exists()
        assert not (target_dir / "malicious.exe").exists()


class TestClearAllData:
    """clear_all_dataのテスト."""

    def test_clear_deletes_data_files(self, tmp_path: Path):
        """データファイルが削除される."""
        (tmp_path / "goals.json").write_text("[]", encoding="utf-8")
        (tmp_path / "tasks.json").write_text("[]", encoding="utf-8")
        (tmp_path / "study_logs.json").write_text("[]", encoding="utf-8")
        (tmp_path / "books.json").write_text("[]", encoding="utf-8")
        (tmp_path / "notifications.json").write_text("[]", encoding="utf-8")

        service = DataExportService(tmp_path)
        count = service.clear_all_data()

        assert count == 5
        assert not (tmp_path / "goals.json").exists()
        assert not (tmp_path / "tasks.json").exists()
        assert not (tmp_path / "study_logs.json").exists()
        assert not (tmp_path / "books.json").exists()
        assert not (tmp_path / "notifications.json").exists()

    def test_clear_preserves_settings(self, tmp_path: Path):
        """settings.jsonは保持される."""
        (tmp_path / "goals.json").write_text("[]", encoding="utf-8")
        (tmp_path / "settings.json").write_text('{"theme": "dark"}', encoding="utf-8")

        service = DataExportService(tmp_path)
        service.clear_all_data()

        assert (tmp_path / "settings.json").exists()
        content = json.loads((tmp_path / "settings.json").read_text(encoding="utf-8"))
        assert content == {"theme": "dark"}

    def test_clear_empty_dir(self, tmp_path: Path):
        """空ディレクトリでは削除数0."""
        service = DataExportService(tmp_path)
        count = service.clear_all_data()
        assert count == 0

    def test_clear_partial_files(self, tmp_path: Path):
        """一部ファイルのみ存在する場合."""
        (tmp_path / "goals.json").write_text("[]", encoding="utf-8")
        (tmp_path / "books.json").write_text("[]", encoding="utf-8")

        service = DataExportService(tmp_path)
        count = service.clear_all_data()

        assert count == 2
        assert not (tmp_path / "goals.json").exists()
        assert not (tmp_path / "books.json").exists()

    def test_clear_ignores_unknown_files(self, tmp_path: Path):
        """対象外ファイルは削除されない."""
        (tmp_path / "goals.json").write_text("[]", encoding="utf-8")
        (tmp_path / "other.txt").write_text("keep me", encoding="utf-8")

        service = DataExportService(tmp_path)
        service.clear_all_data()

        assert (tmp_path / "other.txt").exists()
