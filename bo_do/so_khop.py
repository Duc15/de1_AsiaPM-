"""Bước 1 — "đúng" nghĩa là gì, viết thành luật máy thi hành được.

Mỗi trường trả về một PHAN_QUYET trong 6 giá trị. Ba giá trị sau không phải
"sai" theo nghĩa thông thường và cố tình được tách riêng, vì AC3 và cảnh báo ở
Bước 4 của đề đòi phân biệt chúng:

  DUNG          nhãn có giá trị, model trả đúng
  SAI           nhãn có giá trị, model trả khác
  BO_SOT        nhãn có giá trị, model không trả gì (im lặng quá mức)
  TU_CHOI_DUNG  nhãn là null (ảnh không đọc được), model không trả gì  -> ĐÚNG theo AC3
  BIA           nhãn là null, model vẫn trả ra giá trị                 -> vi phạm AC3
  LOI_HE_THONG  không gọi được model / bộ tách vỡ -> không tính vào accuracy

Vì sao tách BIA khỏi SAI: một trường sai trên ảnh đọc được là lỗi nhận dạng,
người duyệt còn ảnh gốc để đối chiếu. Một trường bịa trên ảnh không đọc được là
dữ liệu không có nguồn gốc — AC3 gọi đó là hành vi bị cấm, không phải hành vi kém.
"""

from __future__ import annotations

import difflib
from dataclasses import dataclass

from . import chuan_hoa as ch
from .schema import LOAI_GIAY_TO, Truong

DUNG = "DUNG"
SAI = "SAI"
BO_SOT = "BO_SOT"
TU_CHOI_DUNG = "TU_CHOI_DUNG"
BIA = "BIA"
LOI_HE_THONG = "LOI_HE_THONG"

# Ngưỡng giống nhau cho địa chỉ. Địa chỉ là trường tự do, dài, OCR gần như luôn
# lệch một hai ký tự; đòi khớp tuyệt đối thì phép đo chỉ đo được độ dài chuỗi.
NGUONG_GIONG_DIA_CHI = 0.90


@dataclass
class KetQuaSoKhop:
    phan_quyet: str
    loai_sai: str | None = None   # phân loại lỗi để trả lời "sai ở đâu"
    do_giong: float | None = None
    ghi_chu: str = ""

    @property
    def la_dung(self) -> bool:
        return self.phan_quyet in (DUNG, TU_CHOI_DUNG)


def _giong(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a, b).ratio()


def _phan_loai_sai_chuoi(nhan: str, tra_ve: str) -> str:
    """Chỉ để phân tích lỗi — không ảnh hưởng phán quyết đúng/sai."""
    n, t = ch.ten_nguoi(nhan), ch.ten_nguoi(tra_ve)
    if ch.bo_dau(n) == ch.bo_dau(t):
        return "sai_dau"          # mất dấu hoặc sai dấu, phần chữ cái đúng
    if len(n) == len(t) and sum(x != y for x, y in zip(n, t)) == 1:
        return "sai_1_ky_tu"
    if n in t or t in n:
        return "thieu_hoac_thua_phan"
    if _giong(ch.bo_dau(n), ch.bo_dau(t)) >= 0.7:
        return "sai_vai_ky_tu"
    return "sai_hoan_toan"


