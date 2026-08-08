"""Bước 2 — sinh bộ ảnh kiểm thử.

Vì sao sinh chứ không đi thu ảnh thật: số định danh và ảnh giấy tờ của người thật
là dữ liệu cá nhân. Đề cấm dùng CCCD thật của bất kỳ ai, kể cả của mình, và cấm
tải ảnh giấy tờ người lạ trên mạng. Sinh bằng script cho thêm ba thứ mà bộ ảnh
thật không có: nhãn đúng theo cấu tạo, chất lượng ảnh điều khiển được theo bậc,
và tái lập được bit-by-bit bằng seed.

Cái phải trả giá: đây là giấy tờ mô phỏng, không phải giấy tờ thật. Xem mục
"Giới hạn" trong BAO-CAO.md — đây là giả định lớn nhất của cả bài.

Chạy:  python scripts/sinh_du_lieu.py
"""

from __future__ import annotations

import argparse
import io
import json
import math
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]

from bo_do.schema import CCCD, MAU_01, MUC_KHONG_DOC_DUOC  # noqa: E402

GOC = Path(__file__).resolve().parents[1]
THU_MUC_ANH = GOC / "data" / "anh"
THU_MUC_NHAN = GOC / "data" / "nhan"

F_THUONG = "C:/Windows/Fonts/arial.ttf"
F_DAM = "C:/Windows/Fonts/arialbd.ttf"
F_NGHIENG = "C:/Windows/Fonts/ariali.ttf"   # dùng mô phỏng chữ viết tay
F_CHAN = "C:/Windows/Fonts/times.ttf"

# Các font viết tay có sẵn trên Windows (Ink Free, Segoe Script) THIẾU glyph dấu
# tiếng Việt — kiểm tra bằng fontTools trước khi chọn. Nên chữ "viết tay" ở đây
# là font nghiêng cộng nhiễu hình học từng ký tự. Đây là một giả định, ghi rõ
# trong báo cáo: nó mô phỏng nét không đều và đường cơ sở gợn, KHÔNG mô phỏng
# hình dạng chữ viết tay thật.


# ---------------------------------------------------------------------------
# Dữ liệu định danh — toàn bộ là hư cấu.
# Tiền tố "000" không phải mã tỉnh hợp lệ theo TT 59/2021, nên 12 chữ số này
# không thể trùng số định danh của một người thật.
# ---------------------------------------------------------------------------
NGUOI = [
    ("000301001234", "TRẦN THỊ MAI", "01/03/1990", "Số 12 Đường Lê Duẩn, Phường Tân Mai, Quận Hoàng Mai, Thành phố Hà Nội"),
    ("000185004567", "NGUYỄN VĂN HÙNG", "17/11/1985", "Thôn Đoài, Xã Nguyên Khê, Huyện Đông Anh, Thành phố Hà Nội"),
    ("000492007781", "LÊ THỊ NGỌC HUYỀN", "23/07/1992", "Số 45/7 Đường Nguyễn Ảnh Thủ, Phường Trung Mỹ Tây, Quận 12, Thành phố Hồ Chí Minh"),
    ("000278003094", "PHẠM ĐỨC THẮNG", "09/02/1978", "Số 8 Ngõ 32 Đường Cầu Giấy, Phường Dịch Vọng, Quận Cầu Giấy, Thành phố Hà Nội"),
    ("000395006612", "VÕ THỊ KIM LOAN", "30/09/1995", "Tổ 4 Khu phố 2, Phường Long Bình, Thành phố Biên Hòa, Tỉnh Đồng Nai"),
    ("000188002345", "HOÀNG MINH TUẤN", "12/05/1988", "Số 210 Đường Trần Phú, Phường Máy Tơ, Quận Ngô Quyền, Thành phố Hải Phòng"),
    ("000501009923", "ĐẶNG THỊ THU HÀ", "05/12/2001", "Số 17 Đường Hùng Vương, Phường Thắng Lợi, Thành phố Buôn Ma Thuột, Tỉnh Đắk Lắk"),
    ("000283005510", "BÙI QUỐC ĐẠT", "28/08/1983", "Thôn Trung, Xã Tân Ước, Huyện Thanh Oai, Thành phố Hà Nội"),
    ("000396001178", "TRƯƠNG THỊ BÍCH PHƯỢNG", "14/04/1996", "Số 3 Đường Nguyễn Huệ, Phường Vĩnh Ninh, Thành phố Huế"),
]

