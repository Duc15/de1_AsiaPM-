"""Thế giới (World) dùng chung cho mọi bước Gherkin.

Giữ ngữ cảnh giữa Cho/Khi/Thì, và là chỗ duy nhất biết đường tới lớp đối tượng.
Khi bài 2 (web) và mobile vào, chúng thay `doi_tuong` bằng lớp của mình mà không
đụng tới bước Gherkin.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

GOC = Path(__file__).resolve().parents[2]


@dataclass
class TheGioi:
    doi_tuong: Any = None
    ket_qua: Any = None
    du_lieu: dict = field(default_factory=dict)

    def dat(self, khoa: str, gia_tri: Any) -> None:
        self.du_lieu[khoa] = gia_tri

    def lay(self, khoa: str, mac_dinh: Any = None) -> Any:
        return self.du_lieu.get(khoa, mac_dinh)


def doc_so_gioi_han() -> dict:
    tep = GOC / "gioi_han" / "so_gioi_han.json"
    return json.loads(tep.read_text(encoding="utf-8"))


def doc_cham_diem(ten_model: str = "tesseract") -> dict:
    tep = GOC / "ket_qua" / ten_model / "cham_diem.json"
    if not tep.exists():
        raise FileNotFoundError(
            f"chưa có {tep} — chạy `python scripts/do_luong.py` trước")
    return json.loads(tep.read_text(encoding="utf-8"))
