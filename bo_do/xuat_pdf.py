"""Render BAO-CAO.md ra PDF A4 và **đếm số trang thật**.

Vì sao có file này: đề đặt một ràng buộc nghiệm thu — "báo cáo ≤ 2 trang". Ước
lượng số trang bằng cách đếm ký tự là đoán, và đoán thì sai. Ở đây báo cáo được
dàn trang bằng một layout engine thật (reportlab), nên `so_trang` là số đo chứ
không phải phỏng đoán — và `tests/test_nop_bai.py` canh nó như canh bất kỳ tiêu
chí nghiệm thu nào khác.

Bộ chuyển đổi Markdown ở đây cố ý tối giản: chỉ đủ cho những gì báo cáo dùng
(tiêu đề, đoạn văn, bảng, đường kẻ ngang, **đậm**/*nghiêng*/`mã`). Nó không phải
một trình Markdown đầy đủ và không định trở thành.
"""

from __future__ import annotations

import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (HRFlowable, KeepTogether, PageBreak, Paragraph,
                                SimpleDocTemplate, Spacer, Table, TableStyle)

# Font phải có glyph tiếng Việt. Thứ tự: (thường, đậm, nghiêng, đậm-nghiêng)
_BO_FONT = [
    ("C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/arialbd.ttf",
     "C:/Windows/Fonts/ariali.ttf", "C:/Windows/Fonts/arialbi.ttf"),
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
     "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
     "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf",
     "/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf"),
]
_MONO = ["C:/Windows/Fonts/consola.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"]

TEN_FONT = "BaoCao"
TEN_MONO = "BaoCaoMono"


def _dang_ky_font() -> None:
    if TEN_FONT in pdfmetrics.getRegisteredFontNames():
        return
    for thuong, dam, nghieng, dam_nghieng in _BO_FONT:
        if not Path(thuong).exists():
            continue
        pdfmetrics.registerFont(TTFont(TEN_FONT, thuong))
        for hau_to, duong_dan in (("-Bold", dam), ("-Italic", nghieng),
                                  ("-BoldItalic", dam_nghieng)):
            pdfmetrics.registerFont(
                TTFont(TEN_FONT + hau_to, duong_dan if Path(duong_dan).exists() else thuong))
        pdfmetrics.registerFontFamily(
            TEN_FONT, normal=TEN_FONT, bold=TEN_FONT + "-Bold",
            italic=TEN_FONT + "-Italic", boldItalic=TEN_FONT + "-BoldItalic")
        break
    else:
        raise FileNotFoundError("không tìm thấy font TrueType có glyph tiếng Việt")

    for duong_dan in _MONO:
        if Path(duong_dan).exists():
            pdfmetrics.registerFont(TTFont(TEN_MONO, duong_dan))
            return
    pdfmetrics.registerFont(TTFont(TEN_MONO, thuong))


# ---------------------------------------------------------------------------
# Markdown nội tuyến -> thẻ của reportlab
# ---------------------------------------------------------------------------
def _noi_tuyen(s: str) -> str:
    s = html.escape(s)
    s = re.sub(r"`([^`]+)`", rf'<font face="{TEN_MONO}" size="7">\1</font>', s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", s)
    s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)
    return s


def _tach_hang_bang(dong: str) -> list[str]:
    return [o.strip() for o in dong.strip().strip("|").split("|")]


def _la_dong_ngan_cach(dong: str) -> bool:
    return bool(re.fullmatch(r"\|[\s|:-]+\|", dong.strip()))


def dung_noi_dung(md: str, kieu: dict, rong: float) -> list:
    """Markdown -> danh sách flowable. Bảng được gom nguyên khối."""
    ra: list = []
    dong = md.splitlines()
    i = 0
    doan: list[str] = []

    def xa_doan() -> None:
        nonlocal doan
        if doan:
            ra.append(Paragraph(_noi_tuyen(" ".join(doan)), kieu["than"]))
            doan = []

    while i < len(dong):
        d = dong[i]
        rong_d = d.strip()

        if not rong_d:
            xa_doan()
            i += 1
            continue

        if rong_d.startswith("#"):
            xa_doan()
            cap = len(rong_d) - len(rong_d.lstrip("#"))
            ra.append(Paragraph(_noi_tuyen(rong_d.lstrip("# ").strip()),
                                kieu[f"h{min(cap, 3)}"]))
            i += 1
            continue

        if rong_d in ("---", "***", "___"):
            xa_doan()
            ra.append(HRFlowable(width="100%", thickness=0.5,
                                 color=colors.HexColor("#999999"),
                                 spaceBefore=3, spaceAfter=3))
            i += 1
            continue

        if rong_d.startswith("|") and i + 1 < len(dong) and _la_dong_ngan_cach(dong[i + 1]):
            xa_doan()
            tieu_de = _tach_hang_bang(rong_d)
            i += 2
            than = []
            while i < len(dong) and dong[i].strip().startswith("|"):
                than.append(_tach_hang_bang(dong[i]))
                i += 1
            ra.append(_dung_bang(tieu_de, than, kieu, rong))
            continue

        if re.match(r"^[-*]\s+", rong_d):
            xa_doan()
            ra.append(Paragraph("• " + _noi_tuyen(re.sub(r"^[-*]\s+", "", rong_d)),
                                kieu["gach_dau_dong"]))
            i += 1
            continue

        doan.append(rong_d)
        i += 1

    xa_doan()
    return ra


