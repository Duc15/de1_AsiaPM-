"""Ca đường lỗi và tính chất của adapter — kiểm cách GỌI model, không kiểm model.

Đề cảnh báo: "khi model trả về kết quả rỗng, đó chưa chắc là lỗi model — nó có
thể là lỗi ở cách bạn gọi model". File này là chỗ ranh giới đó được kiểm bằng
máy: mỗi kiểu hỏng phải rơi vào đúng ô của nó, vì ba ô đó dẫn tới ba hành động
khác nhau và ba người khác nhau phải sửa.

    lỗi hạ tầng      -> `loi_he_thong` có giá trị  -> kỹ sư sửa, KHÔNG tính điểm
    từ chối chính sách -> `ly_do_tu_choi` có giá trị -> hành vi đúng theo AC3
    lỗi lập trình    -> ném exception ngay        -> không được im lặng nuốt
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GOC))

from bo_do.mo_hinh.tesseract import MoHinhTesseract, tao_mo_hinh  # noqa: E402
from bo_do.schema import LOAI_GIAY_TO  # noqa: E402

ANH_SACH = GOC / "data" / "anh" / "cccd_sach_01.jpg"
ANH_KHONG_DOC_DUOC = GOC / "data" / "anh" / "cccd_khong_doc_duoc_01.jpg"


@pytest.fixture(scope="module")
def model():
    return MoHinhTesseract()


# ===========================================================================
# Lỗi hạ tầng phải được nhận diện, không được biến thành "model đọc không ra"
# ===========================================================================
def test_TC_BT_01_tep_khong_ton_tai_bao_loi_ha_tang(model):
    kq = model.trich_xuat(str(GOC / "data" / "anh" / "khong_he_ton_tai.jpg"), "cccd")
    assert kq.loi_he_thong is not None, (
        "ảnh không tồn tại mà adapter trả về êm ru — bộ đo sẽ ghi thành 'model bỏ "
        "sót' và đổ lỗi cho model")
    assert kq.fields == []
    assert kq.ly_do_tu_choi is None, "không được nhầm lỗi hạ tầng thành từ chối AC3"


def test_TC_BT_02_tep_anh_hong_bao_loi_ha_tang(model, tmp_path):
    hong = tmp_path / "hong.jpg"
    hong.write_bytes(b"day khong phai anh JPEG")
    kq = model.trich_xuat(str(hong), "cccd")
    assert kq.loi_he_thong is not None
    assert kq.ly_do_tu_choi is None


def test_TC_BT_03_tep_rong_bao_loi_ha_tang(model, tmp_path):
    rong = tmp_path / "rong.jpg"
    rong.write_bytes(b"")
    kq = model.trich_xuat(str(rong), "cccd")
    assert kq.loi_he_thong is not None


def test_TC_BT_04_anh_1x1_khong_lam_vo_adapter(model, tmp_path):
    """Ảnh hợp lệ nhưng vô nghĩa: phải từ chối, không được ném exception."""
    from PIL import Image
    tin_hieu = tmp_path / "1x1.jpg"
    Image.new("RGB", (1, 1), (255, 255, 255)).save(tin_hieu, "JPEG")
    kq = model.trich_xuat(str(tin_hieu), "cccd")
    assert kq.loi_he_thong is None, "ảnh hợp lệ mà báo lỗi hạ tầng là sai phân loại"
    assert kq.fields == []
    assert kq.ly_do_tu_choi, "phải nêu lý do từ chối, đây là đòi hỏi của AC3"


# ===========================================================================
# Lỗi lập trình phải nổ ngay, không được im lặng trả rỗng
# ===========================================================================
def test_TC_BT_05_loai_giay_to_la_phai_nem_loi(model):
    """Trả rỗng cho doc_type lạ sẽ trông y hệt "từ chối đúng theo AC3" trong log —
    tức là một bug của người gọi được ghi vào sổ như một điểm cộng cho model."""
    with pytest.raises(KeyError):
        model.trich_xuat(str(ANH_SACH), "ho_chieu")


def test_TC_BT_06_ten_model_la_bi_tu_choi_kem_goi_y():
    with pytest.raises(SystemExit) as e:
        tao_mo_hinh("model_khong_ton_tai")
    assert "tesseract" in str(e.value), "thông báo lỗi phải liệt kê model có sẵn"


# ===========================================================================
# Tính chất của cụm model
# ===========================================================================
def test_TC_BT_07_canary_ha_tang_dat(model):
    ok, ghi_chu = model.tu_kiem_tra()
    assert ok, f"canary vỡ: {ghi_chu}"


def test_TC_BT_08_tat_dinh_chay_hai_lan_ra_ket_qua_giong_het(model):
    """Chứng minh sigma = 0 bằng test, không phải bằng quan sát tay.

    Đây là điều kiện để cổng hồi quy ở Bước 5 thu về so khớp chính xác: nếu một
    ngày model thành ngẫu nhiên, ca này đỏ và biên độ phải được đo lại.
    """
    a = model.trich_xuat(str(ANH_SACH), "cccd").to_dict()
    b = model.trich_xuat(str(ANH_SACH), "cccd").to_dict()
    for x in (a, b):
        x.pop("thoi_gian_ms")
    assert a == b, "cùng ảnh, cùng tham số mà ra hai kết quả khác nhau"


def test_TC_BT_09_khong_bia_khi_bi_ep_chay_tren_anh_khong_doc_duoc(model):
    """Tắt chính sách từ chối rồi vẫn không được bịa — kiểm lớp phòng vệ thứ hai.

    Đây chính là mutation M6 được cố định thành một ca kiểm thử thường trực:
    hành vi "không bịa" không được phép chỉ dựa vào một tham số ngưỡng.
    """
    import bo_do.mo_hinh.tesseract as T
    cu = (T.TOI_THIEU_SO_TU, T.TOI_THIEU_CONF_ANH)
    T.TOI_THIEU_SO_TU, T.TOI_THIEU_CONF_ANH = 0, -1.0
    try:
        kq = model.trich_xuat(str(ANH_KHONG_DOC_DUOC), "cccd")
    finally:
        T.TOI_THIEU_SO_TU, T.TOI_THIEU_CONF_ANH = cu
    assert kq.ly_do_tu_choi is None, "chính sách từ chối lẽ ra đã bị tắt"
    assert kq.fields == [], (
        f"bịa trên ảnh không đọc được khi mất lớp phòng vệ thứ nhất: "
        f"{[(f.ten_truong, f.gia_tri) for f in kq.fields]}")


def test_TC_BT_10_model_doi_chung_luon_tu_choi():
    """Model đối chứng phải im lặng tuyệt đối — nó là mốc để bộ đo tự soi mình."""
    m = tao_mo_hinh("luon_tu_choi")
    for ma_loai in LOAI_GIAY_TO:
        kq = m.trich_xuat(str(ANH_SACH), ma_loai)
        assert kq.fields == []
        assert kq.ly_do_tu_choi
        assert kq.loi_he_thong is None


def test_TC_BT_11_moi_truong_tra_ve_deu_thuoc_schema_va_co_conf(model):
    """Hợp đồng đầu ra ở mức adapter (AC1 kiểm ở mức toàn bộ lượt chạy)."""
    for ma_loai, tep in (("cccd", ANH_SACH),):
        kq = model.trich_xuat(str(tep), ma_loai)
        hop_le = {t.ten for t in LOAI_GIAY_TO[ma_loai].truong}
        assert kq.fields, "ảnh sạch mà không trích được trường nào"
        for f in kq.fields:
            assert f.ten_truong in hop_le
            assert f.confidence is not None and 0.0 <= f.confidence <= 1.0
            assert f.gia_tri, "trường có mặt thì phải có giá trị, không được rỗng"
