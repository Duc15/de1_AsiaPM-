"""Bước Gherkin cho features/02-do-tin-cay.feature — góc nhìn nghiệp vụ.

Đọc kết quả đo đã có (`ket_qua/<model>/cham_diem.json`), không gọi lại OCR, nên
chạy ~1 giây. Muốn số mới thì chạy `python scripts/do_luong.py` trước.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from pytest_bdd import given, parsers, scenarios, then

GOC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GOC))

from bo_do.chay import doc_cau_hinh  # noqa: E402
from features.support.the_gioi import TheGioi, doc_cham_diem  # noqa: E402

scenarios("../features/02-do-tin-cay.feature")


@pytest.fixture
def tg() -> TheGioi:
    return TheGioi()


MODEL_DANG_KIEM_THU = "tesseract"   # đổi ở đây, không đổi trong feature


@given("kết quả đo mới nhất của model đang kiểm thử")
def _nap(tg: TheGioi):
    tg.dat("diem", doc_cham_diem(MODEL_DANG_KIEM_THU))
    tg.dat("cong", doc_cau_hinh()["cong_chat_luong"])


@given("kết quả đo của model đối chứng luôn từ chối")
def _nap_doi_chung(tg: TheGioi):
    thu_muc = GOC / "ket_qua" / "luon_tu_choi"
    if not (thu_muc / "cham_diem.json").exists():
        pytest.skip("chưa chạy `python scripts/do_luong.py --model luon_tu_choi`")
    tg.dat("doi_chung", doc_cham_diem("luon_tu_choi"))


def _tt(tg: TheGioi) -> dict:
    return tg.lay("diem")["tom_tat"]


# ------------------------------------------------------------ cổng nghiệp vụ
@then("điểm tin cậy phải đạt ít nhất ngưỡng nghiệp vụ")
def _diem_tin_cay(tg: TheGioi):
    thuc, can = _tt(tg)["diem_tin_cay"], tg.lay("cong")["diem_tin_cay_toi_thieu"]
    assert thuc >= can, (f"điểm tin cậy {thuc:.4f} < ngưỡng nghiệp vụ {can}. "
                         "Đây là KẾT LUẬN của bài, không phải test hỏng.")


@then("accuracy trường nghiêm trọng phải đạt ít nhất ngưỡng nghiệp vụ")
def _nghiem_trong(tg: TheGioi):
    thuc = _tt(tg)["accuracy_truong_nghiem_trong"]
    can = tg.lay("cong")["accuracy_truong_nghiem_trong_toi_thieu"]
    assert thuc >= can, f"accuracy trường nghiêm trọng {thuc:.4f} < {can}"


@then("số trường nghiêm trọng lọt cổng HITL không được vượt mức cho phép")
def _ro_ri(tg: TheGioi):
    thuc = len(tg.lay("diem")["cong_hitl"]["ro_ri_nghiem_trong"])
    can = tg.lay("cong")["so_ro_ri_nghiem_trong_toi_da"]
    assert thuc <= can, f"{thuc} trường nghiêm trọng SAI lọt cổng, mức cho phép {can}"


# ------------------------------------------------------------ AC3
@then("tỉ lệ bịa dữ liệu trên ảnh không đọc được phải bằng 0")
def _khong_bia(tg: TheGioi):
    assert _tt(tg)["ac3_so_truong_bia"] == 0, "AC3 là ràng buộc pháp lý, không có biên độ"


@then("tỉ lệ từ chối đúng phải bằng 100 phần trăm")
def _tu_choi_dung(tg: TheGioi):
    assert _tt(tg)["ac3_ty_le_tu_choi_dung"] == 1.0


@then("không được có lỗi hạ tầng nào trong lượt đo")
def _khong_loi_ha_tang(tg: TheGioi):
    assert _tt(tg)["so_truong_loi_ha_tang"] == 0, tg.lay("diem")["loi_ha_tang"]


# ------------------------------------------------------------ bậc chất lượng
@then(parsers.parse('ở bậc ảnh "{bac}" điểm tin cậy phải nằm quanh {ky_vong:f} phần trăm'))
def _theo_bac(tg: TheGioi, bac: str, ky_vong: float):
    theo_bac = tg.lay("diem")["theo_bac_chat_luong"]
    assert bac in theo_bac, f"lượt đo không có bậc {bac}"
    thuc = theo_bac[bac]["diem_tin_cay"] * 100
    assert abs(thuc - ky_vong) <= 1.0, (
        f"bậc {bac}: đo được {thuc:.1f} %, mô tả trong feature nói {ky_vong} % — "
        "một trong hai đã lạc hậu")


# ------------------------------------------------------------ mức hồ sơ
@then("tỉ lệ hồ sơ người đọc được mà vẫn bị trả về phải được báo cáo")
def _co_muc_ho_so(tg: TheGioi):
    hs = tg.lay("diem").get("muc_ho_so")
    assert hs and hs.get("ty_le_day_ve_oan") is not None, (
        "thiếu chỉ số mức hồ sơ — trung bình theo trường che mất tác động thật")
    tg.dat("hs", hs)


@then("con số đó phải tệ hơn con số accuracy mức trường")
def _muc_ho_so_te_hon(tg: TheGioi):
    hs, t = tg.lay("hs"), _tt(tg)
    di_tiep = hs["ty_le_di_tiep_duoc"]
    assert di_tiep < 1.0, "mức hồ sơ không nói thêm được gì"
    assert hs["ty_le_day_ve_oan"] > 0, (
        "nếu không hồ sơ nào bị trả về oan thì bỏ kịch bản này đi")
    tg.dat("ghi_chu", f"mức trường {t['accuracy_truong_doc_duoc']:.1%} · "
                      f"mức hồ sơ đi tiếp {di_tiep:.1%}")


# ------------------------------------------------------------ ngưỡng HITL
@then(parsers.parse("ở ngưỡng {nguong:f} phải còn {ro_ri:d} trường nghiêm trọng lọt cổng"))
def _quet_nguong(tg: TheGioi, nguong: float, ro_ri: int):
    quet = {round(x["nguong"], 2): x for x in tg.lay("diem")["quet_nguong_hitl"]}
    assert round(nguong, 2) in quet, f"bảng quét ngưỡng không có mốc {nguong}"
    thuc = quet[round(nguong, 2)]["so_ro_ri_nghiem_trong"]
    assert thuc == ro_ri, f"ngưỡng {nguong}: rò rỉ {thuc}, feature nói {ro_ri}"


# ------------------------------------------------------------ đối chứng
@then("điểm tin cậy của nó phải thấp hơn model đang đo")
def _doi_chung_thap_hon(tg: TheGioi):
    dc = tg.lay("doi_chung")["tom_tat"]["diem_tin_cay"]
    thuc = _tt(tg)["diem_tin_cay"]
    assert dc < thuc, (
        f"model không bao giờ trả gì lại được {dc:.4f} ≥ {thuc:.4f} của model thật — "
        "bộ đo đang bị lừa, phải sửa bộ đo chứ không phải mừng")


@then("accuracy trên trường người đọc được của nó phải bằng 0")
def _doi_chung_bang_khong(tg: TheGioi):
    assert tg.lay("doi_chung")["tom_tat"]["accuracy_truong_doc_duoc"] == 0.0