def _dung_bang(tieu_de: list[str], than: list[list[str]], kieu: dict, rong: float):
    so_cot = max(len(tieu_de), *(len(h) for h in than)) if than else len(tieu_de)

    def o(txt: str, k):
        return Paragraph(_noi_tuyen(txt), k)

    du_lieu = [[o(c, kieu["bang_dau"]) for c in (tieu_de + [""] * so_cot)[:so_cot]]]
    for h in than:
        du_lieu.append([o(c, kieu["bang"]) for c in (h + [""] * so_cot)[:so_cot]])

    # Chia cột theo độ dài nội dung, có sàn để cột hẹp không bị bóp nát.
    do_dai = [max(len(re.sub(r"[*`]", "", (h + [""] * so_cot)[j]))
                  for h in [tieu_de] + than) for j in range(so_cot)]
    tong = sum(do_dai) or 1
    san = rong * 0.06
    rong_cot = [max(san, rong * d / tong) for d in do_dai]
    he_so = rong / sum(rong_cot)
    rong_cot = [w * he_so for w in rong_cot]

    t = Table(du_lieu, colWidths=rong_cot, repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#BBBBBB")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EFEFEF")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 2.5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2.5),
        ("TOPPADDING", (0, 0), (-1, -1), 1.2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.2),
    ]))
    return KeepTogether([t, Spacer(1, 3)])


# ---------------------------------------------------------------------------
def tao_kieu(co_chu: float, gian_dong: float) -> dict:
    _dang_ky_font()
    goc = ParagraphStyle("than", fontName=TEN_FONT, fontSize=co_chu,
                         leading=co_chu * gian_dong, alignment=TA_JUSTIFY,
                         spaceAfter=co_chu * 0.42)
    return {
        "than": goc,
        "gach_dau_dong": ParagraphStyle("gach", parent=goc, leftIndent=7,
                                        spaceAfter=co_chu * 0.2),
        "bang": ParagraphStyle("bang", parent=goc, fontSize=co_chu - 0.7,
                               leading=(co_chu - 0.7) * 1.16, alignment=0,
                               spaceAfter=0),
        "bang_dau": ParagraphStyle("bangdau", parent=goc, fontSize=co_chu - 0.7,
                                   leading=(co_chu - 0.7) * 1.16, alignment=0,
                                   spaceAfter=0, fontName=TEN_FONT + "-Bold"),
        "h1": ParagraphStyle("h1", parent=goc, fontName=TEN_FONT + "-Bold",
                             fontSize=co_chu + 3.2, leading=(co_chu + 3.2) * 1.16,
                             spaceBefore=co_chu * 0.5, spaceAfter=co_chu * 0.42,
                             alignment=0),
        "h2": ParagraphStyle("h2", parent=goc, fontName=TEN_FONT + "-Bold",
                             fontSize=co_chu + 1.1, leading=(co_chu + 1.1) * 1.16,
                             spaceBefore=co_chu * 0.62, spaceAfter=co_chu * 0.22,
                             alignment=0),
        "h3": ParagraphStyle("h3", parent=goc, fontName=TEN_FONT + "-Bold",
                             fontSize=co_chu + 0.3, leading=(co_chu + 0.3) * 1.16,
                             spaceBefore=co_chu * 0.4, spaceAfter=co_chu * 0.18,
                             alignment=0),
    }


def xuat_pdf(tep_md: Path, tep_pdf: Path, co_chu: float = 8.0,
             le_mm: float = 12.0, gian_dong: float = 1.22,
             ngat_trang_truoc: str | None = None) -> int:
    """Render và trả về SỐ TRANG THẬT."""
    md = tep_md.read_text(encoding="utf-8")
    kieu = tao_kieu(co_chu, gian_dong)
    rong = A4[0] - 2 * le_mm * mm

    tai_lieu = SimpleDocTemplate(
        str(tep_pdf), pagesize=A4,
        leftMargin=le_mm * mm, rightMargin=le_mm * mm,
        topMargin=le_mm * mm, bottomMargin=le_mm * mm,
        title=tep_md.stem, author="Bài 1 — kiểm thử độ tin cậy mô hình trích xuất")

    if ngat_trang_truoc and ngat_trang_truoc in md:
        truoc, sau = md.split(ngat_trang_truoc, 1)
        noi_dung = (dung_noi_dung(truoc, kieu, rong) + [PageBreak()]
                    + dung_noi_dung(ngat_trang_truoc + sau, kieu, rong))
    else:
        noi_dung = dung_noi_dung(md, kieu, rong)

    tai_lieu.build(noi_dung)
    return tai_lieu.page


def dem_trang(tep_md: Path, **kw) -> int:
    """Đếm số trang mà không giữ lại PDF (dùng cho test)."""
    import tempfile
    with tempfile.TemporaryDirectory() as tam:
        return xuat_pdf(tep_md, Path(tam) / "tam.pdf", **kw)
