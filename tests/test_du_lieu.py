"""Kiểm thử theo dữ liệu — mỗi (ảnh × trường) là MỘT ca kiểm thử độc lập.

132 điểm kiểm, mỗi cái có tên riêng trong báo cáo test, chạy riêng được:

    pytest tests/test_du_lieu.py                              # cả 132
    pytest tests/test_du_lieu.py -k "cccd_sach_01"            # một ảnh
    pytest tests/test_du_lieu.py -k "ho_ten"                  # một trường, mọi ảnh
    pytest tests/test_du_lieu.py -k "khong_doc_duoc"          # riêng nhánh AC3

Điểm kiểm đang hỏng vì lỗi ĐÃ BIẾT được gắn `xfail(strict=True)` theo
`data/nhan/loi_da_biet.json`, nên bộ test chỉ đỏ khi **hành vi đổi**:

    hỏng → vẫn hỏng   xfail   im lặng, đã có mã lỗi theo dõi
    hỏng → ĐẠT        XPASS   ĐỎ: lỗi đã được sửa, phải đóng lỗi và chốt lại sổ
    ĐẠT  → hỏng       FAIL    ĐỎ: hồi quy thật

Model chỉ chạy MỘT lần cho cả module (fixture scope="module", ~35 giây), không
phải 132 lần.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GOC))

for _luong in (sys.stdout, sys.stderr, sys.__stdout__, sys.__stderr__):
    try:
        _luong.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except (AttributeError, ValueError):
        pass

from bo_do.chay import do, doc_nhan  # noqa: E402
from bo_do.so_khop import so_khop_truong  # noqa: E402

TEP_LOI_DA_BIET = GOC / "data" / "nhan" / "loi_da_biet.json"


def _loi_da_biet() -> dict:
    if not TEP_LOI_DA_BIET.exists():
        return {}
    return json.loads(TEP_LOI_DA_BIET.read_text(encoding="utf-8")).get("diem_kiem", {})


def _sinh_ca():
    """Sinh danh sách ca kiểm thử lúc thu thập (collection), trước khi chạy model."""
    da_biet = _loi_da_biet()
    ra = []
    for r in doc_nhan():
        for f in r["fields"]:
            khoa = f"{r['id']}::{f['ten_truong']}"
            danh_dau = []
            if f["ky_vong"] == "vung_xam":
                danh_dau.append(pytest.mark.skip(
                    reason="vùng xám: người gán nhãn cũng không đọc được trường này"))
            elif khoa in da_biet:
                d = da_biet[khoa]
                danh_dau.append(pytest.mark.xfail(
                    strict=True,
                    reason=f"{d['loi']} ({d['phan_quyet']}/{d['loai_sai']}) — "
                           f"nhãn={d['nhan']!r} model={d['model_tra']!r}"))
            ra.append(pytest.param(r["id"], r["doc_type"], f, id=khoa, marks=danh_dau))
    return ra


CA = _sinh_ca()


@pytest.fixture(scope="module")
def ket_qua_chay():
    kq = do("tesseract", lap=1, in_tien_do=False)
    if not kq["canary_ok"]:
        pytest.fail(f"Canary hạ tầng vỡ: {kq['canary']}")
    return kq["tho"]


@pytest.mark.parametrize("ma_anh,doc_type,truong", CA)
def test_diem_kiem(ket_qua_chay, ma_anh, doc_type, truong):
    """Một điểm kiểm: model trích trường này trên ảnh này có đúng không.

    "Đúng" gồm cả **im lặng đúng lúc**: với ảnh không đọc được (nhãn là None),
    hành vi đạt là KHÔNG trả giá trị — xem AC3.
    """
    kq = ket_qua_chay.get(ma_anh)
    assert kq is not None, f"không có kết quả cho ảnh {ma_anh}"
    assert kq.loi_he_thong is None, (
        f"lỗi hạ tầng khi xử lý {ma_anh}: {kq.loi_he_thong} — "
        "đây là lỗi của bộ đo, không phải của model")

    pq = so_khop_truong(doc_type, truong["ten_truong"],
                        truong["gia_tri"], kq.gia_tri(truong["ten_truong"]))

    ky_vong = ("KHÔNG trả giá trị (AC3)" if truong["gia_tri"] is None
               else f"trả đúng {truong['gia_tri']!r}")
    assert pq.la_dung, (
        f"kỳ vọng: {ky_vong}\n"
        f"model trả: {kq.gia_tri(truong['ten_truong'])!r} "
        f"(conf {kq.do_tin_cay(truong['ten_truong'])})\n"
        f"phán quyết: {pq.phan_quyet}"
        + (f" / {pq.loai_sai}" if pq.loai_sai else "")
        + (f"\nghi chú: {pq.ghi_chu}" if pq.ghi_chu else ""))


def test_so_luong_ca_dung_bang_so_diem_kiem_trong_bo_nhan():
    """Canh chính việc sinh ca: thiếu ca thì bộ test im lặng bỏ sót dữ liệu."""
    mong_doi = sum(len(r["fields"]) for r in doc_nhan())
    assert len(CA) == mong_doi, f"sinh {len(CA)} ca, bộ nhãn có {mong_doi} điểm kiểm"


def test_so_loi_da_biet_khop_voi_bao_cao_loi():
    """Mỗi điểm kiểm hỏng phải quy được về một mã lỗi trong LOI-PHAT-HIEN.md."""
    da_biet = _loi_da_biet()
    if not da_biet:
        pytest.skip("chưa chốt sổ lỗi đã biết")
    chua_phan_loai = [k for k, v in da_biet.items() if v["loi"] == "CHUA-PHAN-LOAI"]
    assert not chua_phan_loai, (
        "điểm kiểm hỏng chưa quy được về mã lỗi nào:\n  " + "\n  ".join(chua_phan_loai))
