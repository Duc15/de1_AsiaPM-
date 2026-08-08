"""Đối tượng "Hồ sơ giấy tờ" — bản cài `DoiTuongKiemThu` cho bài 1.

Nó bọc: một ảnh giấy tờ + cụm model trích xuất + cổng HITL, rồi phơi ra hành vi
nghiệp vụ mà bước Gherkin gọi tới. Bước Gherkin không biết Tesseract tồn tại —
đúng như bước Gherkin của bài 2 không biết Playwright tồn tại.
"""

from __future__ import annotations

from pathlib import Path

from bo_do.chay import GOC
from bo_do.mo_hinh.tesseract import tao_mo_hinh
from bo_do.so_bang_chung import CAN_BO_SUNG, _trang_thai_ho_so

from .co_so import DoiTuongKiemThu, KetQuaTruong, KetQuaXuLy


class HoSoGiayTo(DoiTuongKiemThu):
    ten_nen_tang = "model-trich-xuat"

    def __init__(self, ten_model: str = "tesseract", nguong_hitl: float = 0.8) -> None:
        self._mo_hinh = tao_mo_hinh(ten_model)
        self._nguong = nguong_hitl
        self._anh: Path | None = None
        self._doc_type: str | None = None
        self._cache: dict[tuple[str, str], object] = {}   # chỉ cache OCR thô

    # -- vòng đời -----------------------------------------------------------
    def mo(self, dinh_danh: str) -> "HoSoGiayTo":
        """`dinh_danh` là mã ảnh, ví dụ `cccd_sach_01`."""
        self._anh = GOC / "data" / "anh" / f"{dinh_danh}.jpg"
        self._doc_type = "cccd" if dinh_danh.startswith("cccd") else "mau_01"
        return self

    def xu_ly(self) -> KetQuaXuLy:
        """Chạy trích xuất rồi áp cổng HITL theo ngưỡng ĐANG cấu hình.

        Chỉ phần OCR được cache — nó đắt và không phụ thuộc ngưỡng. Cờ
        `can_nguoi_xac_nhan` thì tính lại mỗi lần, vì nó là hàm của ngưỡng.

        Bản đầu cache cả kết quả đã áp cổng, khoá theo (ảnh, loại). Hậu quả:
        kịch bản "ngưỡng phải cấu hình được" đổi ngưỡng xong vẫn nhận cờ cũ, và
        ca kiểm thử đó đỏ — đúng cái nó sinh ra để bắt, chỉ có điều lỗi nằm ở
        lớp đối tượng chứ không ở model.
        """
        if self._anh is None or self._doc_type is None:
            raise RuntimeError("chưa mở hồ sơ nào — gọi .mo(<mã ảnh>) trước")
        khoa = (str(self._anh), self._doc_type)
        if khoa not in self._cache:             # OCR đắt, một ảnh chỉ chạy một lần
            self._cache[khoa] = self._mo_hinh.trich_xuat(str(self._anh), self._doc_type)
        tho = self._cache[khoa]
        trang_thai, ly_do = _trang_thai_ho_so(tho, self._doc_type)

        truong = {}
        for f in tho.fields:
            truong[f.ten_truong] = KetQuaTruong(
                ten=f.ten_truong, gia_tri=f.gia_tri, tin_cay=f.confidence,
                # AC2: "dưới ngưỡng cấu hình" -> so sánh NGẶT
                can_nguoi_xac_nhan=(f.confidence is None or f.confidence < self._nguong),
                nguon=f.nguon)

        return KetQuaXuLy(trang_thai=trang_thai, ly_do=ly_do, truong=truong,
                          thoi_gian_ms=tho.thoi_gian_ms,
                          loi_he_thong=tho.loi_he_thong, chan_doan=tho.chan_doan)

    def tu_kiem_tra(self) -> tuple[bool, str]:
        return self._mo_hinh.tu_kiem_tra()

    # -- tiện ích cho bước Gherkin -----------------------------------------
    @property
    def nguong_hitl(self) -> float:
        return self._nguong

    def doi_nguong(self, nguong: float) -> "HoSoGiayTo":
        """AC2 đòi ngưỡng phải CẤU HÌNH được — bước Gherkin dùng để chứng minh."""
        self._nguong = nguong
        return self

    @property
    def mo_ta_model(self) -> str:
        return f"{self._mo_hinh.ten} ({self._mo_hinh.phien_ban})"

    def can_bo_sung(self) -> bool:
        return self.xu_ly().trang_thai == CAN_BO_SUNG