def _so_khop_gia_tri(truong: Truong, nhan: str, tra_ve: str) -> KetQuaSoKhop:
    kieu = truong.kieu

    if kieu == "so_dinh_danh":
        a, b = ch.chi_so(nhan), ch.chi_so(tra_ve)
        if a == b:
            return KetQuaSoKhop(DUNG, do_giong=1.0)
        loai = "sai_do_dai" if len(a) != len(b) else (
            "sai_1_chu_so" if sum(x != y for x, y in zip(a, b)) == 1 else "sai_nhieu_chu_so")
        # Không có khoan nhượng ở đây: sai một chữ số là hồ sơ của người khác.
        return KetQuaSoKhop(SAI, loai, _giong(a, b),
                            "số định danh so khớp tuyệt đối theo chữ số")

    if kieu == "ten_nguoi":
        a, b = ch.ten_nguoi(nhan), ch.ten_nguoi(tra_ve)
        if a == b:
            return KetQuaSoKhop(DUNG, do_giong=1.0)
        return KetQuaSoKhop(SAI, _phan_loai_sai_chuoi(nhan, tra_ve), _giong(a, b))

    if kieu == "ngay":
        a, b = ch.ngay(nhan), ch.ngay(tra_ve)
        if a is not None and a == b:
            return KetQuaSoKhop(DUNG, do_giong=1.0)
        if b is None:
            return KetQuaSoKhop(SAI, "khong_phai_ngay", 0.0,
                                f"không parse được {tra_ve!r} thành ngày")
        return KetQuaSoKhop(SAI, "sai_gia_tri_ngay", _giong(a or "", b))

    if kieu == "tien":
        # Quyết định của Bước 1: với tiền, dấu phân cách nghìn là CÁCH TRÌNH BÀY,
        # không phải giá trị. "8.500.000" và "8500.000" và "8 500 000" là cùng một
        # số tiền, nên so khớp trên dãy chữ số. Đổi lại, "8.500.000" vs "8.500.00"
        # bị tính sai — đúng như mong muốn, vì đó là lệch một chữ số thật.
        a, b = ch.chi_so(nhan), ch.chi_so(tra_ve)
        if a and a == b:
            return KetQuaSoKhop(DUNG, do_giong=1.0,
                                ghi_chu="so khớp theo dãy chữ số, bỏ dấu phân cách nghìn")
        if not b:
            return KetQuaSoKhop(SAI, "khong_phai_so", 0.0)
        if len(a) != len(b):
            return KetQuaSoKhop(SAI, "sai_so_chu_so", _giong(a, b))
        if sum(x != y for x, y in zip(a, b)) == 1:
            return KetQuaSoKhop(SAI, "sai_1_chu_so", _giong(a, b))
        return KetQuaSoKhop(SAI, "sai_nhieu_chu_so", _giong(a, b))

    if kieu == "so_luong":
        a, b = ch.so(nhan), ch.so(tra_ve)
        if a is not None and b is not None and abs(a - b) < 1e-9:
            return KetQuaSoKhop(DUNG, do_giong=1.0, ghi_chu="đơn vị do schema quy định, không tính vào so khớp")
        if b is None:
            return KetQuaSoKhop(SAI, "khong_phai_so", 0.0)
        if a and b and abs(b / a - 1) < 0.001:
            return KetQuaSoKhop(SAI, "lech_lam_tron", 0.99)
        if a and b in (a * 1000, a / 1000, a * 1_000_000, a / 1_000_000):
            return KetQuaSoKhop(SAI, "sai_bac_don_vi", 0.5)
        return KetQuaSoKhop(SAI, "sai_gia_tri_so", 0.0)

    if kieu == "dia_chi":
        a, b = ch.dia_chi(nhan), ch.dia_chi(tra_ve)
        r = _giong(a, b)
        if r >= NGUONG_GIONG_DIA_CHI:
            return KetQuaSoKhop(DUNG, do_giong=r,
                                ghi_chu=f"khớp mờ ≥ {NGUONG_GIONG_DIA_CHI}")
        return KetQuaSoKhop(SAI, "lech_qua_nguong" if r >= 0.6 else "sai_hoan_toan", r)

    if kieu == "enum":
        a, b = ch.enum_hinh_thuc(nhan), ch.enum_hinh_thuc(tra_ve)
        if a is not None and a == b:
            return KetQuaSoKhop(DUNG, do_giong=1.0)
        if b is None:
            return KetQuaSoKhop(SAI, "ngoai_tap_gia_tri", 0.0,
                                f"{tra_ve!r} không thuộc {truong.gia_tri_hop_le}")
        return KetQuaSoKhop(SAI, "chon_sai_o", 0.0)

    raise ValueError(f"kiểu trường lạ: {kieu}")


def so_khop_truong(ma_loai: str, ten_truong: str,
                   gia_tri_nhan: str | None,
                   gia_tri_model: str | None,
                   loi_he_thong: bool = False) -> KetQuaSoKhop:
    """So khớp một trường. `None` nghĩa là "không có giá trị"."""
    truong = LOAI_GIAY_TO[ma_loai].lay(ten_truong)

    if loi_he_thong:
        return KetQuaSoKhop(LOI_HE_THONG, "loi_goi_model",
                            ghi_chu="không tính vào accuracy, xem mục lỗi hạ tầng")

    co_nhan = gia_tri_nhan is not None and str(gia_tri_nhan).strip() != ""
    co_tra_ve = gia_tri_model is not None and str(gia_tri_model).strip() != ""

    if not co_nhan:
        # Ảnh không đọc được -> AC3: đúng là không trả gì.
        if not co_tra_ve:
            return KetQuaSoKhop(TU_CHOI_DUNG, ghi_chu="AC3: từ chối đúng")
        return KetQuaSoKhop(BIA, "bia_tren_anh_khong_doc_duoc",
                            ghi_chu=f"AC3 bị vi phạm: trả {gia_tri_model!r} trên ảnh không đọc được")

    if not co_tra_ve:
        return KetQuaSoKhop(BO_SOT, "im_lang_tren_anh_doc_duoc",
                            ghi_chu="nhãn có giá trị nhưng model không trả gì")

    kq = _so_khop_gia_tri(truong, str(gia_tri_nhan), str(gia_tri_model))
    return kq
