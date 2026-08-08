"""Chuẩn hoá giá trị trước khi so khớp.

Nguyên tắc: chuẩn hoá chỉ được xoá những khác biệt KHÔNG mang thông tin nghiệp
vụ (khoảng trắng, chữ hoa/thường, dấu câu, đơn vị đo, dấu phân cách nghìn).
Mọi thứ còn lại — kể cả dấu tiếng Việt trong tên người — được giữ, vì nó phân
biệt hai con người khác nhau.
"""

from __future__ import annotations

import re
import unicodedata

_KHOANG_TRANG = re.compile(r"\s+")
_DAU_CAU = re.compile(r"[.,;:!?'\"“”‘’()\[\]]")


def gon_khoang_trang(s: str) -> str:
    return _KHOANG_TRANG.sub(" ", s).strip()


def bo_dau(s: str) -> str:
    """Bỏ dấu tiếng Việt. Chỉ dùng cho phép đo phụ, không dùng để kết luận đúng/sai."""
    s = s.replace("Đ", "D").replace("đ", "d")
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


def chuan_nfc(s: str) -> str:
    """Gộp về NFC — 'ầ' viết dạng tổ hợp và dạng dựng sẵn phải bằng nhau."""
    return unicodedata.normalize("NFC", s)


def ten_nguoi(s: str) -> str:
    s = chuan_nfc(s)
    s = _DAU_CAU.sub(" ", s)
    return gon_khoang_trang(s).upper()


def chi_so(s: str) -> str:
    """Giữ lại đúng các chữ số. Dùng cho số định danh."""
    return re.sub(r"\D", "", chuan_nfc(s))


def dia_chi(s: str) -> str:
    s = chuan_nfc(s).lower()
    s = _DAU_CAU.sub(" ", s)
    # Viết tắt hành chính rất hay lệch giữa nhãn và OCR, coi là tương đương.
    for dai, ngan in (("thành phố", "tp"), ("quận", "q"), ("phường", "p"),
                      ("huyện", "h"), ("xã", "x"), ("tỉnh", "t"),
                      ("đường", "đ"), ("số nhà", "sn")):
        s = re.sub(rf"\b{dai}\b", ngan, s)
    return gon_khoang_trang(s)


_NGAY = [
    re.compile(r"^(\d{1,2})[/\-. ](\d{1,2})[/\-. ](\d{4})$"),   # 01/03/1990
    re.compile(r"^(\d{4})[/\-. ](\d{1,2})[/\-. ](\d{1,2})$"),   # 1990-03-01
]


def ngay(s: str) -> str | None:
    """Về ISO yyyy-mm-dd. Trả None nếu không phải ngày -> tính là sai."""
    s = gon_khoang_trang(chuan_nfc(s))
    s = re.sub(r"[^\d/\-. ]", "", s).strip()
    for i, mau in enumerate(_NGAY):
        m = mau.match(s)
        if not m:
            continue
        a, b, c = m.groups()
        d, mo, y = (a, b, c) if i == 0 else (c, b, a)
        try:
            di, mi, yi = int(d), int(mo), int(y)
        except ValueError:
            return None
        if not (1 <= mi <= 12 and 1 <= di <= 31 and 1900 <= yi <= 2100):
            return None
        return f"{yi:04d}-{mi:02d}-{di:02d}"
    return None


# Đơn vị phải bị bóc TRƯỚC khi vét chữ số, nếu không "m2" đóng góp một chữ số 2
# vào giá trị: '15 m2' bị đọc thành 152. Tesseract đọc 'm²' thành 'm2' rất thường
# xuyên, nên đây không phải ca hiếm. Lỗi này do unit test TC-LUAT-32 bắt được.
_DON_VI = re.compile(
    r"(m\s*²|m\s*\^?\s*2|mét\s*vuông|met\s*vuong|đồng|dong|vn[dđ]|/\s*người|/\s*nguoi)",
    re.IGNORECASE)


def so(s: str) -> float | None:
    """Về số thực. Bỏ đơn vị (m², đồng, vnđ) và dấu phân cách nghìn.

    '15 m²' -> 15.0 ; '15 m2' -> 15.0 ; '8.500.000 đồng' -> 8500000.0
    '8,5 triệu' -> 8500000.0
    """
    s = chuan_nfc(s).lower().strip()
    if not s:
        return None
    nhan_trieu = "triệu" in s or "tr/" in s or re.search(r"\btr\b", s) is not None
    nhan_nghin = "nghìn" in s or "ngàn" in s
    s = _DON_VI.sub(" ", s)
    s = re.sub(r"[^\d.,]", "", s)
    if not s:
        return None
    # Phân biệt dấu thập phân với dấu phân cách nghìn:
    #   "8.500.000" -> nhiều dấu . cách nhau 3 số  => phân cách nghìn
    #   "8,5"       -> 1 dấu , theo sau 1-2 số     => thập phân (kiểu VN)
    if re.fullmatch(r"\d{1,3}(\.\d{3})+", s):
        s = s.replace(".", "")
    elif re.fullmatch(r"\d{1,3}(,\d{3})+", s):
        s = s.replace(",", "")
    else:
        s = s.replace(".", "#").replace(",", ".").replace("#", ".")
        if s.count(".") > 1:  # còn nhiều dấu -> coi hết là phân cách nghìn
            s = s.replace(".", "")
    try:
        v = float(s)
    except ValueError:
        return None
    if nhan_trieu:
        v *= 1_000_000
    elif nhan_nghin:
        v *= 1_000
    return v


_ENUM_HINH_THUC = {
    "mua": "mua",
    "thue": "thuê",
    "thue mua": "thuê mua",
}


def enum_hinh_thuc(s: str) -> str | None:
    k = bo_dau(gon_khoang_trang(chuan_nfc(s)).lower())
    k = _KHOANG_TRANG.sub(" ", _DAU_CAU.sub(" ", k)).strip()
    return _ENUM_HINH_THUC.get(k)