DON = [
    ("TRẦN THỊ MAI", "mua", "15", "8.500.000"),
    ("NGUYỄN VĂN HÙNG", "thuê", "9,5", "6.200.000"),
    ("LÊ THỊ NGỌC HUYỀN", "thuê mua", "12", "11.000.000"),
    ("PHẠM ĐỨC THẮNG", "mua", "7", "4.800.000"),
    ("VÕ THỊ KIM LOAN", "thuê", "18,5", "9.750.000"),
    ("HOÀNG MINH TUẤN", "thuê mua", "10", "7.300.000"),
    ("ĐẶNG THỊ THU HÀ", "mua", "6,5", "5.100.000"),
    ("BÙI QUỐC ĐẠT", "thuê", "22", "13.400.000"),
]

# Bao nhiêu ảnh cho mỗi (loại giấy tờ, mức chất lượng).
KE_HOACH = {
    "cccd":   {"sach": 4, "nhe": 4, "trung_binh": 4, "nang": 3, MUC_KHONG_DOC_DUOC: 3},
    "mau_01": {"sach": 3, "nhe": 3, "trung_binh": 3, "nang": 3, MUC_KHONG_DOC_DUOC: 3},
}


def font(duong_dan: str, co: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(duong_dan, co)


# ---------------------------------------------------------------------------
# Vẽ giấy tờ sạch
# ---------------------------------------------------------------------------
def ve_chu_viet_tay(anh: Image.Image, xy, text: str, co: int,
                    rng: random.Random, mau=(20, 30, 90)) -> None:
    """Vẽ từng ký tự với xoay/lệch/co giãn nhẹ để giả nét viết tay."""
    x, y = xy
    f = font(F_NGHIENG, co)
    for c in text:
        if c == " ":
            x += co * 0.32
            continue
        lop = Image.new("RGBA", (co * 2, co * 2), (0, 0, 0, 0))
        ImageDraw.Draw(lop).text((co * 0.3, co * 0.2), c, font=f, fill=mau + (255,))
        lop = lop.rotate(rng.uniform(-7, 7), resample=Image.BICUBIC,
                         center=(co * 0.5, co))
        anh.alpha_composite(lop, (int(x), int(y + rng.uniform(-co * 0.09, co * 0.09))))
        x += f.getlength(c) * rng.uniform(0.94, 1.06)


def ve_cccd(nguoi, rng: random.Random) -> Image.Image:
    so, ten, sinh, tru = nguoi
    W, H = 1050, 660
    anh = Image.new("RGBA", (W, H), (236, 242, 248, 255))
    ve = ImageDraw.Draw(anh)

    # hoa văn nền mờ — giống mặt thẻ thật, và là thứ làm OCR khó lên
    for i in range(0, W + H, 13):
        ve.line([(i, 0), (0, i)], fill=(214, 226, 238, 255), width=1)
    ve.rectangle([8, 8, W - 8, H - 8], outline=(120, 150, 185, 255), width=3)

    ve.text((W // 2, 34), "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM",
            font=font(F_DAM, 27), fill=(150, 20, 20), anchor="mm")
    ve.text((W // 2, 68), "Độc lập - Tự do - Hạnh phúc",
            font=font(F_CHAN, 23), fill=(150, 20, 20), anchor="mm")
    ve.text((W // 2, 112), "CĂN CƯỚC CÔNG DÂN",
            font=font(F_DAM, 34), fill=(150, 20, 20), anchor="mm")

    # ô ảnh chân dung: chỉ là hình khối, không có mặt người nào
    ve.rectangle([46, 168, 266, 458], fill=(206, 212, 220, 255),
                 outline=(150, 160, 172, 255), width=2)
    ve.text((156, 313), "ẢNH", font=font(F_DAM, 24), fill=(140, 148, 158), anchor="mm")

    x = 300
    y = 176
    cap = [(CCCD.lay("so_dinh_danh").moc_neo[0], so, 31, F_DAM),
           (CCCD.lay("ho_ten").moc_neo[0], ten, 28, F_DAM),
           (CCCD.lay("ngay_sinh").moc_neo[0], sinh, 26, F_THUONG),
           (CCCD.lay("noi_thuong_tru").moc_neo[0], tru, 22, F_THUONG)]
    for moc, gia_tri, co, f_gia_tri in cap:
        ve.text((x, y), moc, font=font(F_THUONG, 22), fill=(40, 48, 62))
        rong_moc = font(F_THUONG, 22).getlength(moc)
        if moc.startswith("Nơi"):
            # địa chỉ dài -> ngắt dòng như thẻ thật
            chu = gia_tri.split(", ")
            giua = math.ceil(len(chu) / 2)
            ve.text((x + rong_moc + 10, y - 2), ", ".join(chu[:giua]),
                    font=font(f_gia_tri, co), fill=(18, 24, 40))
            ve.text((x, y + co + 8), ", ".join(chu[giua:]),
                    font=font(f_gia_tri, co), fill=(18, 24, 40))
            y += co + 8
        else:
            ve.text((x + rong_moc + 12, y - 4), gia_tri,
                    font=font(f_gia_tri, co), fill=(18, 24, 40))
        y += max(co, 26) + 34

    ve.text((60, 596), "Có giá trị đến: 01/03/2030",
            font=font(F_THUONG, 19), fill=(60, 70, 88))
    ve.text((700, 596), "ẢNH MÔ PHỎNG - KHÔNG CÓ GIÁ TRỊ",
            font=font(F_DAM, 17), fill=(170, 60, 60))
    return anh


def ve_mau_01(don, rng: random.Random) -> Image.Image:
    ten, hinh_thuc, dien_tich, thu_nhap = don
    W, H = 900, 1240
    anh = Image.new("RGBA", (W, H), (250, 249, 245, 255))
    ve = ImageDraw.Draw(anh)

    ve.text((W // 2, 46), "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM",
            font=font(F_DAM, 24), fill=(25, 25, 25), anchor="mm")
    ve.text((W // 2, 78), "Độc lập - Tự do - Hạnh phúc",
            font=font(F_CHAN, 21), fill=(25, 25, 25), anchor="mm")
    ve.line([(330, 96), (570, 96)], fill=(25, 25, 25), width=2)
    ve.text((W // 2, 140), "ĐƠN ĐĂNG KÝ MUA, THUÊ, THUÊ MUA",
            font=font(F_DAM, 27), fill=(20, 20, 20), anchor="mm")
    ve.text((W // 2, 174), "NHÀ Ở XÃ HỘI", font=font(F_DAM, 27),
            fill=(20, 20, 20), anchor="mm")
    ve.text((W // 2, 206), "(Mẫu số 01 - Nghị định 136/2026/NĐ-CP)",
            font=font(F_CHAN, 19), fill=(60, 60, 60), anchor="mm")
    ve.text((60, 250), "Kính gửi: Ban Quản lý dự án nhà ở xã hội",
            font=font(F_THUONG, 21), fill=(25, 25, 25))

    f_moc = font(F_THUONG, 21)
    y = 310

    def moc_va_tay(nhan: str, gia_tri: str, co_tay: int = 30) -> None:
        nonlocal y
        ve.text((60, y), nhan, font=f_moc, fill=(25, 25, 25))
        rong = f_moc.getlength(nhan)
        # dòng kẻ chấm của biểu in sẵn
        ve.line([(70 + rong, y + 26), (W - 60, y + 26)], fill=(150, 150, 150), width=1)
        ve_chu_viet_tay(anh, (76 + rong, y - 6), gia_tri, co_tay, rng)
        y += 74

    moc_va_tay(MAU_01.lay("ho_ten_nguoi_viet_don").moc_neo[0], ten, 31)

    ve.text((60, y), MAU_01.lay("hinh_thuc").moc_neo[0], font=f_moc, fill=(25, 25, 25))
    y += 40
    for pa in ("Mua", "Thuê", "Thuê mua"):
        ox, oy = 150, y
        ve.rectangle([ox, oy, ox + 24, oy + 24], outline=(30, 30, 30), width=2)
        if pa.lower() == hinh_thuc.lower():
            # dấu tích vẽ tay: hai nét chéo lệch nhau
            for (a, b, c, d) in ((3, 4, 21, 20), (21, 3, 4, 21)):
                ve.line([(ox + a + rng.randint(-2, 2), oy + b + rng.randint(-2, 2)),
                         (ox + c + rng.randint(-2, 2), oy + d + rng.randint(-2, 2))],
                        fill=(20, 30, 90), width=3)
        ve.text((ox + 42, oy + 1), pa, font=font(F_THUONG, 22), fill=(25, 25, 25))
        y += 44
    y += 22

    moc_va_tay(MAU_01.lay("dien_tich_binh_quan").moc_neo[0], f"{dien_tich} m²", 30)
    moc_va_tay(MAU_01.lay("thu_nhap_hang_thang").moc_neo[0], f"{thu_nhap} đồng", 30)

    ve.text((60, y), "Tôi xin cam đoan những nội dung khai trên là đúng sự thật và",
            font=font(F_THUONG, 20), fill=(25, 25, 25))
    ve.text((60, y + 30), "xin chịu trách nhiệm trước pháp luật về nội dung đã khai.",
            font=font(F_THUONG, 20), fill=(25, 25, 25))
    ve.text((600, y + 96), "Người viết đơn", font=font(F_THUONG, 20), fill=(25, 25, 25))
    ve.text((596, y + 124), "(Ký, ghi rõ họ tên)", font=font(F_CHAN, 17), fill=(70, 70, 70))
    ve_chu_viet_tay(anh, (588, y + 168), ten.title(), 27, rng)
    ve.text((W // 2, H - 40), "BIỂU MÔ PHỎNG DÙNG CHO KIỂM THỬ - KHÔNG CÓ GIÁ TRỊ PHÁP LÝ",
            font=font(F_DAM, 16), fill=(170, 60, 60), anchor="mm")
    return anh


# ---------------------------------------------------------------------------
# Làm xấu ảnh — mô phỏng người dân chụp bằng điện thoại ở sảnh UBND xã
# ---------------------------------------------------------------------------
def _he_so_phoi_canh(nguon, dich):
    A, B = [], []
    for (x, y), (u, v) in zip(nguon, dich):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); B.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); B.append(v)
    return np.linalg.solve(np.asarray(A, float), np.asarray(B, float)).tolist()


def phoi_canh(anh: Image.Image, muc: float, rng: random.Random) -> Image.Image:
    w, h = anh.size
    d = muc * min(w, h)
    dich = [(0, 0), (w, 0), (w, h), (0, h)]
    nguon = [(rng.uniform(-d, d), rng.uniform(-d, d)),
             (w + rng.uniform(-d, d), rng.uniform(-d, d)),
             (w + rng.uniform(-d, d), h + rng.uniform(-d, d)),
             (rng.uniform(-d, d), h + rng.uniform(-d, d))]
    return anh.transform((w, h), Image.PERSPECTIVE,
                         _he_so_phoi_canh(nguon, dich),
                         resample=Image.BICUBIC, fillcolor=(120, 120, 125, 255))


def nhoe_chuyen_dong(anh: Image.Image, dai: int, goc: float) -> Image.Image:
    """Tay run: cộng nhiều bản dịch chuyển theo một hướng."""
    a = np.asarray(anh.convert("RGB"), np.float32)
    dx, dy = math.cos(math.radians(goc)), math.sin(math.radians(goc))
    tich = np.zeros_like(a)
    for i in range(dai):
        t = i - dai // 2
        tich += np.roll(np.roll(a, int(round(dy * t)), 0), int(round(dx * t)), 1)
    return Image.fromarray(np.clip(tich / dai, 0, 255).astype(np.uint8)).convert("RGBA")


def anh_sang_khong_deu(anh: Image.Image, muc: float, rng: random.Random) -> Image.Image:
    w, h = anh.size
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    goc = rng.uniform(0, math.pi * 2)
    ramp = (math.cos(goc) * xx / w + math.sin(goc) * yy / h)
    he_so = 1.0 + muc * (ramp - ramp.mean()) * 2.4
    a = np.asarray(anh.convert("RGB"), np.float32) * he_so[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")


def loa_sang(anh: Image.Image, muc: float, rng: random.Random) -> Image.Image:
    """Vệt loá đèn huỳnh quang phản trên mặt thẻ ép plastic."""
    w, h = anh.size
    cx, cy = rng.uniform(0.25, 0.75) * w, rng.uniform(0.2, 0.7) * h
    r = rng.uniform(0.18, 0.34) * max(w, h)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / r
    g = np.clip(1 - d, 0, 1) ** 1.7 * muc
    a = np.asarray(anh.convert("RGB"), np.float32)
    a = 255 - (255 - a) * (1 - g[..., None])          # screen blend
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")


def dau_giap_lai(anh: Image.Image, rng: random.Random) -> Image.Image:
    """Dấu đỏ đè lên chữ — đúng tình huống đề nêu."""
    w, h = anh.size
    lop = Image.new("RGBA", (int(w * 0.5), int(w * 0.5)), (0, 0, 0, 0))
    d = ImageDraw.Draw(lop)
    r = lop.width // 2 - 6
    c = lop.width // 2
    do = (185, 35, 45, 120)
    d.ellipse([c - r, c - r, c + r, c + r], outline=do, width=6)
    d.ellipse([c - r + 16, c - r + 16, c + r - 16, c + r - 16], outline=do, width=3)
    f = ImageFont.truetype(F_DAM, max(14, r // 5))
    d.text((c, c - r // 2), "UBND XÃ", font=f, fill=do, anchor="mm")
    d.text((c, c), "MÔ PHỎNG", font=f, fill=do, anchor="mm")
    d.text((c, c + r // 2), "KIỂM THỬ", font=f, fill=do, anchor="mm")
    lop = lop.rotate(rng.uniform(-30, 30), resample=Image.BICUBIC, expand=False)
    ra = anh.copy()
    ra.alpha_composite(lop, (int(rng.uniform(0.18, 0.5) * w), int(rng.uniform(0.15, 0.5) * h)))
    return ra


def nhieu(anh: Image.Image, sigma: float, rng: random.Random) -> Image.Image:
    a = np.asarray(anh.convert("RGB"), np.float32)
    r = np.random.default_rng(rng.randrange(1 << 30))
    a += r.normal(0, sigma, a.shape)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")


def qua_jpeg(anh: Image.Image, chat_luong: int) -> Image.Image:
    bo = io.BytesIO()
    anh.convert("RGB").save(bo, "JPEG", quality=chat_luong)
    bo.seek(0)
    return Image.open(bo).convert("RGBA")


def lam_xau(anh: Image.Image, muc: str, rng: random.Random) -> tuple[Image.Image, list[str]]:
    """Thang chất lượng 5 bậc. Mỗi bậc là một mô tả bằng lời, không phải một con số."""
    da_lam: list[str] = []

    def ghi(t: str) -> None:
        da_lam.append(t)

    if muc == "sach":
        anh = anh.rotate(rng.uniform(-0.6, 0.6), resample=Image.BICUBIC,
                         fillcolor=(255, 255, 255, 255)); ghi("nghieng<1do")
        anh = qua_jpeg(anh, 92); ghi("jpeg92")

    elif muc == "nhe":
        anh = anh.rotate(rng.uniform(-2.5, 2.5), resample=Image.BICUBIC,
                         fillcolor=(250, 250, 250, 255)); ghi("nghieng<3do")
        anh = anh.filter(ImageFilter.GaussianBlur(rng.uniform(0.6, 1.1))); ghi("nhoe_nhe")
        anh = anh_sang_khong_deu(anh, 0.14, rng); ghi("anh_sang_lech_nhe")
        anh = nhieu(anh, 3.0, rng); ghi("nhieu_nhe")
        anh = qua_jpeg(anh, 82); ghi("jpeg82")

    elif muc == "trung_binh":
        anh = phoi_canh(anh, rng.uniform(0.012, 0.03), rng); ghi("phoi_canh")
        anh = anh.filter(ImageFilter.GaussianBlur(rng.uniform(1.1, 1.8))); ghi("nhoe_tieu_cu")
        anh = anh_sang_khong_deu(anh, 0.3, rng); ghi("anh_sang_lech")
        anh = loa_sang(anh, 0.4, rng); ghi("loa_den")
        # đèn huỳnh quang: lệch màu xanh lục
        a = np.asarray(anh.convert("RGB"), np.float32) * np.array([0.94, 1.03, 0.93])
        anh = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
        ghi("lech_mau_huynh_quang")
        anh = nhieu(anh, 6.0, rng); ghi("nhieu_trung_binh")
        ti_le = rng.uniform(0.55, 0.7)
        anh = anh.resize((int(anh.width * ti_le), int(anh.height * ti_le)), Image.BILINEAR)
        ghi(f"giam_phan_giai_x{ti_le:.2f}")
        anh = qua_jpeg(anh, 62); ghi("jpeg62")

    elif muc == "nang":
        anh = phoi_canh(anh, rng.uniform(0.03, 0.055), rng); ghi("phoi_canh_manh")
        anh = dau_giap_lai(anh, rng); ghi("dau_giap_lai_de_len_chu")
        anh = nhoe_chuyen_dong(anh, rng.randint(9, 15), rng.uniform(0, 180)); ghi("nhoe_tay_run")
        anh = anh.filter(ImageFilter.GaussianBlur(rng.uniform(1.0, 1.6))); ghi("nhoe_tieu_cu")
        anh = loa_sang(anh, 0.78, rng); ghi("loa_den_manh")
        a = np.asarray(anh.convert("RGB"), np.float32) * rng.uniform(0.5, 0.68)
        anh = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
        ghi("thieu_sang")
        anh = nhieu(anh, 13.0, rng); ghi("nhieu_manh")
        ti_le = rng.uniform(0.36, 0.46)
        anh = anh.resize((int(anh.width * ti_le), int(anh.height * ti_le)), Image.BILINEAR)
        ghi(f"giam_phan_giai_x{ti_le:.2f}")
        anh = qua_jpeg(anh, 38); ghi("jpeg38")

    elif muc == MUC_KHONG_DOC_DUOC:
        anh = phoi_canh(anh, rng.uniform(0.06, 0.09), rng); ghi("phoi_canh_rat_manh")
        anh = nhoe_chuyen_dong(anh, rng.randint(26, 40), rng.uniform(0, 180)); ghi("nhoe_tay_run_rat_manh")
        anh = anh.filter(ImageFilter.GaussianBlur(rng.uniform(3.4, 5.0))); ghi("mat_net_hoan_toan")
        anh = loa_sang(anh, 0.95, rng); ghi("loa_chay_sang")
        a = np.asarray(anh.convert("RGB"), np.float32) * rng.uniform(0.22, 0.32)
        anh = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
        ghi("gan_nhu_toi")
        anh = nhieu(anh, 26.0, rng); ghi("nhieu_rat_manh")
        ti_le = rng.uniform(0.18, 0.24)
        anh = anh.resize((int(anh.width * ti_le), int(anh.height * ti_le)), Image.BILINEAR)
        ghi(f"giam_phan_giai_x{ti_le:.2f}")
        anh = qua_jpeg(anh, 22); ghi("jpeg22")
    else:
        raise ValueError(muc)

    return anh, da_lam


# ---------------------------------------------------------------------------
def sinh(seed_goc: int = 20260808) -> dict:
    THU_MUC_ANH.mkdir(parents=True, exist_ok=True)
    for cu in THU_MUC_ANH.glob("*.jpg"):
        cu.unlink()
    THU_MUC_NHAN.mkdir(parents=True, exist_ok=True)

    ban_ke: list[dict] = []
    stt = 0
    for ma_loai, phan_bo in KE_HOACH.items():
        for muc, so_luong in phan_bo.items():
            for k in range(so_luong):
                stt += 1
                seed = seed_goc + stt * 977
                rng = random.Random(seed)
                if ma_loai == "cccd":
                    nguoi = NGUOI[(stt - 1) % len(NGUOI)]
                    goc = ve_cccd(nguoi, rng)
                    su_that = {"so_dinh_danh": nguoi[0], "ho_ten": nguoi[1],
                               "ngay_sinh": nguoi[2], "noi_thuong_tru": nguoi[3]}
                else:
                    don = DON[(stt - 1) % len(DON)]
                    goc = ve_mau_01(don, rng)
                    su_that = {"ho_ten_nguoi_viet_don": don[0], "hinh_thuc": don[1],
                               "dien_tich_binh_quan": f"{don[2]} m²",
                               "thu_nhap_hang_thang": f"{don[3]} đồng"}

                anh, da_lam = lam_xau(goc, muc, rng)
                ten_tep = f"{ma_loai}_{muc}_{k + 1:02d}.jpg"
                anh.convert("RGB").save(THU_MUC_ANH / ten_tep, "JPEG", quality=95)

                ban_ke.append({
                    "id": ten_tep[:-4],
                    "tep": f"data/anh/{ten_tep}",
                    "doc_type": ma_loai,
                    "muc_chat_luong": muc,
                    "seed": seed,
                    "bien_dang": da_lam,
                    "kich_thuoc": list(anh.size),
                    "noi_dung_da_ve": su_that,
                })
                print(f"  {ten_tep:36s} {anh.size[0]}x{anh.size[1]}  {', '.join(da_lam)}")

    ban_ke_json = {
        "seed_goc": seed_goc,
        "canh_bao": ("Toàn bộ giấy tờ trong bộ này là mô phỏng. Số định danh dùng "
                     "tiền tố 000 (không phải mã tỉnh hợp lệ) nên không thể trùng "
                     "số của người thật. Không có ảnh giấy tờ thật nào được dùng."),
        "so_anh": len(ban_ke),
        "anh": ban_ke,
    }
    (THU_MUC_NHAN / "ban_ke_sinh.json").write_text(
        json.dumps(ban_ke_json, ensure_ascii=False, indent=2), encoding="utf-8")
    return ban_ke_json


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Sinh bộ ảnh kiểm thử (Bước 2)")
    ap.add_argument("--seed", type=int, default=20260808)
    a = ap.parse_args()
    kq = sinh(a.seed)
    print(f"\nĐã sinh {kq['so_anh']} ảnh vào {THU_MUC_ANH}")
    print(f"Bản kê: {THU_MUC_NHAN / 'ban_ke_sinh.json'}")
