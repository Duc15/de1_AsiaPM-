"""Kiểm thử theo ĐẶC TẢ — truy vết 1:1 tới AC1, AC2, AC3 của US-M1-EXTRACT-001.

Khác với `test_hoi_quy.py` (canh chất lượng, có ngưỡng và biên độ), file này kiểm
**hợp đồng hành vi**: đúng/sai nhị phân, không có biên độ. Một AC hoặc được thoả
hoặc không.

Ma trận truy vết đầy đủ nằm ở KE-HOACH-KIEM-THU.md; ID ca kiểm thử ở đây trùng
với ID trong tài liệu đó.

  AC1 (happy path)  TC-AC1-01 .. TC-AC1-05
  AC2 (edge)        TC-AC2-01 .. TC-AC2-04
  AC3 (negative)    TC-AC3-01 .. TC-AC3-04
"""

from __future__ import annotations

import re
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

from bo_do.chay import do, doc_cau_hinh, doc_nhan  # noqa: E402
from bo_do.schema import LOAI_GIAY_TO  # noqa: E402
from bo_do.so_bang_chung import (CAN_BO_SUNG, DU_DIEU_KIEN, ghi_nhat_ky_worker,  # noqa: E402
                                 lap_so_bang_chung)

NGUON_HOP_LE = {"ocr", "qr", "mrz", "llm_repair", "cross_validate", "human"}


@pytest.fixture(scope="module")
def chay_that():
    """Chạy model một lần cho cả module. Nhãn chỉ dùng để biết ảnh nào đọc được."""
    kq = do("tesseract", lap=1, in_tien_do=False)
    if not kq["canary_ok"]:
        pytest.fail(f"Canary hạ tầng vỡ: {kq['canary']} — không kiểm thử AC được")
    kq["ban_ghi"] = doc_nhan()
    kq["nguong"] = doc_cau_hinh()["nguong_hitl"]
    kq["so"] = lap_so_bang_chung(kq["ban_ghi"], kq["tho"], kq["meta"], kq["nguong"])
    return kq


def _theo_id(so: dict) -> dict[str, dict]:
    return {h["id"]: h for h in so["ho_so"]}


def _anh_doc_duoc(ban_ghi: list[dict]) -> list[str]:
    return [r["id"] for r in ban_ghi if r["anh_doc_duoc"]]


def _anh_khong_doc_duoc(ban_ghi: list[dict]) -> list[str]:
    return [r["id"] for r in ban_ghi if not r["anh_doc_duoc"]]


# ===========================================================================
# AC1 — Given ảnh giấy tờ hợp lệ, đọc được / When worker trích xuất chạy /
# Then trường được điền vào schema chuẩn, mỗi trường kèm điểm tin cậy, ảnh gốc
# được liên kết trong sổ bằng chứng, nhật ký worker được ghi.
# ===========================================================================
def test_TC_AC1_01_truong_dung_schema_chuan(chay_that):
    """Mọi trường model trả về phải thuộc schema của đúng loại giấy tờ đó."""
    sai = []
    for h in chay_that["so"]["ho_so"]:
        hop_le = {t.ten for t in LOAI_GIAY_TO[h["doc_type"]].truong}
        for f in h["fields"]:
            if f["ten_truong"] not in hop_le:
                sai.append(f"{h['id']}: trường lạ {f['ten_truong']!r}")
    assert not sai, "\n".join(sai)


def test_TC_AC1_02_moi_truong_deu_co_diem_tin_cay(chay_that):
    """AC1 nói "mỗi trường kèm một điểm tin cậy" — không có ngoại lệ.

    Trường không có confidence thì cổng HITL ở AC2 không phân loại được nó.
    """
    sai = []
    for h in chay_that["so"]["ho_so"]:
        for f in h["fields"]:
            c = f["confidence"]
            if c is None:
                sai.append(f"{h['id']}.{f['ten_truong']}: thiếu confidence")
            elif not (0.0 <= c <= 1.0):
                sai.append(f"{h['id']}.{f['ten_truong']}: confidence={c} ngoài [0,1]")
    assert not sai, "\n".join(sai)


def test_TC_AC1_03_nguon_thuoc_tap_dac_ta(chay_that):
    """`nguon` phải thuộc tập đề liệt kê ở mục 03, không được tự chế giá trị mới."""
    sai = [f"{h['id']}.{f['ten_truong']}: nguon={f['nguon']!r}"
           for h in chay_that["so"]["ho_so"] for f in h["fields"]
           if f["nguon"] not in NGUON_HOP_LE]
    assert not sai, "\n".join(sai) + f"\nTập hợp lệ: {sorted(NGUON_HOP_LE)}"


