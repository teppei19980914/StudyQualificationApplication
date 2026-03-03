"""データエクスポート/インポートサービス."""

from __future__ import annotations

import json
import logging
import zipfile
from pathlib import Path


logger = logging.getLogger(__name__)

# エクスポート対象のJSONファイル名
_DATA_FILES = [
    "goals.json",
    "tasks.json",
    "study_logs.json",
    "books.json",
    "notifications.json",
    "settings.json",
]

# 全データ削除対象のJSONファイル名（settings.jsonは保持）
_CLEARABLE_FILES = [
    "goals.json",
    "tasks.json",
    "study_logs.json",
    "books.json",
    "notifications.json",
]


class DataExportService:
    """データのエクスポートとインポートを行うサービス.

    Attributes:
        _data_dir: データディレクトリのパス.
    """

    def __init__(self, data_dir: Path) -> None:
        """DataExportServiceを初期化する.

        Args:
            data_dir: データディレクトリのパス.
        """
        self._data_dir = data_dir

    @property
    def data_dir(self) -> Path:
        """データディレクトリのパスを返す.

        Returns:
            データディレクトリのパス.
        """
        return self._data_dir

    def get_exportable_files(self) -> list[Path]:
        """エクスポート対象の既存ファイルリストを取得する.

        Returns:
            存在するデータファイルのパスリスト.
        """
        result: list[Path] = []
        for name in _DATA_FILES:
            path = self._data_dir / name
            if path.exists():
                result.append(path)
        return result

    def export_data(self, output_path: Path) -> int:
        """データファイルをZIPにエクスポートする.

        Args:
            output_path: 出力先ZIPファイルパス.

        Returns:
            エクスポートしたファイル数.

        Raises:
            OSError: ファイル操作に失敗した場合.
        """
        files = self.get_exportable_files()
        if not files:
            logger.warning("No data files found to export")
            return 0

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for file_path in files:
                zf.write(file_path, file_path.name)
                logger.debug(f"Added to archive: {file_path.name}")

        logger.info(f"Exported {len(files)} files to {output_path}")
        return len(files)

    def import_data(self, zip_path: Path) -> int:
        """ZIPファイルからデータをインポートする.

        Args:
            zip_path: インポート元ZIPファイルパス.

        Returns:
            インポートしたファイル数.

        Raises:
            FileNotFoundError: ZIPファイルが存在しない場合.
            zipfile.BadZipFile: 不正なZIPファイルの場合.
            ValueError: ZIPに有効なデータファイルが含まれない場合.
        """
        if not zip_path.exists():
            raise FileNotFoundError(f"File not found: {zip_path}")

        with zipfile.ZipFile(zip_path, "r") as zf:
            valid_names = [name for name in zf.namelist() if name in _DATA_FILES]
            if not valid_names:
                raise ValueError(
                    "ZIPファイルに有効なデータファイルが含まれていません。"
                )

            for name in valid_names:
                data = zf.read(name)
                try:
                    json.loads(data.decode("utf-8"))
                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    raise ValueError(f"不正なJSONファイル: {name} ({e})") from e

            self._data_dir.mkdir(parents=True, exist_ok=True)
            for name in valid_names:
                target = self._data_dir / name
                data = zf.read(name)
                target.write_bytes(data)
                logger.debug(f"Imported: {name}")

        logger.info(f"Imported {len(valid_names)} files from {zip_path}")
        return len(valid_names)

    def validate_zip(self, zip_path: Path) -> list[str]:
        """ZIPファイルの内容を検証し、含まれるデータファイル名を返す.

        Args:
            zip_path: 検証するZIPファイルパス.

        Returns:
            有効なデータファイル名のリスト.

        Raises:
            FileNotFoundError: ZIPファイルが存在しない場合.
            zipfile.BadZipFile: 不正なZIPファイルの場合.
        """
        if not zip_path.exists():
            raise FileNotFoundError(f"File not found: {zip_path}")

        with zipfile.ZipFile(zip_path, "r") as zf:
            return [name for name in zf.namelist() if name in _DATA_FILES]

    def clear_all_data(self) -> int:
        """全データファイルを削除する.

        設定ファイル(settings.json)は保持し、
        目標・タスク・学習ログ・書籍・通知のデータを削除する。

        Returns:
            削除したファイル数.
        """
        deleted = 0
        for name in _CLEARABLE_FILES:
            path = self._data_dir / name
            if path.exists():
                path.unlink()
                logger.debug(f"Deleted: {name}")
                deleted += 1

        logger.info(f"Cleared {deleted} data files")
        return deleted
