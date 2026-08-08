"""Giao diện model. Bộ đo chỉ biết đúng lớp này, không biết Tesseract.

Đổi model = viết một lớp mới cài `trich_xuat()` rồi khai trong `DANH_MUC`.
Không sửa một dòng nào trong bo_do/cham_diem.py hay bo_do/so_khop.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class TruongTraVe:
    ten_truong: str
    gia_tri: str | None
    confidence: float | None
    nguon: str = "ocr"

    def to_dict(self) -> dict:
        return {"ten_truong": self.ten_truong, "gia_tri": self.gia_tri,
                "confidence": self.confidence, "nguon": self.nguon}


@dataclass
class KetQuaTrichXuat:
    """Đúng cấu trúc mục 03 của đề, cộng phần siêu dữ liệu để chẩn đoán.

    `loi_he_thong` là ranh giới quan trọng nhất trong file này: nó phân biệt
    "model không đọc được ảnh" (kết quả hợp lệ, tính vào điểm) với "chúng ta gọi
    model sai" (không tính vào điểm, phải đi sửa hạ tầng).
    """
    doc_type: str
    fields: list[TruongTraVe] = field(default_factory=list)
    thoi_gian_ms: float = 0.0
    loi_he_thong: str | None = None
    ly_do_tu_choi: str | None = None
    chan_doan: dict = field(default_factory=dict)

    def gia_tri(self, ten_truong: str) -> str | None:
        for f in self.fields:
            if f.ten_truong == ten_truong:
                return f.gia_tri
        return None

    def do_tin_cay(self, ten_truong: str) -> float | None:
        for f in self.fields:
            if f.ten_truong == ten_truong:
                return f.confidence
        return None

    def nguon(self, ten_truong: str) -> str | None:
        for f in self.fields:
            if f.ten_truong == ten_truong:
                return f.nguon
        return None

    def to_dict(self) -> dict:
        return {"doc_type": self.doc_type,
                "fields": [f.to_dict() for f in self.fields],
                "thoi_gian_ms": round(self.thoi_gian_ms, 1),
                "loi_he_thong": self.loi_he_thong,
                "ly_do_tu_choi": self.ly_do_tu_choi,
                "chan_doan": self.chan_doan}


class MoHinh(Protocol):
    ten: str
    phien_ban: str

    def trich_xuat(self, duong_dan_anh: str, ma_loai: str) -> KetQuaTrichXuat: ...

    def tu_kiem_tra(self) -> tuple[bool, str]:
        """Canary: chạy trước mỗi lượt đo để biết hạ tầng còn sống."""
        return True, "không có tự kiểm tra"
