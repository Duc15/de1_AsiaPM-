"""Schema trường + luật "đúng là gì" (Bước 1).

Đây là nơi duy nhất khai báo: có những trường nào, trường nào quan trọng tới
mức nào, và so khớp bằng luật nào. Bộ đo và bộ sinh dữ liệu đều đọc từ đây,
nên không thể lệch nhau.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

NGUON = Literal["ocr", "qr", "mrz", "llm_repair", "cross_validate", "human"]

# Mức nghiêm trọng: quyết định trọng số khi tính điểm tổng.
#   nghiem_trong = sai là hồ sơ của người khác  -> trọng số cao, không khoan nhượng
#   trung_binh   = sai thì người duyệt còn cơ hội phát hiện
#   nhe          = sai gây bất tiện, không gây hậu quả pháp lý
MUC_DO = Literal["nghiem_trong", "trung_binh", "nhe"]

TRONG_SO: dict[str, float] = {"nghiem_trong": 3.0, "trung_binh": 1.5, "nhe": 1.0}


@dataclass(frozen=True)
class Truong:
    ten: str
    nhan_hien_thi: str
    muc_do: MUC_DO
    kieu: Literal["so_dinh_danh", "ten_nguoi", "ngay", "dia_chi", "so_luong", "tien", "enum"]
    # Nhãn in trên giấy tờ — bộ tách trường dùng làm mốc neo, bộ sinh dữ liệu
    # dùng làm text in ra. Một mốc là đủ để khớp (khớp mờ).
    moc_neo: tuple[str, ...] = ()
    gia_tri_hop_le: tuple[str, ...] = ()

    @property
    def trong_so(self) -> float:
        return TRONG_SO[self.muc_do]


@dataclass(frozen=True)
class LoaiGiayTo:
    ma: str
    ten: str
    truong: tuple[Truong, ...]

    def lay(self, ten: str) -> Truong:
        for t in self.truong:
            if t.ten == ten:
                return t
        raise KeyError(f"{self.ma} không có trường {ten}")


CCCD = LoaiGiayTo(
    ma="cccd",
    ten="Căn cước công dân",
    truong=(
        Truong("so_dinh_danh", "Số định danh", "nghiem_trong", "so_dinh_danh",
               moc_neo=("Số:", "So:")),
        Truong("ho_ten", "Họ và tên", "nghiem_trong", "ten_nguoi",
               moc_neo=("Họ và tên:", "Ho va ten:")),
        Truong("ngay_sinh", "Ngày sinh", "trung_binh", "ngay",
               moc_neo=("Ngày sinh:", "Ngay sinh:")),
        Truong("noi_thuong_tru", "Nơi thường trú", "trung_binh", "dia_chi",
               moc_neo=("Nơi thường trú:", "Noi thuong tru:")),
    ),
)

MAU_01 = LoaiGiayTo(
    ma="mau_01",
    ten="Mẫu số 01 — Đơn đăng ký NƠXH",
    truong=(
        Truong("ho_ten_nguoi_viet_don", "Họ tên người viết đơn", "nghiem_trong", "ten_nguoi",
               moc_neo=("Họ và tên người viết đơn:", "Ho va ten nguoi viet don:")),
        Truong("hinh_thuc", "Hình thức đăng ký", "trung_binh", "enum",
               moc_neo=("Hình thức đăng ký:",),
               gia_tri_hop_le=("mua", "thuê", "thuê mua")),
        Truong("dien_tich_binh_quan", "Diện tích bình quân (m²/người)", "trung_binh", "so_luong",
               moc_neo=("Diện tích bình quân:", "Dien tich binh quan:")),
        Truong("thu_nhap_hang_thang", "Thu nhập hàng tháng (đồng)", "trung_binh", "tien",
               moc_neo=("Thu nhập hàng tháng:", "Thu nhap hang thang:")),
    ),
)

LOAI_GIAY_TO: dict[str, LoaiGiayTo] = {d.ma: d for d in (CCCD, MAU_01)}


# ---------------------------------------------------------------------------
# Thang chất lượng ảnh. Nhãn ở mức "khong_doc_duoc" là null theo AC3:
# hành vi đúng của mô hình ở đó là KHÔNG trả về giá trị.
# ---------------------------------------------------------------------------
MUC_CHAT_LUONG: tuple[str, ...] = ("sach", "nhe", "trung_binh", "nang", "khong_doc_duoc")

MUC_KHONG_DOC_DUOC = "khong_doc_duoc"


def moi_truong() -> list[tuple[str, Truong]]:
    """Danh sách (ma_loai, truong) của toàn bộ schema."""
    return [(d.ma, t) for d in LOAI_GIAY_TO.values() for t in d.truong]