def test_TC_AC1_04_anh_goc_duoc_lien_ket_trong_so_bang_chung(chay_that):
    """Mỗi hồ sơ phải trỏ ngược được về đúng file ảnh đã sinh ra nó.

    Kiểm cả sha256 chứ không chỉ đường dẫn: đường dẫn có thể trỏ sang ảnh khác
    sau một lần sinh lại dữ liệu, lúc đó sổ bằng chứng nói dối mà không ai biết.
    """
    import hashlib
    thieu, lech = [], []
    for h in chay_that["so"]["ho_so"]:
        a = h.get("anh_goc") or {}
        tep = GOC / a.get("duong_dan", "")
        if not a.get("duong_dan") or not a.get("sha256") or not tep.exists():
            thieu.append(h["id"])
            continue
        if hashlib.sha256(tep.read_bytes()).hexdigest() != a["sha256"]:
            lech.append(h["id"])
    assert not thieu, f"hồ sơ không liên kết được ảnh gốc: {thieu}"
    assert not lech, f"sha256 trong sổ không khớp ảnh trên đĩa: {lech}"


def test_TC_AC1_05_nhat_ky_worker_duoc_ghi(chay_that, tmp_path):
    """Nhật ký worker phải có, và phải có đúng một dòng cho mỗi ảnh đã xử lý."""
    tep = tmp_path / "nhat_ky_worker.log"
    ghi_nhat_ky_worker(chay_that["so"], tep)
    assert tep.exists(), "không ghi được nhật ký worker"
    dong = [d for d in tep.read_text(encoding="utf-8").splitlines()
            if d.strip() and not d.startswith("#")]
    assert len(dong) == len(chay_that["so"]["ho_so"]), (
        f"nhật ký có {len(dong)} dòng, cần {len(chay_that['so']['ho_so'])}")
    for d in dong:
        assert d.count("|") >= 6, f"dòng nhật ký thiếu cột: {d!r}"


# ===========================================================================
# AC2 — Given trường có điểm tin cậy dưới ngưỡng cấu hình / When kết quả được
# lưu / Then trường bị đánh dấu cần người xác nhận.
# ===========================================================================
def test_TC_AC2_01_truong_duoi_nguong_bi_danh_dau(chay_that):
    sai = [f"{h['id']}.{f['ten_truong']} conf={f['confidence']}"
           for h in chay_that["so"]["ho_so"] for f in h["fields"]
           if f["confidence"] is not None and f["confidence"] < chay_that["nguong"]
           and not f["can_nguoi_xac_nhan"]]
    assert not sai, "dưới ngưỡng nhưng KHÔNG bị gắn cờ:\n" + "\n".join(sai)


def test_TC_AC2_02_truong_tren_nguong_khong_bi_danh_dau(chay_that):
    """Gắn cờ thừa cũng là lỗi: nó đẩy việc sang người duyệt vô cớ."""
    sai = [f"{h['id']}.{f['ten_truong']} conf={f['confidence']}"
           for h in chay_that["so"]["ho_so"] for f in h["fields"]
           if f["confidence"] is not None and f["confidence"] >= chay_that["nguong"]
           and f["can_nguoi_xac_nhan"]]
    assert not sai, "trên ngưỡng nhưng vẫn bị gắn cờ:\n" + "\n".join(sai)


