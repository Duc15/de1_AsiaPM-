"""Lớp đối tượng kiểm thử — vai trò của Page Object, tổng quát hoá cho nhiều nền tảng.

VÌ SAO KHÔNG GỌI LÀ "PAGE OBJECT"
    Page Object sinh ra để giấu **locator** của một trang web. Bài 1 không có
    trang, không có locator, không có trình duyệt — đối tượng dưới quyền là một
    cụm model OCR chạy headless. Gọi nó là Page thì cái tên nói dối về thứ nó bọc.

    Nhưng NGUYÊN LÝ của POM thì giữ nguyên và chính là thứ cần ở đây:

        giấu CÁCH tương tác  →  phơi ra HÀNH VI nghiệp vụ  →  bước Gherkin
        viết một lần, dùng cho mọi nền tảng.

CÁCH SCALE SANG WEB VÀ MOBILE
    Cả ba nền tảng kế thừa `DoiTuongKiemThu` và trả về cùng một `KetQuaTruong`.
    Nhờ vậy các bước Gherkin ở `features/steps/buoc_chung.py` — "Khi hệ thống xử
    lý hồ sơ", "Thì trường X phải bị gắn cờ cần người xác nhận" — dùng lại y
    nguyên, không sửa một dòng:

        bài 1 (model)   HoSoGiayTo(anh, mo_hinh)      -> trích xuất bằng OCR
        bài 2 (web)     TrangTiepNhanHoSo(page)       -> điền form Playwright
        mobile (sau)    ManHinhTiepNhan(driver)       -> chạm Appium

    Cái đổi là lớp `doi_tuong/`. Feature file và bước Gherkin thì không.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class KetQuaTruong:
    """Một trường sau khi hệ thống xử lý — hợp đồng chung cho mọi nền tảng.

    Web sẽ điền `loi` (thông báo lỗi trên màn hình) và bỏ trống `tin_cay`;
    model thì ngược lại. Bước Gherkin nào cần gì thì kiểm cái đó.
    """
    ten: str
    gia_tri: str | None = None
    tin_cay: float | None = None
    can_nguoi_xac_nhan: bool | None = None
    nguon: str | None = None
    loi: str | None = None

    @property
    def co_gia_tri(self) -> bool:
        return self.gia_tri is not None and str(self.gia_tri).strip() != ""


@dataclass
class KetQuaXuLy:
    """Kết quả của một lượt xử lý ở mức HỒ SƠ."""
    trang_thai: str = ""
    ly_do: str | None = None
    truong: dict[str, KetQuaTruong] = field(default_factory=dict)
    thoi_gian_ms: float = 0.0
    loi_he_thong: str | None = None
    chan_doan: dict[str, Any] = field(default_factory=dict)

    def lay(self, ten_truong: str) -> KetQuaTruong:
        return self.truong.get(ten_truong, KetQuaTruong(ten=ten_truong))


class DoiTuongKiemThu(ABC):
    """Hợp đồng tối thiểu mà mọi nền tảng phải cài để dùng chung bước Gherkin."""

    ten_nen_tang: str = "chua-dat-ten"

    @abstractmethod
    def mo(self, dinh_danh: str) -> "DoiTuongKiemThu":
        """Đưa đối tượng về trạng thái sẵn sàng.

        web: `page.goto(url)` · mobile: mở màn hình · model: nạp ảnh giấy tờ.
        """

    @abstractmethod
    def xu_ly(self) -> KetQuaXuLy:
        """Kích hoạt hành vi cần đo.

        web: bấm nộp · mobile: chạm nút · model: chạy worker trích xuất.
        """

    @abstractmethod
    def tu_kiem_tra(self) -> tuple[bool, str]:
        """Canary: hạ tầng còn sống không?

        web: trang có load được không · model: OCR có đọc nổi ảnh chuẩn không.
        Vỡ canary thì mọi kết quả sau đó vô nghĩa, và bộ đo phải DỪNG chứ không
        được báo 0 %.
        """
