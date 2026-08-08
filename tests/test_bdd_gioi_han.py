"""Bước Gherkin cho features/03-gioi-han-phep-do.feature.

Đây là bộ canh cho mục "ĐIỀU CHÚNG TÔI QUAN TÂM NHẤT" của đề: không cho phép báo
cáo công bố một con số mà không khai giới hạn của nó.

Chạy nhanh (~1 giây), không gọi OCR — nó đọc kết quả đo đã có.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

GOC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GOC))

from features.support.the_gioi import (TheGioi, doc_cham_diem,  # noqa: E402
                                       doc_so_gioi_han)

scenarios("../features/03-gioi-han-phep-do.feature")

MUC_DO_CHO_PHEP = {"chan_ket_luan", "thu_hep", "canh_bao"}

# Chỉ số được coi là "công bố": xuất hiện trong báo cáo 2 trang dưới dạng con số.
# Ánh xạ tên kỹ thuật -> cụm chữ trong báo cáo, để biết chỉ số nào đã công bố.
CHI_SO_CONG_BO = {
    "diem_tin_cay": "Điểm tin cậy (có trọng số)",
    "accuracy_truong_doc_duoc": "Điểm kiểm ĐẠT",
    "accuracy_truong_nghiem_trong": "trường nghiêm trọng",
    "ty_le_day_ve_oan": "bị trả về bắt dân nộp lại",
    "so_ro_ri_nghiem_trong": "rò rỉ nghiêm trọng",
    "accuracy_theo_truong": "Chữ viết tay 8–27",
    "accuracy_mau_01": "Chữ viết tay 8–27",
    "ty_le_khop_hai_luot": "đồng thuận",
    "ty_le_tu_dong": "tự động",
    "phan_bo_ky_vong": "vùng xám",
    "so_ho_so_can_bo_sung": "hồ sơ",
    "so_anh_doc_duoc_chu_nhung_khong_neo_duoc_truong": "không neo được trường",
    "hieu_chuan_conf_ece": "ECE 0,183",
    "auc_phan_biet_dung_sai": "AUC 0,839",
}


@pytest.fixture
def tg() -> TheGioi:
    return TheGioi()


# ---------------------------------------------------------------- Cho
@given("sổ giới hạn đã được nạp")
def _nap_so(tg: TheGioi):
    tg.dat("so", doc_so_gioi_han())


@given("kết quả đo mới nhất đã có")
def _nap_diem(tg: TheGioi):
    tg.dat("diem", doc_cham_diem())


@given(parsers.parse('giới hạn "{ma}"'))
def _mot_gioi_han(tg: TheGioi, ma: str):
    ds = [g for g in tg.lay("so")["gioi_han"] if g["ma"] == ma]
    assert ds, f"sổ giới hạn không có mục {ma}"
    tg.dat("gh", ds[0])


@given(parsers.parse('chỉ số nổi bật nhất của báo cáo là "{ten}"'))
def _chi_so_noi_bat(tg: TheGioi, ten: str):
    tg.dat("chi_so", ten)


# ---------------------------------------------------------------- Khi
@when("tôi đối chiếu các chỉ số công bố với sổ giới hạn")
def _doi_chieu(tg: TheGioi):
    bao_cao = (GOC / "BAO-CAO.md").read_text(encoding="utf-8")
    duoc_phu = {c for g in tg.lay("so")["gioi_han"] for c in g["chan_cac_chi_so"]}
    thieu = [ten for ten, dau_hieu in CHI_SO_CONG_BO.items()
             if dau_hieu in bao_cao and ten not in duoc_phu]
    tg.dat("thieu_gioi_han", thieu)


@when(parsers.parse('tôi lọc các giới hạn có trạng thái "{trang_thai}"'))
def _loc_trang_thai(tg: TheGioi, trang_thai: str):
    tg.dat("loc", [g for g in tg.lay("so")["gioi_han"]
                   if g["trang_thai"] == trang_thai])


@when(parsers.parse('tôi lọc các giới hạn mức "{muc}"'))
def _loc_muc(tg: TheGioi, muc: str):
    tg.dat("loc", [g for g in tg.lay("so")["gioi_han"] if g["muc_do"] == muc])


# ---------------------------------------------------------------- Thì
@then("không được có chỉ số nào không được giới hạn nào phủ")
def _moi_chi_so_co_gioi_han(tg: TheGioi):
    thieu = tg.lay("thieu_gioi_han")
    assert not thieu, (
        "Báo cáo công bố những chỉ số này mà sổ giới hạn không phủ:\n  "
        + "\n  ".join(thieu)
        + "\n\nĐề nói rõ điều họ quan tâm nhất là biết phép đo không chứng minh "
          "được gì. Công bố một con số mà không khai giới hạn của nó là đi ngược "
          "yêu cầu đó. Thêm mục vào gioi_han/so_gioi_han.json.")


@then("nó phải nêu được điều phép đo không chứng minh được")
def _co_khong_chung_minh(tg: TheGioi):
    g = tg.lay("gh")
    assert len(g.get("khong_chung_minh_duoc", "").strip()) >= 60, (
        f"{g['ma']}: phần 'không chứng minh được' quá sơ sài — nó là nội dung "
        "chính của mục này, không phải một dòng cho có")


@then("nó phải nêu được bằng chứng cần thu thập để gỡ")
def _co_bang_chung_de_go(tg: TheGioi):
    g = tg.lay("gh")
    assert len(g.get("bang_chung_de_go", "").strip()) >= 30, (
        f"{g['ma']}: không nêu được cần bằng chứng gì để gỡ. Một giới hạn không "
        "kèm đường thoát thì chỉ là lời than, không phải kế hoạch.")


@then("nó phải nêu được hậu quả nếu bỏ qua")
def _co_hau_qua(tg: TheGioi):
    g = tg.lay("gh")
    assert g.get("hau_qua_neu_bo_qua", "").strip(), (
        f"{g['ma']}: không nêu hậu quả nếu người đọc bỏ qua giới hạn này")


@then("mức độ của nó phải thuộc tập cho phép")
def _muc_do_hop_le(tg: TheGioi):
    g = tg.lay("gh")
    assert g["muc_do"] in MUC_DO_CHO_PHEP, (
        f"{g['ma']}: mức độ {g['muc_do']!r} không thuộc {sorted(MUC_DO_CHO_PHEP)}")


@then("mỗi giới hạn đó phải dẫn được bằng chứng cụ thể")
def _da_go_co_bang_chung(tg: TheGioi):
    thieu = [g["ma"] for g in tg.lay("loc")
             if len(g.get("bang_chung_da_go", "").strip()) < 40]
    assert not thieu, (
        f"tuyên bố đã gỡ giới hạn {thieu} mà không dẫn được bằng chứng — "
        "đó là tự xoá giới hạn, không phải gỡ nó")


@then("bằng chứng đó phải trỏ tới một tệp có thật trong repo")
def _bang_chung_tro_toi_tep_that(tg: TheGioi):
    hong = []
    for g in tg.lay("loc"):
        tep = re.findall(r"[\w/\-]+\.(?:csv|json|jsonl|md|py)", g.get("bang_chung_da_go", ""))
        if not tep:
            hong.append(f"{g['ma']}: bằng chứng không dẫn tệp nào")
            continue
        for t in tep:
            if not list(GOC.rglob(Path(t).name)):
                hong.append(f"{g['ma']}: dẫn tệp {t} nhưng không tìm thấy trong repo")
    assert not hong, "\n  ".join(hong)


@then("mỗi giới hạn đó phải được nhắc tới trong BAO-CAO.md")
def _chan_ket_luan_co_trong_bao_cao(tg: TheGioi):
    bao_cao = (GOC / "BAO-CAO.md").read_text(encoding="utf-8").lower()
    # Mỗi giới hạn khai một cụm từ neo; thiếu neo trong báo cáo là giới hạn bị giấu.
    # Neo là cụm từ ổn định nhất của mỗi giới hạn, KHÔNG phải nguyên câu — nguyên
    # câu thì sửa văn phong một chữ là cổng đỏ oan. Bản đầu neo vào "không của
    # tesseract" và đã đỏ oan đúng như vậy.
    NEO = {"GH-01": "mô phỏng", "GH-03": "bộ tách của tôi", "GH-09": "hoàn vốn"}
    thieu = [f"{g['ma']} ({g['tieu_de']})" for g in tg.lay("loc")
             if NEO.get(g["ma"], "").lower() not in bao_cao]
    assert not thieu, (
        "giới hạn mức chặn-kết-luận nhưng không xuất hiện trong báo cáo 2 trang:\n  "
        + "\n  ".join(thieu)
        + "\nGiới hạn nặng nhất mà nằm ngoài báo cáo thì người đọc không thấy.")


@then(parsers.parse('nó phải bị ít nhất một giới hạn mức "{muc}" phủ'))
def _chi_so_noi_bat_bi_phu(tg: TheGioi, muc: str):
    ten = tg.lay("chi_so")
    phu = [g["ma"] for g in tg.lay("so")["gioi_han"]
           if g["muc_do"] == muc and ten in g["chan_cac_chi_so"]]
    assert phu, f"{ten} không bị giới hạn mức {muc} nào phủ"


@then(parsers.parse("phải còn ít nhất {n:d} giới hạn đang mở"))
def _con_gioi_han_mo(tg: TheGioi, n: int):
    mo = [g for g in tg.lay("so")["gioi_han"] if g["trang_thai"] == "mo"]
    assert len(mo) >= n, (
        f"chỉ còn {len(mo)} giới hạn mở. Một bộ đo trên 33 ảnh mô phỏng mà tự "
        "khai gần như không còn giới hạn nào là dấu hiệu tự tin quá mức, không "
        "phải dấu hiệu trưởng thành.")


@then("điều đó được ghi thẳng vào báo cáo chứ không giấu trong phụ lục")
def _ghi_trong_bao_cao(tg: TheGioi):
    bao_cao = (GOC / "BAO-CAO.md").read_text(encoding="utf-8")
    assert "không chứng minh được gì" in bao_cao, (
        "BAO-CAO.md phải có mục nêu giới hạn của phép đo, không được đẩy hết "
        "sang PHU-LUC.md")
