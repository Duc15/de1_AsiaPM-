"""Bộ test tự động (Bước 5). Chạy: pytest -v

Chạy được lặp lại, dùng nhãn có sẵn làm căn cứ, và tự nói tốt lên / xấu đi /
không đổi. Toàn bộ lượt đo chạy MỘT lần cho cả file (fixture scope=session), vì
gọi OCR 33 ảnh mất khoảng 40 giây.

Ba nhóm test, tương ứng ba tầng ở bo_do/hoi_quy.py:
  test_bat_bien_*   không có biên độ tha thứ
  test_cong_*       ngưỡng nghiệp vụ tuyệt đối
  test_khong_tut_*  so với baseline, có biên = max(3·sigma, biên tối thiểu)

Và một nhóm riêng canh chính THƯỚC ĐO, không canh model: nếu bộ nhãn hỏng thì mọi
test còn lại đều vô nghĩa.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GOC))

# Console Windows mặc định là cp1252; báo lỗi tiếng Việt sẽ vỡ khi in.
for _luong in (sys.stdout, sys.stderr, sys.__stdout__, sys.__stderr__):
    try:
        _luong.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except (AttributeError, ValueError):
        pass

from bo_do.chay import do, doc_cau_hinh, doc_nhan  # noqa: E402
from bo_do.hoi_quy import danh_gia, doc_baseline  # noqa: E402
from bo_do.schema import LOAI_GIAY_TO  # noqa: E402


@pytest.fixture(scope="session")
def lan_do():
    kq = do("tesseract", lap=1, in_tien_do=False)
    cong = doc_cau_hinh()["cong_chat_luong"]
    kq["phan_quyet"] = danh_gia(kq["diem"], kq["canary_ok"], cong, doc_baseline())
    return kq


# --------------------------------------------------------------------------
# Canh thước đo trước, canh model sau.
# --------------------------------------------------------------------------
def test_bo_nhan_du_va_dung_schema():
    ban_ghi = doc_nhan()
    assert len(ban_ghi) >= 30, "đề yêu cầu tối thiểu 30 ảnh"
    for r in ban_ghi:
        ten_schema = {t.ten for t in LOAI_GIAY_TO[r["doc_type"]].truong}
        ten_nhan = {f["ten_truong"] for f in r["fields"]}
        assert ten_nhan == ten_schema, f"{r['id']} lệch schema: {ten_nhan ^ ten_schema}"
        for f in r["fields"]:
            assert f["ky_vong"] in ("phai_trich_dung", "phai_tu_choi", "vung_xam")
            if f["ky_vong"] == "phai_tu_choi":
                assert f["gia_tri"] is None, \
                    f"{r['id']}.{f['ten_truong']}: ảnh không đọc được thì nhãn phải là null"


def test_do_dong_thuan_hai_luot_con_dat():
    """Nhãn là thước đo duy nhất. Thước lệch thì mọi con số phía sau lệch theo."""
    tep = GOC / "data" / "nhan" / "do_dong_thuan.json"
    assert tep.exists(), "chưa chạy scripts/gan_nhan.py"
    d = json.loads(tep.read_text(encoding="utf-8"))
    assert d["so_truong_so_sanh_duoc"] >= 30, "lấy mẫu lượt 2 quá mỏng để nói gì"
    assert d["ty_le_khop"] >= 0.95, f"hai lượt gán nhãn lệch nhau: {d['cac_cho_lech']}"


def test_phu_du_cac_bac_chat_luong():
    ban_ghi = doc_nhan()
    bac = {r["muc_chat_luong"] for r in ban_ghi}
    assert {"sach", "nhe", "trung_binh", "nang", "khong_doc_duoc"} <= bac
    loai = {r["doc_type"] for r in ban_ghi}
    assert loai == set(LOAI_GIAY_TO), "phải phủ cả hai loại giấy tờ"


# --------------------------------------------------------------------------
# Tầng 1 — bất biến
# --------------------------------------------------------------------------
def test_bat_bien_canary_ha_tang(lan_do):
    assert lan_do["canary_ok"], (
        f"Canary vỡ: {lan_do['canary']}. Đây là lỗi hạ tầng, không phải lỗi model — "
        "mọi con số trong lần chạy này đều không dùng được.")


def test_bat_bien_khong_bia_du_lieu_ac3(lan_do):
    t = lan_do["diem"]["tom_tat"]
    assert t["ac3_so_truong_bia"] == 0, (
        "AC3 bị vi phạm: model trả ra giá trị trên ảnh mà cả hai lượt gán nhãn đều "
        "không đọc được. Đây là ràng buộc pháp lý, không có biên độ tha thứ.")


def test_bat_bien_khong_co_loi_ha_tang(lan_do):
    t = lan_do["diem"]["tom_tat"]
    assert t["so_truong_loi_ha_tang"] == 0, lan_do["diem"]["loi_ha_tang"]


# --------------------------------------------------------------------------
# Tầng 2 — cổng tuyệt đối và biên độ so với baseline
# --------------------------------------------------------------------------
@pytest.mark.cong_nghiep_vu
def test_cong_chat_luong_tuyet_doi(lan_do):
    """Ngưỡng nghiệp vụ NƠXH, đặt trong cau_hinh.json.

    Test này ĐANG ĐỎ với Tesseract, và đó là kết luận của bài chứ không phải test
    hỏng: model này chưa đủ để dùng cho hệ thống ở mục 01. Xem BAO-CAO.md.

    Muốn chạy riêng phần canh hồi quy (bỏ cổng nghiệp vụ):
        pytest -m "not cong_nghiep_vu"
    """
    pq = lan_do["phan_quyet"]
    loi_cong = [l for l in pq["loi"] if l.startswith("CỔNG")]
    assert not loi_cong, (
        "Model chưa qua cổng nghiệp vụ (đây là kết luận, không phải test hỏng):\n  "
        + "\n  ".join(loi_cong))


@pytest.mark.skipif(doc_baseline() is None, reason="chưa chốt baseline")
def test_khong_tut_so_voi_baseline(lan_do):
    pq = lan_do["phan_quyet"]
    loi_bien = [l for l in pq["loi"] if l.startswith("BIÊN ĐỘ") or "dấu vân tay" in l]
    assert not loi_bien, "\n".join(loi_bien)


@pytest.mark.skipif(doc_baseline() is None, reason="chưa chốt baseline")
def test_khong_co_truong_tu_dung_thanh_sai(lan_do):
    """Tầng 3 — chỉ số tổng che được việc 5 trường tốt lên, 5 trường xấu đi."""
    pq = lan_do["phan_quyet"]
    assert not pq["ca_xau_di"], (
        "Có trường đang đúng mà thành sai:\n  " + "\n  ".join(pq["ca_xau_di"]))


# --------------------------------------------------------------------------
# Kết luận tổng, in ra để CI đọc được bằng mắt.
# --------------------------------------------------------------------------
def test_in_xu_huong(lan_do, capsys):
    pq = lan_do["phan_quyet"]
    with capsys.disabled():
        print(f"\n>>> XU HƯỚNG SO VỚI BASELINE: {pq['xu_huong']}")
        for k, v in pq["so_sanh_baseline"].items():
            print(f"    {k:34s} {v['baseline']} → {v['lan_nay']} "
                  f"(lệch {v['lech']:+.4f}, biên {v['bien_cho_phep']})")
        for c in pq["canh_bao"]:
            print(f"    CẢNH BÁO: {c}")
    assert pq["xu_huong"] in ("TỐT LÊN", "XẤU ĐI", "KHÔNG ĐỔI")
