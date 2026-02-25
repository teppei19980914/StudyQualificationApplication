"""汎用JSON永続化ストレージ."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any


logger = logging.getLogger(__name__)


class JsonStorage:
    """JSONファイルによるデータ永続化.

    Attributes:
        file_path: JSONファイルのパス.
    """

    def __init__(self, file_path: Path) -> None:
        """JsonStorageを初期化する.

        Args:
            file_path: JSONファイルのパス.
        """
        self.file_path = file_path

    def load(self) -> list[dict[str, Any]]:
        """JSONファイルからデータを読み込む.

        Returns:
            辞書のリスト。ファイルが存在しない場合は空リスト.
        """
        if not self.file_path.exists():
            logger.debug(f"File not found, returning empty list: {self.file_path}")
            return []
        try:
            text = self.file_path.read_text(encoding="utf-8")
            data: list[dict[str, Any]] = json.loads(text)
            logger.debug(f"Loaded {len(data)} items from {self.file_path}")
            return data
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to load JSON from {self.file_path}: {e}")
            return []

    def save(self, data: list[dict[str, Any]]) -> None:
        """データをJSONファイルに保存する.

        Args:
            data: 保存する辞書のリスト.
        """
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(data, ensure_ascii=False, indent=2)
        self.file_path.write_text(text, encoding="utf-8")
        logger.debug(f"Saved {len(data)} items to {self.file_path}")
