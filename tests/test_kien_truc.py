"""Ràng buộc KIẾN TRÚC — canh cho lớp đối tượng không rữa khi thêm web và mobile.

Ba tầng (features → bước Gherkin → lớp đối tượng) chỉ có giá trị nếu ranh giới
giữa chúng được giữ. Ranh giới giữ bằng thiện chí thì rữa sau vài sprint; giữ
bằng test thì không.

Đây là "architecture fitness function": test không kiểm hành vi sản phẩm, nó kiểm
rằng mã nguồn vẫn có hình dạng đã thoả thuận. Chạy 0,1 giây, không cần OCR.

    pytest tests/test_kien_truc.py -o addopts= -q
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GOC))

FEATURES = sorted((GOC / "features").glob("*.feature"))
BUOC_BDD = sorted((GOC / "tests").glob("test_bdd_*.py"))
DOI_TUONG = sorted((GOC / "doi_tuong").glob("*.py"))

# Từ ngữ kỹ thuật không được xuất hiện trong feature file: chúng trói kịch bản
# nghiệp vụ vào một nền tảng, và làm bài 2 (web) không dùng lại được.
TU_KY_THUAT = ["tesseract", "pytesseract", "psm", "locator", "xpath", "css selector",
               "click(", "get_by_role", "driver", "webdriver", "appium", "sql"]

# Module thuộc tầng dưới (driver). Bước Gherkin không được import trực tiếp.
MODULE_TANG_DUOI = ["bo_do.mo_hinh", "pytesseract", "playwright", "appium", "selenium"]


def _dong_khong_phai_ghi_chu(tep: Path) -> list[tuple[int, str]]:
    """Các dòng feature thật sự, bỏ dòng ghi chú `#`."""
    return [(i, d) for i, d in enumerate(tep.read_text(encoding="utf-8").splitlines(), 1)
            if d.strip() and not d.strip().startswith("#")]


@pytest.mark.parametrize("tep", FEATURES, ids=[f.name for f in FEATURES])
def test_TC_KT_01_feature_khong_dinh_ky_thuat(tep: Path):
    """Feature file phải đọc được bởi người không biết code.

    Ghi chú `#` được miễn — chúng là chỗ giải thích bối cảnh cho người đọc.
    """
    dinh = [f"dòng {i}: {d.strip()!r} (chứa {t!r})"
            for i, d in _dong_khong_phai_ghi_chu(tep)
            for t in TU_KY_THUAT if t in d.lower()]
    assert not dinh, (
        f"{tep.name} rò rỉ chi tiết kỹ thuật vào kịch bản nghiệp vụ:\n  "
        + "\n  ".join(dinh)
        + "\nĐẩy chi tiết đó xuống doi_tuong/, giữ feature ở mức hành vi.")


@pytest.mark.parametrize("tep", BUOC_BDD, ids=[f.name for f in BUOC_BDD])
def test_TC_KT_02_buoc_gherkin_khong_import_tang_duoi(tep: Path):
    """Bước Gherkin chỉ được đi qua lớp đối tượng.

    Import thẳng driver là đường tắt tiện lúc viết và đắt lúc thêm nền tảng: mọi
    bước dùng đường tắt đó phải viết lại cho web và cho mobile.
    """
    cay = ast.parse(tep.read_text(encoding="utf-8"))
    vi_pham = []
    for nut in ast.walk(cay):
        ten = ""
        if isinstance(nut, ast.Import):
            ten = " ".join(a.name for a in nut.names)
        elif isinstance(nut, ast.ImportFrom):
            ten = nut.module or ""
        for cam in MODULE_TANG_DUOI:
            if ten.startswith(cam):
                vi_pham.append(f"dòng {nut.lineno}: import {ten}")
    assert not vi_pham, (
        f"{tep.name} import thẳng tầng driver:\n  " + "\n  ".join(vi_pham)
        + "\nĐi qua doi_tuong/ để bài 2 (web) và mobile dùng lại được bộ bước này.")


@pytest.mark.parametrize("tep", DOI_TUONG, ids=[f.name for f in DOI_TUONG])
def test_TC_KT_03_lop_doi_tuong_khong_chua_phan_quyet(tep: Path):
    """Lớp đối tượng trả DỮ LIỆU; phán quyết đúng/sai là việc của bước `Thì`.

    Trộn assertion vào lớp đối tượng thì nó chỉ dùng được cho đúng ca kiểm thử đã
    viết nó, và nền tảng khác phải viết lại từ đầu.
    """
    cay = ast.parse(tep.read_text(encoding="utf-8"))
    assert_ = [n.lineno for n in ast.walk(cay) if isinstance(n, ast.Assert)]
    assert not assert_, (
        f"{tep.name} chứa assert ở dòng {assert_} — chuyển phán quyết lên bước `Thì`")


def test_TC_KT_04_moi_feature_deu_co_buoc_rang_buoc():
    """Feature không được gắn với bước nào là feature không bao giờ chạy."""
    da_rang = set()
    for tep in BUOC_BDD:
        for m in re.findall(r'scenarios\(\s*["\']([^"\']+)["\']', tep.read_text(encoding="utf-8")):
            da_rang.add(Path(m).name)
    mo_coi = [f.name for f in FEATURES if f.name not in da_rang]
    assert not mo_coi, (
        f"feature không có file bước nào ràng buộc — nó không hề chạy: {mo_coi}")


def test_TC_KT_05_lop_doi_tuong_cai_du_hop_dong():
    """Mọi lớp con của DoiTuongKiemThu phải cài đủ 3 phương thức của hợp đồng."""
    from doi_tuong.co_so import DoiTuongKiemThu
    from doi_tuong.ho_so_giay_to import HoSoGiayTo

    for lop in (HoSoGiayTo,):
        assert issubclass(lop, DoiTuongKiemThu)
        for ten in ("mo", "xu_ly", "tu_kiem_tra"):
            assert callable(getattr(lop, ten, None)), f"{lop.__name__} thiếu {ten}()"
        # Cài đủ nghĩa là instantiate được — lớp abstract còn thiếu sẽ nổ ở đây.
        lop()


def test_TC_KT_06_hop_dong_ket_qua_du_cho_ca_web_lan_model():
    """`KetQuaTruong` phải mang được cả tín hiệu của model lẫn của web.

    Model điền `tin_cay`, web điền `loi`. Thiếu một trong hai thì một nền tảng
    phải bịa ra trường không có, và bước Gherkin bắt đầu phân nhánh theo nền tảng.
    """
    from doi_tuong.co_so import KetQuaTruong
    t = KetQuaTruong(ten="x")
    for thuoc_tinh in ("gia_tri", "tin_cay", "can_nguoi_xac_nhan", "nguon", "loi"):
        assert hasattr(t, thuoc_tinh), f"KetQuaTruong thiếu {thuoc_tinh}"


def test_TC_KT_07_feature_dung_gherkin_tieng_viet():
    """Giữ cùng một bộ từ vựng với bài 2 để hai repo đọc như một."""
    thieu = [f.name for f in FEATURES
             if not f.read_text(encoding="utf-8").lstrip().startswith("# language: vi")]
    assert not thieu, f"feature thiếu khai báo `# language: vi`: {thieu}"
