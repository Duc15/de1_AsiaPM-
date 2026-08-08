"""Unit test cho LUẬT SO KHỚP của Bước 1 — cái thước đo, không phải cái được đo.

Vì sao đây là file test quan trọng nhất repo: mọi con số trong báo cáo đều đi qua
`so_khop_truong()`. Luật đó sai một chỗ thì cả bài sai, mà sai kiểu im lặng —
không có exception nào, chỉ có accuracy lệch đi vài điểm phần trăm.

Chạy trong ~0,2 giây (không gọi OCR), nên chạy được ở mọi commit.

  TC-LUAT-01..06   sáu tình huống đề nêu nguyên văn ở Bước 1
  TC-LUAT-1x       theo kiểu trường: số định danh, tên, ngày, tiền, số lượng, enum, địa chỉ
  TC-LUAT-2x       sáu phán quyết, gồm các nhánh AC3 (từ chối đúng / bịa)
  TC-LUAT-3x       ranh giới: ngưỡng khớp mờ địa chỉ
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GOC))

from bo_do.so_khop import (BIA, BO_SOT, DUNG, LOI_HE_THONG, NGUONG_GIONG_DIA_CHI,  # noqa: E402
                           SAI, TU_CHOI_DUNG, so_khop_truong)

CCCD = "cccd"
MAU = "mau_01"


# ===========================================================================
# TC-LUAT-01..06 — sáu tình huống đề nêu ở Bước 1. Đây là đáp án của tôi,
# viết thành test để không ai (kể cả tôi) đổi luật mà quên đổi báo cáo.
# ===========================================================================
SAU_TINH_HUONG = [
    ("TC-LUAT-01", CCCD, "ho_ten", "TRẦN THỊ MAI", "Trần Thị Mai", DUNG, None),
    ("TC-LUAT-02", CCCD, "ho_ten", "TRẦN THỊ MAI", "TRAN THI MAI", SAI, "sai_dau"),
    ("TC-LUAT-03", CCCD, "ho_ten", "TRẦN THỊ MAI", "TRÀN THỊ MAI", SAI, "sai_dau"),
    ("TC-LUAT-04", CCCD, "ngay_sinh", "01/03/1990", "1/3/1990", DUNG, None),
    ("TC-LUAT-05", CCCD, "so_dinh_danh", "000301001234", "000301001284", SAI, "sai_1_chu_so"),
    ("TC-LUAT-06", MAU, "dien_tich_binh_quan", "15 m²", "15", DUNG, None),
]


@pytest.mark.parametrize("ma,loai,truong,nhan,model,pq,loai_sai",
                         SAU_TINH_HUONG, ids=[c[0] for c in SAU_TINH_HUONG])
def test_sau_tinh_huong_de_neu(ma, loai, truong, nhan, model, pq, loai_sai):
    kq = so_khop_truong(loai, truong, nhan, model)
    assert kq.phan_quyet == pq, f"{ma}: {nhan!r} vs {model!r} → {kq.phan_quyet}, cần {pq}"
    if loai_sai:
        assert kq.loai_sai == loai_sai, f"{ma}: phân loại lỗi ra {kq.loai_sai}"


# ===========================================================================
# TC-LUAT-1x — theo kiểu trường. Mỗi kiểu có ca thuận, ca nghịch và ca biên.
# ===========================================================================
THEO_KIEU = [
    # --- số định danh: tuyệt đối, không khoan nhượng ---------------------
    ("TC-LUAT-10", CCCD, "so_dinh_danh", "000301001234", "000301001234", DUNG, None),
    ("TC-LUAT-11", CCCD, "so_dinh_danh", "000301001234", "0003 0100 1234", DUNG, None),
    ("TC-LUAT-12", CCCD, "so_dinh_danh", "000301001234", "00030100123", SAI, "sai_do_dai"),
    ("TC-LUAT-13", CCCD, "so_dinh_danh", "000301001234", "000301001243", SAI, "sai_nhieu_chu_so"),
    ("TC-LUAT-14", CCCD, "so_dinh_danh", "000301001234", "abc", SAI, None),

    # --- tên người: dấu mang thông tin, hoa/thường thì không -------------
    ("TC-LUAT-15", CCCD, "ho_ten", "TRẦN THỊ MAI", "  TRẦN   THỊ  MAI  ", DUNG, None),
    ("TC-LUAT-16", CCCD, "ho_ten", "TRẦN THỊ MAI", "TRẦN, THỊ. MAI", DUNG, None),
    ("TC-LUAT-17", CCCD, "ho_ten", "LÊ THỊ NGỌC HUYỀN", "LÊ THỊ NGỌC", SAI,
     "thieu_hoac_thua_phan"),
    ("TC-LUAT-18", CCCD, "ho_ten", "BÙI QUỐC ĐẠT", "NGUYỄN VĂN A", SAI, "sai_hoan_toan"),

    # --- ngày: định dạng là trình bày, giá trị mới là thông tin ----------
    ("TC-LUAT-19", CCCD, "ngay_sinh", "01/03/1990", "1990-03-01", DUNG, None),
    ("TC-LUAT-20", CCCD, "ngay_sinh", "01/03/1990", "01-03-1990", DUNG, None),
    ("TC-LUAT-21", CCCD, "ngay_sinh", "01/03/1990", "03/01/1990", SAI, "sai_gia_tri_ngay"),
    ("TC-LUAT-22", CCCD, "ngay_sinh", "01/03/1990", "32/13/1990", SAI, "khong_phai_ngay"),
    ("TC-LUAT-23", CCCD, "ngay_sinh", "01/03/1990", "TUẦN", SAI, "khong_phai_ngay"),

    # --- tiền: dấu phân cách nghìn là trình bày, so theo dãy chữ số ------
    ("TC-LUAT-24", MAU, "thu_nhap_hang_thang", "8.500.000 đồng", "8500000", DUNG, None),
    ("TC-LUAT-25", MAU, "thu_nhap_hang_thang", "8.500.000 đồng", "8500.000 đồng", DUNG, None),
    ("TC-LUAT-26", MAU, "thu_nhap_hang_thang", "8.500.000 đồng", "8 500 000", DUNG, None),
    ("TC-LUAT-27", MAU, "thu_nhap_hang_thang", "11.000.000 đồng", "17.000.000", SAI,
     "sai_1_chu_so"),
    ("TC-LUAT-28", MAU, "thu_nhap_hang_thang", "8.500.000 đồng", "850.000", SAI,
     "sai_so_chu_so"),

    # --- số lượng: dấu thập phân MANG thông tin (ngược với tiền) --------
    ("TC-LUAT-29", MAU, "dien_tich_binh_quan", "18,5 m²", "18.5", DUNG, None),
    ("TC-LUAT-30", MAU, "dien_tich_binh_quan", "18,5 m²", "185", SAI, None),
    ("TC-LUAT-31", MAU, "dien_tich_binh_quan", "18,5 m²", "18", SAI, None),
    ("TC-LUAT-32", MAU, "dien_tich_binh_quan", "15 m²", "15 m2", DUNG, None),

    # --- enum: chỉ nhận đúng tập giá trị -------------------------------
    ("TC-LUAT-33", MAU, "hinh_thuc", "thuê mua", "Thuê mua", DUNG, None),
    ("TC-LUAT-34", MAU, "hinh_thuc", "thuê mua", "thuê", SAI, "chon_sai_o"),
    ("TC-LUAT-35", MAU, "hinh_thuc", "mua", "bán", SAI, "ngoai_tap_gia_tri"),

    # --- địa chỉ: khớp mờ, có chuẩn hoá viết tắt hành chính -------------
    ("TC-LUAT-36", CCCD, "noi_thuong_tru",
     "Số 12 Đường Lê Duẩn, Phường Tân Mai, Quận Hoàng Mai, Thành phố Hà Nội",
     "So 12 Duong Le Duan, Phuong Tan Mai, Quan Hoang Mai, Thanh pho Ha Noi", SAI, None),
    ("TC-LUAT-37", CCCD, "noi_thuong_tru",
     "Số 12 Đường Lê Duẩn, Phường Tân Mai, Quận Hoàng Mai, Thành phố Hà Nội",
     "Số 12 Đường Lê Duẩn, Phường Tân Mai", SAI, "lech_qua_nguong"),
]


@pytest.mark.parametrize("ma,loai,truong,nhan,model,pq,loai_sai",
                         THEO_KIEU, ids=[c[0] for c in THEO_KIEU])
def test_luat_theo_kieu_truong(ma, loai, truong, nhan, model, pq, loai_sai):
    kq = so_khop_truong(loai, truong, nhan, model)
    assert kq.phan_quyet == pq, f"{ma}: {nhan!r} vs {model!r} → {kq.phan_quyet}, cần {pq}"
    if loai_sai:
        assert kq.loai_sai == loai_sai, f"{ma}: phân loại lỗi ra {kq.loai_sai!r}"


# ===========================================================================
# TC-LUAT-2x — sáu phán quyết. Đây là chỗ AC3 sống hoặc chết.
# ===========================================================================
SAU_PHAN_QUYET = [
    ("TC-LUAT-40 dung", CCCD, "so_dinh_danh", "000301001234", "000301001234", DUNG),
    ("TC-LUAT-41 sai", CCCD, "so_dinh_danh", "000301001234", "000301001299", SAI),
    ("TC-LUAT-42 bo_sot", CCCD, "so_dinh_danh", "000301001234", None, BO_SOT),
    ("TC-LUAT-43 bo_sot_chuoi_rong", CCCD, "so_dinh_danh", "000301001234", "   ", BO_SOT),
    ("TC-LUAT-44 tu_choi_dung", CCCD, "so_dinh_danh", None, None, TU_CHOI_DUNG),
    ("TC-LUAT-45 bia", CCCD, "so_dinh_danh", None, "000301001234", BIA),
    ("TC-LUAT-46 bia_ca_rac", CCCD, "ho_ten", None, "xxx", BIA),
]


@pytest.mark.parametrize("ma,loai,truong,nhan,model,pq",
                         SAU_PHAN_QUYET, ids=[c[0].split()[0] for c in SAU_PHAN_QUYET])
def test_sau_phan_quyet(ma, loai, truong, nhan, model, pq):
    kq = so_khop_truong(loai, truong, nhan, model)
    assert kq.phan_quyet == pq, f"{ma}: → {kq.phan_quyet}, cần {pq}"


def test_TC_LUAT_47_loi_he_thong_khong_bi_tinh_la_sai():
    """Không gọi được model ≠ model trả sai. Gộp hai thứ này là tự bịa số liệu."""
    kq = so_khop_truong(CCCD, "so_dinh_danh", "000301001234", None, loi_he_thong=True)
    assert kq.phan_quyet == LOI_HE_THONG
    assert not kq.la_dung


def test_TC_LUAT_48_tu_choi_dung_duoc_tinh_la_dung():
    """AC3: im lặng trên ảnh không đọc được là hành vi ĐÚNG, phải được tính điểm."""
    assert so_khop_truong(CCCD, "ho_ten", None, None).la_dung is True


def test_TC_LUAT_49_bia_khong_bao_gio_duoc_tinh_la_dung():
    assert so_khop_truong(CCCD, "ho_ten", None, "TRẦN THỊ MAI").la_dung is False


# ===========================================================================
# TC-LUAT-3x — ranh giới ngưỡng khớp mờ địa chỉ (phân tích giá trị biên).
# ===========================================================================
def test_TC_LUAT_50_bien_nguong_khop_mo_dia_chi():
    """Dựng hai chuỗi nằm hai bên ngưỡng rồi kiểm phán quyết lật đúng chỗ."""
    goc = "Thôn Đoài, Xã Nguyên Khê, Huyện Đông Anh, Thành phố Hà Nội"
    tren = so_khop_truong(CCCD, "noi_thuong_tru", goc, goc + " ")
    assert tren.phan_quyet == DUNG and tren.do_giong >= NGUONG_GIONG_DIA_CHI

    duoi = so_khop_truong(CCCD, "noi_thuong_tru", goc, "Thôn Đoài")
    assert duoi.phan_quyet == SAI and duoi.do_giong < NGUONG_GIONG_DIA_CHI


def test_TC_LUAT_51_truong_la_bi_tu_choi_ngay():
    """Gọi sai tên trường phải nổ ngay, không được im lặng trả về SAI."""
    with pytest.raises(KeyError):
        so_khop_truong(CCCD, "truong_khong_ton_tai", "a", "b")


def test_TC_LUAT_52_loai_giay_to_la_bi_tu_choi_ngay():
    with pytest.raises(KeyError):
        so_khop_truong("ho_chieu", "ho_ten", "a", "b")
