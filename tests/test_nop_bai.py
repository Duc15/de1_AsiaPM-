"""Kiểm thử chính BÀI NỘP — mục 06 của đề là một danh sách nghiệm thu.

Đề liệt kê 6 thứ phải nộp và một ràng buộc "báo cáo ≤ 2 trang". Đó là tiêu chí
nghiệm thu, nên chúng được KIỂM chứ không được tin. Đặc biệt là số trang: đếm ký
tự rồi đoán ra số trang là sai — ở đây báo cáo được dàn trang bằng layout engine
thật (reportlab) và số trang là số đo.

Ca TC-NOP-02 canh đúng cái ràng buộc khó nhất: **vừa ≤ 2 trang vừa không được bỏ
mục nào**. Nó đối chiếu từng tiêu đề trong .md với văn bản trích ra từ PDF, nên
không thể lách bằng cách xoá bớt một mục cho vừa trang.

    pytest tests/test_nop_bai.py -o addopts= -q      # ~6 giây, không cần OCR
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GOC))

from bo_do.xuat_pdf import (CO_CHU_NOP, LE_MM_NOP, NGAT_TRANG_NOP,  # noqa: E402
                            dem_trang, xuat_pdf)

BAO_CAO = GOC / "BAO-CAO.md"
BAO_CAO_PDF = GOC / "BAO-CAO.pdf"
TOI_DA_TRANG = 2
# Lấy thẳng từ bo_do/xuat_pdf.py — KHÔNG khai lại ở đây. Khai lại chính là lỗi
# BD-08: cổng đo bản render 10 pt không ngắt trang (2 trang, xanh) trong khi
# `scripts/xuat_bao_cao_pdf.py` ghi ra bản 8 pt có ngắt trang (3 trang) và đó mới
# là tệp thật sự nộp đi.
CO_CHU = CO_CHU_NOP
LE_MM = LE_MM_NOP
NGAT = NGAT_TRANG_NOP


@pytest.fixture(scope="module")
def pdf_va_van_ban(tmp_path_factory):
    pytest.importorskip("pypdf", reason="cần pypdf để đọc lại PDF đã render")
    from pypdf import PdfReader
    tep = tmp_path_factory.mktemp("pdf") / "bao-cao.pdf"
    so_trang = xuat_pdf(BAO_CAO, tep, co_chu=CO_CHU, le_mm=LE_MM,
                        ngat_trang_truoc=NGAT)
    doc = PdfReader(str(tep))
    return so_trang, "\n".join(t.extract_text() or "" for t in doc.pages)


def _chuan(s: str) -> str:
    """Bỏ đánh dấu Markdown và gộp khoảng trắng để so được với text trích từ PDF."""
    s = re.sub(r"[*`_]", "", s)
    return re.sub(r"\s+", " ", s).strip()


# ===========================================================================
# Ràng buộc "≤ 2 trang" — đo, không đoán
# ===========================================================================
def test_TC_NOP_01_bao_cao_khong_qua_2_trang(pdf_va_van_ban):
    so_trang, _ = pdf_va_van_ban
    assert so_trang <= TOI_DA_TRANG, (
        f"báo cáo dài {so_trang} trang A4 ở cỡ chữ {CO_CHU} pt / lề {LE_MM} mm, "
        f"đề giới hạn {TOI_DA_TRANG}. Rút gọn nội dung — KHÔNG hạ cỡ chữ để lách, "
        "vì TC-NOP-06 canh cỡ chữ tối thiểu.")


# Mục bắt buộc phải có trong báo cáo, suy ra từ những gì đề hỏi. Đây là chốt chặn
# cho cách lách dễ nhất khi bị giới hạn 2 trang: xoá bớt một mục cho vừa.
# Mỗi mục = (tên để báo lỗi, các cụm từ phải xuất hiện — đủ MỘT là được).
MUC_BAT_BUOC = [
    ("luật \"đúng là gì\" của Bước 1", ["Đúng\" nghĩa là gì", "Đúng nghĩa là gì"]),
    ("bảng kết quả đo", ["Điểm tin cậy (có trọng số)"]),
    ("bao phủ đặc tả AC", ["Bao phủ AC"]),
    ("danh sách lỗi kèm mức nghiêm trọng", ["Nghiêm trọng", "LOI-01"]),
    ("kết luận nghiệp vụ go/no-go", ["chưa dùng được", "KHÔNG ĐẠT"]),
    ("giới hạn của phép đo", ["không chứng minh được gì"]),
    ("trả lời câu hỏi cuối", ["Trả lời câu hỏi cuối"]),
]


@pytest.mark.parametrize("ten,cum_tu", MUC_BAT_BUOC, ids=[m[0] for m in MUC_BAT_BUOC])
def test_TC_NOP_02_bao_cao_con_du_muc_bat_buoc(pdf_va_van_ban, ten, cum_tu):
    """Chốt chặn cho cách lách dễ nhất: xoá bớt mục cho vừa 2 trang.

    Ca này ra đời sau khi tôi thử chính cổng của mình: xoá hẳn mục "phép đo không
    chứng minh được gì" thì TC-NOP-03 (đối chiếu tiêu đề .md ↔ PDF) vẫn XANH, vì
    xoá cả hai đầu thì hai đầu vẫn khớp nhau. Nó chỉ bắt được mục bị *renderer*
    đánh rơi, không bắt được mục bị *người viết* cắt.
    """
    _, van_ban = pdf_va_van_ban
    van_ban_chuan = _chuan(van_ban)
    assert any(_chuan(c) in van_ban_chuan for c in cum_tu), (
        f"báo cáo thiếu mục bắt buộc: {ten}. Nếu cắt mục này để vừa 2 trang thì "
        "phải rút gọn chỗ khác, không được bỏ mục.")


def test_TC_NOP_03_khong_muc_nao_bi_renderer_danh_roi(pdf_va_van_ban):
    """Đối chiếu từng tiêu đề trong Markdown với văn bản thật trong PDF."""
    _, van_ban = pdf_va_van_ban
    van_ban_chuan = _chuan(van_ban)
    thieu = []
    for dong in BAO_CAO.read_text(encoding="utf-8").splitlines():
        if not dong.startswith("#"):
            continue
        tieu_de = _chuan(dong.lstrip("# "))
        if tieu_de and tieu_de not in van_ban_chuan:
            thieu.append(tieu_de)
    assert not thieu, "mục có trong .md nhưng không có trong PDF:\n  " + "\n  ".join(thieu)


def test_TC_NOP_04_bang_bieu_khong_bi_rot_khi_render(pdf_va_van_ban):
    """Mọi bảng phải xuất hiện trong PDF — kiểm qua ô đầu của từng bảng."""
    _, van_ban = pdf_va_van_ban
    van_ban_chuan = _chuan(van_ban)
    dong = BAO_CAO.read_text(encoding="utf-8").splitlines()
    thieu = []
    for i, d in enumerate(dong):
        if not d.strip().startswith("|") or i + 1 >= len(dong):
            continue
        if not re.fullmatch(r"\|[\s|:-]+\|", dong[i + 1].strip()):
            continue
        o_dau = _chuan(d.strip().strip("|").split("|")[0])
        if o_dau and o_dau not in van_ban_chuan:
            thieu.append(f"dòng {i + 1}: {o_dau!r}")
    assert not thieu, "bảng không render được vào PDF:\n  " + "\n  ".join(thieu)


def test_TC_NOP_05_dau_tieng_viet_khong_vo_khi_render(pdf_va_van_ban):
    """Font thiếu glyph thì dấu biến mất im lặng — báo cáo vẫn 2 trang nhưng sai."""
    _, van_ban = pdf_va_van_ban
    for mau in ("TRẦN THỊ MAI", "nghiêm trọng", "điểm kiểm", "hồ sơ"):
        assert mau in van_ban, f"mất dấu tiếng Việt khi render: thiếu {mau!r}"


def test_TC_NOP_06_co_chu_khong_duoc_nho_qua_muc_doc_duoc():
    """Chặn đường lách: không được co chữ xuống mức không đọc nổi cho vừa trang."""
    assert CO_CHU >= 9.0, f"cỡ chữ {CO_CHU} pt quá nhỏ để gọi là báo cáo đọc được"


def test_TC_NOP_07_cau_hoi_cuoi_nam_trong_2_trang_do(pdf_va_van_ban):
    """Đề: "báo cáo ≤ 2 trang — GỒM CẢ trả lời câu hỏi cuối ở mục 05"."""
    _, van_ban = pdf_va_van_ban
    van_ban_chuan = _chuan(van_ban)
    assert "Trả lời câu hỏi cuối" in van_ban_chuan
    for y in ("Không đồng ý", "sigma", "46,5"):
        assert y in van_ban_chuan, f"phần trả lời câu hỏi cuối thiếu ý: {y!r}"


# ===========================================================================
# Danh sách nộp bài ở mục 06 của đề
# ===========================================================================
DANH_SACH_NOP = [
    ("bộ dữ liệu", lambda: len(list((GOC / "data" / "anh").glob("*.jpg"))) >= 30),
    ("cách sinh bộ dữ liệu", lambda: (GOC / "scripts" / "sinh_du_lieu.py").exists()),
    ("bản kê sinh dữ liệu", lambda: (GOC / "data" / "nhan" / "ban_ke_sinh.json").exists()),
    ("bộ nhãn máy đọc được", lambda: (GOC / "data" / "nhan" / "nhan.jsonl").exists()),
    ("script đo", lambda: (GOC / "scripts" / "do_luong.py").exists()),
    ("bộ test tự động", lambda: len(list((GOC / "tests").glob("test_*.py"))) >= 3),
    ("prompt đã dùng với AI", lambda: (GOC / "PROMPTS.md").exists()),
    ("báo cáo", lambda: BAO_CAO.exists()),
    ("hướng dẫn chạy", lambda: (GOC / "README.md").exists()),
]


@pytest.mark.parametrize("ten,kiem", DANH_SACH_NOP, ids=[t[0] for t in DANH_SACH_NOP])
def test_TC_NOP_10_du_muc_nop_bai(ten, kiem):
    assert kiem(), f"thiếu sản phẩm bắt buộc theo mục 06 của đề: {ten}"


def test_TC_NOP_11_script_do_chay_duoc_bang_mot_lenh():
    """Đề: "chạy được bằng một lệnh". Kiểm bằng cách gọi thật với --help.

    Phải ép UTF-8: console Windows mặc định cp1252, mà trợ giúp của script có
    tiếng Việt — không ép thì chính ca kiểm thử này vỡ vì lý do không liên quan.
    """
    import os
    r = subprocess.run(
        [sys.executable, "scripts/do_luong.py", "--help"], cwd=GOC,
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=dict(os.environ, PYTHONIOENCODING="utf-8"), timeout=90)
    assert r.returncode == 0, f"scripts/do_luong.py không chạy được: {r.stderr[:400]}"
    assert "--model" in r.stdout, "script đo không nêu được tham số của nó"


def test_TC_NOP_12_readme_co_lenh_chay():
    doc = (GOC / "README.md").read_text(encoding="utf-8")
    assert "python scripts/do_luong.py" in doc, "README thiếu lệnh chạy bộ đo"
    assert "pytest" in doc, "README thiếu cách chạy bộ test"


def test_TC_NOP_13_khong_lo_du_lieu_ca_nhan():
    """Ràng buộc không thương lượng của đề: không dùng CCCD thật của ai.

    Số định danh thật có 3 chữ số đầu là mã tỉnh 001–096. Bộ này dùng tiền tố
    000 — không phải mã tỉnh hợp lệ — nên không thể trùng số của người thật.
    """
    import json
    ban_ke = json.loads((GOC / "data" / "nhan" / "ban_ke_sinh.json")
                        .read_text(encoding="utf-8"))
    vi_pham = []
    for anh in ban_ke["anh"]:
        so = anh["noi_dung_da_ve"].get("so_dinh_danh")
        if so and not so.startswith("000"):
            vi_pham.append(f"{anh['id']}: {so}")
    assert not vi_pham, ("số định danh không dùng tiền tố 000 — có nguy cơ trùng "
                         "số người thật:\n  " + "\n  ".join(vi_pham))


def test_TC_NOP_14_bao_cao_neu_ro_gioi_han_cua_phep_do():
    """Đề nói rõ đây là thứ họ quan tâm nhất — nên nó phải có trong báo cáo."""
    doc = _chuan(BAO_CAO.read_text(encoding="utf-8"))
    for y in ("không chứng minh được gì", "mô phỏng", "n = 33"):
        assert y in doc, f"báo cáo thiếu phần nêu giới hạn: {y!r}"


def test_TC_NOP_15_so_trang_on_dinh_qua_cac_lan_render():
    """Số trang phải tất định, nếu không thì cổng TC-NOP-01 lúc xanh lúc đỏ."""
    kw = dict(co_chu=CO_CHU, le_mm=LE_MM, ngat_trang_truoc=NGAT)
    a = dem_trang(BAO_CAO, **kw)
    b = dem_trang(BAO_CAO, **kw)
    assert a == b == dem_trang(BAO_CAO, **kw)


def test_TC_NOP_16_pdf_da_nop_khop_voi_ban_render_hien_tai():
    """Cổng phải đo ĐÚNG TỆP NỘP ĐI, không đo một bản render khác (lỗi BD-08).

    Người chấm mở `BAO-CAO.pdf`, không mở `BAO-CAO.md`. Nên tệp PDF trong repo
    phải (a) tồn tại, (b) ≤ 2 trang, (c) là bản render của đúng nội dung .md hiện
    tại — sửa .md mà quên chạy lại script thì cổng này ĐỎ.
    """
    pytest.importorskip("pypdf", reason="cần pypdf để đọc lại PDF đã render")
    from pypdf import PdfReader

    assert BAO_CAO_PDF.exists(), (
        "thiếu BAO-CAO.pdf. Chạy: python scripts/xuat_bao_cao_pdf.py")

    da_nop = PdfReader(str(BAO_CAO_PDF))
    assert len(da_nop.pages) <= TOI_DA_TRANG, (
        f"BAO-CAO.pdf trong repo dày {len(da_nop.pages)} trang, đề giới hạn "
        f"{TOI_DA_TRANG}. Đây là tệp người chấm mở ra đọc.")

    import tempfile
    with tempfile.TemporaryDirectory() as tam:
        moi = Path(tam) / "moi.pdf"
        xuat_pdf(BAO_CAO, moi, co_chu=CO_CHU, le_mm=LE_MM, ngat_trang_truoc=NGAT)
        van_ban_moi = "\n".join(t.extract_text() or "" for t in PdfReader(str(moi)).pages)

    van_ban_cu = "\n".join(t.extract_text() or "" for t in da_nop.pages)
    assert _chuan(van_ban_cu) == _chuan(van_ban_moi), (
        "BAO-CAO.pdf đã cũ so với BAO-CAO.md. Chạy lại: "
        "python scripts/xuat_bao_cao_pdf.py")
