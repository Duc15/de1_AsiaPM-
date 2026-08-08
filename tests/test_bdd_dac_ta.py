"""Bước Gherkin cho features/01-dac-ta-trich-xuat.feature (AC1/AC2/AC3).

Không dòng nào ở đây nhắc tới Tesseract, pytesseract hay đường dẫn ảnh — mọi thứ
đi qua `doi_tuong.HoSoGiayTo`. Đó là điều kiện để bài 2 (web) và mobile dùng lại
cùng bộ bước: chúng chỉ cần cắm một lớp đối tượng khác vào fixture `doi_tuong`.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

GOC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GOC))

from bo_do.schema import LOAI_GIAY_TO  # noqa: E402
from bo_do.so_bang_chung import CAN_BO_SUNG, DU_DIEU_KIEN  # noqa: E402
from doi_tuong.ho_so_giay_to import HoSoGiayTo  # noqa: E402
from features.support.the_gioi import TheGioi  # noqa: E402

scenarios("../features/01-dac-ta-trich-xuat.feature")

NGUON_HOP_LE = {"ocr", "qr", "mrz", "llm_repair", "cross_validate", "human"}


@pytest.fixture(scope="module")
def doi_tuong() -> HoSoGiayTo:
    """Đổi dòng này sang TrangTiepNhanHoSo(page) là cả file chạy cho web."""
    return HoSoGiayTo()


@pytest.fixture
def tg(doi_tuong) -> TheGioi:
    return TheGioi(doi_tuong=doi_tuong)


# ============================================================== Cho
@given("hạ tầng trích xuất đã qua canary")
def _canary(tg: TheGioi):
    ok, ghi_chu = tg.doi_tuong.tu_kiem_tra()
    assert ok, (f"canary vỡ: {ghi_chu}. Đây là lỗi hạ tầng — mọi kết quả sau đó "
                "vô nghĩa, nên dừng chứ không báo 0 %.")


@given(parsers.parse('một ảnh giấy tờ hợp lệ, đọc được "{ma}"'))
@given(parsers.parse('một ảnh mờ, lỗi, không đọc được "{ma}"'))
@given(parsers.parse('một ảnh không tồn tại "{ma}"'))
def _mo_ho_so(tg: TheGioi, ma: str):
    tg.dat("ma_anh", ma)
    tg.doi_tuong.mo(ma)


@given(parsers.parse("ngưỡng tin cậy cấu hình là {nguong:f}"))
def _dat_nguong(tg: TheGioi, nguong: float):
    tg.doi_tuong.doi_nguong(nguong)


# ============================================================== Khi
@when("worker trích xuất chạy")
def _chay(tg: TheGioi):
    tg.ket_qua = tg.doi_tuong.xu_ly()


@when(parsers.parse('ngưỡng được đặt đúng bằng điểm tin cậy của trường "{ten}"'))
def _nguong_bang_conf(tg: TheGioi, ten: str):
    conf = tg.ket_qua.lay(ten).tin_cay
    assert conf is not None, f"trường {ten} không có điểm tin cậy để dựng ca biên"
    tg.doi_tuong.doi_nguong(conf)
    tg.ket_qua = tg.doi_tuong.xu_ly()


# ============================================================== Thì — AC1
@then("mọi trường trả về phải thuộc schema chuẩn của loại giấy tờ đó")
def _dung_schema(tg: TheGioi):
    ma = tg.lay("ma_anh")
    loai = "cccd" if ma.startswith("cccd") else "mau_01"
    hop_le = {t.ten for t in LOAI_GIAY_TO[loai].truong}
    la = [t for t in tg.ket_qua.truong if t not in hop_le]
    assert not la, f"trường lạ ngoài schema: {la}"


@then("mỗi trường phải kèm một điểm tin cậy trong khoảng 0 đến 1")
def _co_conf(tg: TheGioi):
    thieu = [f"{t.ten}={t.tin_cay}" for t in tg.ket_qua.truong.values()
             if t.tin_cay is None or not (0.0 <= t.tin_cay <= 1.0)]
    assert not thieu, ("AC1 đòi MỖI trường kèm một điểm tin cậy; thiếu thì cổng "
                       f"HITL ở AC2 không phân loại được nó: {thieu}")


@then("nguồn của mỗi trường phải thuộc tập đặc tả cho phép")
def _nguon_hop_le(tg: TheGioi):
    la = [f"{t.ten}={t.nguon!r}" for t in tg.ket_qua.truong.values()
          if t.nguon not in NGUON_HOP_LE]
    assert not la, f"nguồn ngoài tập {sorted(NGUON_HOP_LE)}: {la}"


@then("ảnh gốc phải được liên kết trong sổ bằng chứng")
def _lien_ket_anh(tg: TheGioi):
    tep = GOC / "data" / "anh" / f"{tg.lay('ma_anh')}.jpg"
    assert tep.exists(), f"không truy ngược được về ảnh gốc: {tep}"
    assert hashlib.sha256(tep.read_bytes()).hexdigest(), "không băm được ảnh gốc"


@then("nhật ký worker phải được ghi")
def _nhat_ky(tg: TheGioi):
    assert tg.ket_qua.thoi_gian_ms >= 0, "không ghi được thời gian xử lý"
    assert tg.ket_qua.trang_thai, "không ghi được trạng thái hồ sơ"


# ============================================================== Thì — AC2
@then("mọi trường có điểm tin cậy dưới ngưỡng phải bị đánh dấu cần người xác nhận")
def _duoi_nguong_bi_gan_co(tg: TheGioi):
    nguong = tg.doi_tuong.nguong_hitl
    sai = [f"{t.ten} conf={t.tin_cay}" for t in tg.ket_qua.truong.values()
           if t.tin_cay is not None and t.tin_cay < nguong and not t.can_nguoi_xac_nhan]
    assert not sai, f"dưới ngưỡng {nguong} mà không gắn cờ: {sai}"


@then("không trường nào từ ngưỡng trở lên bị đánh dấu thừa")
def _tren_nguong_khong_gan_co(tg: TheGioi):
    nguong = tg.doi_tuong.nguong_hitl
    sai = [f"{t.ten} conf={t.tin_cay}" for t in tg.ket_qua.truong.values()
           if t.tin_cay is not None and t.tin_cay >= nguong and t.can_nguoi_xac_nhan]
    assert not sai, ("gắn cờ thừa cũng là lỗi — nó đẩy việc sang người duyệt vô "
                     f"cớ: {sai}")


@then(parsers.parse('trường "{ten}" không bị đánh dấu cần người xác nhận'))
def _truong_khong_bi_gan_co(tg: TheGioi, ten: str):
    t = tg.ket_qua.lay(ten)
    assert t.can_nguoi_xac_nhan is False, (
        f"conf {t.tin_cay} đúng bằng ngưỡng {tg.doi_tuong.nguong_hitl} mà vẫn bị "
        'gắn cờ — sai quy ước "DƯỚI ngưỡng" của AC2')


@then(parsers.parse("số trường bị đánh dấu cần người xác nhận phải là {n:d}"))
def _dem_gan_co(tg: TheGioi, n: int):
    thuc = sum(1 for t in tg.ket_qua.truong.values() if t.can_nguoi_xac_nhan)
    assert thuc == n, (f"ngưỡng {tg.doi_tuong.nguong_hitl} gắn cờ {thuc} trường, "
                       f"cần {n} — ngưỡng có vẻ bị hard-code")


# ============================================================== Thì — AC3
@then("hệ thống KHÔNG được trả về bất kỳ giá trị nào")
def _khong_bia(tg: TheGioi):
    bia = [f"{t.ten}={t.gia_tri!r}" for t in tg.ket_qua.truong.values() if t.co_gia_tri]
    assert not bia, ("AC3 bị vi phạm — bịa giá trị trên ảnh không đọc được: "
                     f"{bia}")


@then(parsers.parse('hồ sơ phải mang trạng thái "{trang_thai}"'))
def _trang_thai_ho_so(tg: TheGioi, trang_thai: str):
    assert tg.ket_qua.trang_thai == trang_thai, (
        f"trạng thái là {tg.ket_qua.trang_thai!r}, cần {trang_thai!r}")


@then("trạng thái đó phải kèm lý do bằng tiếng người")
def _co_ly_do(tg: TheGioi):
    assert (tg.ket_qua.ly_do or "").strip(), (
        "hồ sơ cần bổ sung mà không có lý do — người duyệt không biết bảo dân "
        "nộp lại cái gì")


@then("nếu hồ sơ đủ điều kiện xử lý thì mọi trường nghiêm trọng phải có giá trị")
def _du_dieu_kien_du_truong(tg: TheGioi):
    if tg.ket_qua.trang_thai != DU_DIEU_KIEN:
        return
    ma = tg.lay("ma_anh")
    loai = "cccd" if ma.startswith("cccd") else "mau_01"
    thieu = [t.ten for t in LOAI_GIAY_TO[loai].truong
             if t.muc_do == "nghiem_trong" and not tg.ket_qua.lay(t.ten).co_gia_tri]
    assert not thieu, f"cho hồ sơ đi tiếp nhưng thiếu trường bắt buộc: {thieu}"


# ============================================================== Thì — hạ tầng
@then("kết quả phải mang lỗi hạ tầng")
def _co_loi_ha_tang(tg: TheGioi):
    assert tg.ket_qua.loi_he_thong is not None, (
        "ảnh không tồn tại mà không báo lỗi hạ tầng — bộ đo sẽ ghi thành 'model "
        "bỏ sót' và đổ lỗi cho model")


@then("không được coi đó là hành vi từ chối theo AC3")
def _khong_nham_voi_tu_choi(tg: TheGioi):
    assert tg.ket_qua.trang_thai == CAN_BO_SUNG
    assert "không xử lý được ảnh" in (tg.ket_qua.ly_do or ""), (
        "lý do phải chỉ rõ đây là lỗi hạ tầng, không phải model đọc không ra")