def test_TC_AC2_03_ca_bien_conf_dung_bang_nguong(chay_that):
    """Ranh giới: AC2 nói "DƯỚI ngưỡng", nên conf == ngưỡng thì KHÔNG gắn cờ.

    Dựng ngưỡng bằng đúng một giá trị conf có thật trong lần chạy này, để ca biên
    không phải giả định mà là dữ liệu thật.
    """
    conf_co_that = sorted({f["confidence"] for h in chay_that["so"]["ho_so"]
                           for f in h["fields"] if f["confidence"] is not None})
    if not conf_co_that:
        pytest.skip("lần chạy này không có trường nào mang confidence")
    bien = conf_co_that[len(conf_co_that) // 2]
    so = lap_so_bang_chung(chay_that["ban_ghi"], chay_that["tho"],
                           chay_that["meta"], bien)
    tai_bien = [f for h in so["ho_so"] for f in h["fields"]
                if f["confidence"] == bien]
    assert tai_bien, "không dựng được ca biên"
    assert not any(f["can_nguoi_xac_nhan"] for f in tai_bien), (
        f"conf == ngưỡng ({bien}) mà vẫn bị gắn cờ — sai quy ước 'dưới ngưỡng'")


def test_TC_AC2_04_nguong_thuc_su_cau_hinh_duoc(chay_that):
    """AC2 nói "ngưỡng cấu hình". Đổi ngưỡng phải đổi tập trường bị gắn cờ.

    Ngưỡng bị hard-code là lỗi im lặng: hệ thống vẫn chạy, bảng đánh đổi ngưỡng
    trong báo cáo trở thành vô nghĩa, và không ai phát hiện cho tới lúc vận hành.
    """
    dem = {}
    for nguong in (0.0, 0.5, 1.01):
        so = lap_so_bang_chung(chay_that["ban_ghi"], chay_that["tho"],
                               chay_that["meta"], nguong)
        dem[nguong] = sum(h["so_truong_can_nguoi_xac_nhan"] for h in so["ho_so"])
    assert dem[0.0] == 0, f"ngưỡng 0.0 lẽ ra không gắn cờ trường nào, thực tế {dem[0.0]}"
    assert dem[0.0] < dem[0.5] < dem[1.01], f"ngưỡng không có tác dụng: {dem}"


# ===========================================================================
# AC3 — Given ảnh mờ/lỗi/không đọc được / When worker chạy / Then hệ thống KHÔNG
# bịa dữ liệu; hồ sơ được đặt trạng thái "cần bổ sung" kèm lý do.
# ===========================================================================
def test_TC_AC3_01_khong_bia_du_lieu_tren_anh_khong_doc_duoc(chay_that):
    """Ràng buộc cứng nhất của cả đặc tả. Không có biên độ tha thứ."""
    bia = []
    theo_id = _theo_id(chay_that["so"])
    for ma in _anh_khong_doc_duoc(chay_that["ban_ghi"]):
        for f in theo_id[ma]["fields"]:
            if f["gia_tri"] not in (None, ""):
                bia.append(f"{ma}.{f['ten_truong']} = {f['gia_tri']!r} "
                           f"(conf {f['confidence']})")
    assert not bia, ("AC3 bị vi phạm — model bịa giá trị trên ảnh mà cả hai lượt "
                     "gán nhãn đều không đọc được:\n" + "\n".join(bia))


def test_TC_AC3_02_ho_so_khong_doc_duoc_co_trang_thai_can_bo_sung(chay_that):
    theo_id = _theo_id(chay_that["so"])
    sai = [f"{ma}: trạng thái={theo_id[ma]['trang_thai_ho_so']}"
           for ma in _anh_khong_doc_duoc(chay_that["ban_ghi"])
           if theo_id[ma]["trang_thai_ho_so"] != CAN_BO_SUNG]
    assert not sai, "\n".join(sai)


def test_TC_AC3_03_moi_ho_so_can_bo_sung_deu_co_ly_do(chay_that):
    """"kèm lý do" — lý do rỗng thì người duyệt không biết bảo dân nộp lại cái gì."""
    sai = [h["id"] for h in chay_that["so"]["ho_so"]
           if h["trang_thai_ho_so"] == CAN_BO_SUNG
           and not (h["ly_do"] or "").strip()]
    assert not sai, f"hồ sơ cần bổ sung mà không có lý do: {sai}"


def test_TC_AC3_04_ho_so_du_dieu_kien_phai_co_du_truong_nghiem_trong(chay_that):
    """Mặt trái của AC3: đã cho hồ sơ đi tiếp thì không được thiếu trường bắt buộc."""
    sai = []
    for h in chay_that["so"]["ho_so"]:
        if h["trang_thai_ho_so"] != DU_DIEU_KIEN:
            continue
        co = {f["ten_truong"] for f in h["fields"] if f["gia_tri"]}
        for t in LOAI_GIAY_TO[h["doc_type"]].truong:
            if t.muc_do == "nghiem_trong" and t.ten not in co:
                sai.append(f"{h['id']}: đủ điều kiện xử lý nhưng thiếu {t.ten}")
    assert not sai, "\n".join(sai)


# ===========================================================================
# Bao phủ — kiểm chính bộ kiểm thử, không kiểm model.
# ===========================================================================
def test_TC_BAO_PHU_01_moi_AC_deu_co_it_nhat_mot_ca(chay_that):
    """Đọc file này và đếm ca theo từng AC. Thêm AC mà quên viết test thì đỏ ở đây."""
    nguon = Path(__file__).read_text(encoding="utf-8")
    for ac in ("AC1", "AC2", "AC3"):
        ca = re.findall(rf"def test_TC_{ac}_\d+", nguon)
        assert len(ca) >= 2, f"{ac} chỉ có {len(ca)} ca kiểm thử"


def test_TC_BAO_PHU_02_bo_du_lieu_phu_ca_ba_nhanh_AC(chay_that):
    """AC1 cần ảnh đọc được, AC3 cần ảnh không đọc được. Thiếu một nhánh thì có
    test cũng không kiểm được gì."""
    ban_ghi = chay_that["ban_ghi"]
    assert len(_anh_doc_duoc(ban_ghi)) >= 20, "quá ít ảnh đọc được cho nhánh AC1"
    assert len(_anh_khong_doc_duoc(ban_ghi)) >= 3, "quá ít ảnh cho nhánh AC3"
    bac = {r["muc_chat_luong"] for r in ban_ghi}
    assert len(bac) >= 5, f"chỉ phủ {len(bac)} bậc chất lượng ảnh"
