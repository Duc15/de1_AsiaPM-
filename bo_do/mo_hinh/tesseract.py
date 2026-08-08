"""Model đang được đo: Tesseract 5 (lang=vie) + một bộ tách trường neo theo nhãn in.

"Model" ở đây là cả cụm OCR + bộ tách, vì đó mới là thứ hệ thống ở mục 01 thật
sự dùng. Tesseract trả chữ; nó không trả trường có tên và điểm tin cậy.

Điểm tin cậy từng trường = trung bình conf của các từ tạo nên giá trị (Tesseract
cho conf mức từ), đưa về [0,1]. Đây là điểm do CHÍNH MODEL tự báo — bước 4 của
đề đòi kiểm xem nó có ăn khớp với đúng/sai thật hay không, nên nó không được
tính từ nhãn.

Chính sách từ chối (để hành vi đúng theo AC3 là khả thi): nếu ảnh cho quá ít từ
đọc được, hoặc conf trung bình toàn ảnh quá thấp, cụm này trả về rỗng kèm lý do
thay vì cố đoán.
"""

from __future__ import annotations

import difflib
import os
import re
import shutil
import time

import numpy as np
import pytesseract
from PIL import Image, ImageOps
from pytesseract import Output

from .. import chuan_hoa as ch
from ..schema import LOAI_GIAY_TO
from .co_so import KetQuaTrichXuat, TruongTraVe

_DUONG_DAN_MAC_DINH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Ngưỡng của chính sách từ chối. Đây là tham số của cụm model, không phải
# ngưỡng HITL của hệ thống (ngưỡng đó nằm trong cau_hinh.json).
TOI_THIEU_SO_TU = 8
TOI_THIEU_CONF_ANH = 30.0     # thang Tesseract 0..100
NGUONG_KHOP_MOC = 0.70
BE_RONG_CHUAN = 1700          # upscale để Tesseract đủ dpi
_LECH_DAU_DONG_TOI_DA = 8     # mốc neo phải nằm ở đầu dòng (xem _khop_moc_diem)


def _tim_tesseract() -> str:
    p = os.environ.get("TESSERACT_CMD") or shutil.which("tesseract") or _DUONG_DAN_MAC_DINH
    return p


# Font cho canary. Phải có glyph tiếng Việt và phải tìm được trên cả Windows lẫn
# Linux (CI), nếu không canary tự vỡ trên máy khác và bộ đo dừng vì lý do sai.
_UNG_VIEN_FONT = (
    "C:/Windows/Fonts/arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/Library/Fonts/Arial.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
)


def tim_font(co: int):
    """Font TrueType đầu tiên tìm được. Ném lỗi rõ ràng nếu máy không có font nào."""
    from PIL import ImageFont
    for duong_dan in _UNG_VIEN_FONT:
        if os.path.exists(duong_dan):
            return ImageFont.truetype(duong_dan, co)
    raise FileNotFoundError(
        "không tìm thấy font TrueType nào để dựng canary. Cài một trong: "
        + ", ".join(_UNG_VIEN_FONT))


def _chuan_bi(anh: Image.Image) -> Image.Image:
    """Tiền xử lý tối thiểu, giống nhau cho mọi ảnh.

    Cố ý KHÔNG tự động khử nhiễu/deskew theo từng ảnh: nếu tiền xử lý thay đổi
    theo chất lượng ảnh thì phép đo không còn đo model nữa, nó đo bộ tiền xử lý.
    """
    if anh.mode != "L":
        anh = anh.convert("L")
    if anh.width < BE_RONG_CHUAN:
        ti_le = BE_RONG_CHUAN / anh.width
        anh = anh.resize((BE_RONG_CHUAN, int(anh.height * ti_le)), Image.LANCZOS)
    return ImageOps.autocontrast(anh, cutoff=1)


class _Dong:
    __slots__ = ("tu", "text", "text_chuan", "vi_tri", "top", "cao")

    def __init__(self) -> None:
        self.tu: list[dict] = []

    def hoan_tat(self) -> None:
        self.text = " ".join(t["text"] for t in self.tu)
        self.vi_tri = []
        vt = 0
        for t in self.tu:
            self.vi_tri.append(vt)
            vt += len(t["text"]) + 1
        self.text_chuan = _chuan_moc(self.text)
        self.top = min(t["top"] for t in self.tu)
        self.cao = max(t["height"] for t in self.tu)


def _chuan_moc(s: str) -> str:
    """Chuẩn hoá dùng riêng cho việc khớp mốc neo: bỏ dấu, bỏ dấu câu, hạ chữ."""
    s = ch.bo_dau(ch.chuan_nfc(s)).lower()
    return re.sub(r"[^a-z0-9:/ ]", " ", s)


def _gom_dong(d: dict) -> list[_Dong]:
    dong: dict[tuple, _Dong] = {}
    for i, txt in enumerate(d["text"]):
        txt = (txt or "").strip()
        if not txt:
            continue
        try:
            conf = float(d["conf"][i])
        except (TypeError, ValueError):
            conf = -1.0
        if conf < 0:
            continue
        key = (d["block_num"][i], d["par_num"][i], d["line_num"][i])
        dong.setdefault(key, _Dong()).tu.append(
            {"text": txt, "conf": conf, "left": d["left"][i], "top": d["top"][i],
             "width": d["width"][i], "height": d["height"][i]})
    ra = []
    for _, dg in sorted(dong.items()):
        dg.tu.sort(key=lambda t: t["left"])
        dg.hoan_tat()
        ra.append(dg)
    ra.sort(key=lambda x: x.top)
    return ra


def _khop_moc_diem(dong: _Dong, moc: str) -> tuple[float, int] | None:
    """Trả về (điểm khớp, offset ký tự ngay sau mốc neo), hoặc None.

    Khớp mờ vì chính nhãn in cũng bị OCR sai ("Họ và tên" -> "Ho vò tên").

    Ràng buộc vị trí là bắt buộc, không phải tinh chỉnh cho đẹp: nhãn in nằm ở
    ĐẦU dòng trên cả hai loại giấy tờ. Bỏ ràng buộc này thì "Họ và tên:" khớp mờ
    được với "...Thành phố Hà Nội" ở giữa dòng địa chỉ, và bộ tách đi lấy giá trị
    từ dòng của trường khác. Lỗi đó đã xảy ra thật ở lần chạy đầu.
    """
    moc_c = _chuan_moc(moc).rstrip(": ").strip()
    if not moc_c:
        return None
    line = dong.text_chuan
    n = len(moc_c)
    tot_nhat, vi_tri = 0.0, None
    for bd in range(0, min(_LECH_DAU_DONG_TOI_DA, len(line)) + 1):
        for do_dai in {n - 2, n - 1, n, n + 1, n + 2}:
            if do_dai <= 2 or bd + do_dai > len(line):
                continue
            r = difflib.SequenceMatcher(None, line[bd:bd + do_dai], moc_c).ratio()
            if r > tot_nhat:
                tot_nhat, vi_tri = r, bd + do_dai
    if tot_nhat < NGUONG_KHOP_MOC or vi_tri is None:
        return None
    # Nhãn in luôn kết thúc bằng dấu hai chấm; nếu OCR còn giữ được nó thì tin nó.
    hai_cham = dong.text_chuan.find(":", max(0, vi_tri - 3))
    if 0 <= hai_cham <= vi_tri + 3:
        vi_tri = hai_cham + 1
    return tot_nhat, vi_tri


def _khop_moc(dong: _Dong, moc: str) -> int | None:
    kq = _khop_moc_diem(dong, moc)
    return None if kq is None else kq[1]


def _tu_sau_offset(dong: _Dong, offset: int) -> list[dict]:
    return [t for t, vt in zip(dong.tu, dong.vi_tri) if vt >= offset - 1]


CONF_TOI_THIEU_TU_RIA = 40.0


def _cat_ria_conf_thap(tu: list[dict]) -> list[dict]:
    """Bỏ các từ conf thấp ở ĐUÔI giá trị.

    Biểu in sẵn có dòng kẻ chấm chạy hết dòng; Tesseract đọc nó thành rác
    ("mm", "—¬", "_—X") dính vào đuôi giá trị. Luật này dùng chính điểm tin cậy
    của model để cắt, nên không phải tinh chỉnh riêng cho bộ ảnh này.

    Cố ý KHÔNG cắt ở đầu: chữ viết tay thường là phần conf thấp nhất của dòng,
    cắt đầu là cắt mất chính giá trị. Bản đầu tiên của hàm này cắt hai đầu và làm
    hai trường thu_nhap từ "sai" thành "bỏ sót" — tức là bộ đo tự tạo ra lỗi rồi
    quy cho model.
    """
    j = len(tu)
    while j > 1 and tu[j - 1]["conf"] < CONF_TOI_THIEU_TU_RIA:
        j -= 1
    return tu[:j]


def _hau_xu_ly(kieu: str, gia_tri: str) -> str | None:
    gia_tri = ch.gon_khoang_trang(gia_tri)
    if not gia_tri:
        return None
    if kieu == "so_dinh_danh":
        # Số định danh là dãy chữ số dài nhất trên dòng; Tesseract hay chèn
        # khoảng trắng vào giữa nên phải gom lại trước.
        chu_so = re.sub(r"[^\d]", "", gia_tri)
        return chu_so or None
    if kieu == "ngay":
        m = re.search(r"\d{1,2}\s*[/\-.]\s*\d{1,2}\s*[/\-.]\s*\d{2,4}", gia_tri)
        return re.sub(r"\s+", "", m.group(0)) if m else gia_tri
    if kieu == "so_luong":
        # Diện tích: lấy số đầu tiên, giữ phần thập phân. Đơn vị m² do schema
        # quy định nên không cần đọc ra.
        m = re.search(r"\d+(?:[.,]\d+)?", gia_tri)
        return m.group(0) if m else None
    if kieu == "tien":
        m = re.search(r"\d[\d.,\s]*\d|\d", gia_tri)
        return m.group(0).strip() if m else None
    if kieu == "ten_nguoi":
        s = re.sub(r"[^A-Za-zÀ-ỹĐđ\s'-]", " ", gia_tri)
        s = " ".join(t for t in s.split() if len(t) > 1 or t.upper() in ("Y", "A"))
        return s or None
    return gia_tri


def _nhan_phuong_an(text_dong: str, phuong_an: tuple[str, ...]) -> str | None:
    """Dòng OCR này là nhãn của phương án nào trong danh sách ô tích?

    Dòng thật có dạng "[] Mua", "X] Thuê mua", "IX] Thuê" — ký hiệu ô bị OCR đọc
    thành chữ, nên không so khớp cả dòng được. So khớp phần ĐUÔI dòng, và thử
    phương án dài trước ("thuê mua" trước "thuê") để không nhận nhầm.
    """
    dong_c = _chuan_moc(text_dong).strip()
    if not dong_c:
        return None
    for pa in sorted(phuong_an, key=len, reverse=True):
        pa_c = _chuan_moc(pa).strip()
        duoi = dong_c[-len(pa_c):]
        if duoi == pa_c or difflib.SequenceMatcher(None, duoi, pa_c).ratio() >= 0.8:
            return pa
    return None


def _hop_o_tich(dong: _Dong, nhan: str) -> tuple[tuple[int, int, int] | None, int, int]:
    """(hộp ô vuông nếu OCR đọc được nó, tâm y của nhãn, chiều cao dòng).

    Tesseract đọc chính ô vuông thành một "từ" rác ở đầu dòng ("[ ]", "5D",
    "[LI"), nên hộp của từ đó CHÍNH LÀ ô cần soi. Khi ô bị OCR bỏ qua hoặc dính
    liền vào nhãn, không có hộp nào — người gọi phải suy ra từ các dòng khác.
    """
    dau_nhan = _chuan_moc(nhan).split()[0]
    idx = None
    for i, t in enumerate(dong.tu):
        if difflib.SequenceMatcher(None, _chuan_moc(t["text"]).strip(), dau_nhan).ratio() >= 0.8:
            idx = i
            break
    cao = max(dong.cao, 12)
    if idx is None:
        return None, dong.top + cao // 2, cao
    t_nhan = dong.tu[idx]
    cy = t_nhan["top"] + t_nhan["height"] // 2
    truoc = dong.tu[:idx]
    if not truoc:
        return None, cy, cao
    x1 = min(t["left"] for t in truoc)
    x2 = max(t["left"] + t["width"] for t in truoc)
    y1 = min(t["top"] for t in truoc)
    y2 = max(t["top"] + t["height"] for t in truoc)
    return ((x1 + x2) // 2, (y1 + y2) // 2, max(cao, y2 - y1)), cy, cao


class MoHinhTesseract:
    ten = "tesseract"

    def __init__(self, lang: str = "vie", psm: int = 6,
                 nguong_muc_o_tich: float = 0.16) -> None:
        pytesseract.pytesseract.tesseract_cmd = _tim_tesseract()
        self.lang = lang
        self.psm = psm
        self.nguong_muc_o_tich = nguong_muc_o_tich
        try:
            self.phien_ban = f"tesseract-{pytesseract.get_tesseract_version()}-{lang}-psm{psm}"
        except Exception as e:                                    # noqa: BLE001
            self.phien_ban = f"tesseract-KHONG-XAC-DINH ({e})"

    # -- canary ----------------------------------------------------------
    def tu_kiem_tra(self) -> tuple[bool, str]:
        """Render một dòng chữ sạch rồi bắt Tesseract đọc lại.

        Nếu canary này fail thì mọi con số phía sau vô nghĩa: lỗi ở cách gọi
        model, không phải ở model. Bộ đo dừng ngay chứ không báo cáo 0%.
        """
        from PIL import ImageDraw
        try:
            anh = Image.new("L", (900, 140), 255)
            font = tim_font(56)
            ImageDraw.Draw(anh).text((20, 35), "CANARY 123456789012", font=font, fill=0)
            doc = pytesseract.image_to_string(anh, lang=self.lang,
                                              config=f"--psm {self.psm}")
            chu_so = re.sub(r"\D", "", doc)
            ok = "CANARY" in doc.upper() and chu_so == "123456789012"
            return ok, f"canary đọc được: {doc.strip()!r}"
        except Exception as e:                                    # noqa: BLE001
            return False, f"canary vỡ: {type(e).__name__}: {e}"

    # -- trích xuất ------------------------------------------------------
    def trich_xuat(self, duong_dan_anh: str, ma_loai: str) -> KetQuaTrichXuat:
        t0 = time.perf_counter()
        kq = KetQuaTrichXuat(doc_type=ma_loai)
        try:
            anh_goc = Image.open(duong_dan_anh)
            anh = _chuan_bi(anh_goc)
            data = pytesseract.image_to_data(anh, lang=self.lang,
                                             config=f"--psm {self.psm}",
                                             output_type=Output.DICT)
        except Exception as e:                                    # noqa: BLE001
            kq.thoi_gian_ms = (time.perf_counter() - t0) * 1000
            kq.loi_he_thong = f"{type(e).__name__}: {e}"
            return kq

        dong = _gom_dong(data)
        moi_tu = [t for dg in dong for t in dg.tu]
        conf_tb = float(np.mean([t["conf"] for t in moi_tu])) if moi_tu else 0.0
        kq.chan_doan = {"so_tu": len(moi_tu), "conf_tb_anh": round(conf_tb, 1),
                        "so_dong": len(dong)}

        # Chính sách từ chối — hiện thực hoá AC3 ở phía cụm model.
        if len(moi_tu) < TOI_THIEU_SO_TU or conf_tb < TOI_THIEU_CONF_ANH:
            kq.thoi_gian_ms = (time.perf_counter() - t0) * 1000
            kq.ly_do_tu_choi = (f"ảnh không đọc được: {len(moi_tu)} từ, "
                                f"conf trung bình {conf_tb:.1f} "
                                f"(ngưỡng {TOI_THIEU_SO_TU} từ / {TOI_THIEU_CONF_ANH})")
            return kq

        moc_khac = [m for t in LOAI_GIAY_TO[ma_loai].truong for m in t.moc_neo]
        for truong in LOAI_GIAY_TO[ma_loai].truong:
            if truong.kieu == "enum":
                tt = self._doc_o_tich(anh, dong, truong)
            else:
                tt = self._doc_truong_van_ban(dong, truong, moc_khac)
            if tt is not None:
                kq.fields.append(tt)

        if not kq.fields:
            # Đọc ra chữ nhưng không neo được trường nào. Đây KHÔNG phải từ chối
            # theo chính sách, cũng KHÔNG phải lỗi hạ tầng — nó là một kiểu gãy
            # riêng của cụm model, và phải đếm riêng mới thấy được.
            kq.chan_doan["bo_tach_khong_neo_duoc"] = True
            kq.chan_doan["van_ban_doc_duoc"] = " | ".join(d.text for d in dong)[:300]

        kq.thoi_gian_ms = (time.perf_counter() - t0) * 1000
        return kq

    def _doc_truong_van_ban(self, dong: list[_Dong], truong,
                            moc_khac: list[str]) -> TruongTraVe | None:
        # Chọn dòng khớp mốc neo TỐT NHẤT, không phải dòng khớp đầu tiên.
        ung_vien: list[tuple[float, int, int]] = []
        for i, dg in enumerate(dong):
            for moc in truong.moc_neo:
                kq = _khop_moc_diem(dg, moc)
                if kq is not None:
                    ung_vien.append((kq[0], i, kq[1]))
        ung_vien.sort(key=lambda x: -x[0])

        for _, i, off in ung_vien:
            dg = dong[i]
            tu = _tu_sau_offset(dg, off)
            if not tu and i + 1 < len(dong):
                tu = dong[i + 1].tu              # giá trị tràn xuống dòng dưới
            if truong.kieu == "dia_chi" and i + 1 < len(dong):
                # Nơi thường trú in trên hai dòng của thẻ. Vét thêm dòng dưới,
                # trừ khi dòng đó là mốc neo của một trường khác.
                sau = dong[i + 1]
                if not any(_khop_moc(sau, m) is not None for m in moc_khac):
                    tu = tu + sau.tu
            if not tu:
                continue
            tu = _cat_ria_conf_thap(tu)
            tho = " ".join(t["text"] for t in tu)
            gia_tri = _hau_xu_ly(truong.kieu, tho)
            if gia_tri is None:
                continue
            conf = float(np.mean([t["conf"] for t in tu])) / 100.0
            return TruongTraVe(truong.ten, gia_tri, round(conf, 4), "ocr")
        return None

    def _doc_o_tich(self, anh: Image.Image, dong: list[_Dong], truong) -> TruongTraVe | None:
        """Ô tích chọn: OCR đọc nhãn phương án, mật độ mực quyết định ô nào được tích.

        Hai tín hiệu độc lập nhau -> nguon = cross_validate. Đây là chỗ OCR thuần
        không làm được gì: Tesseract không "thấy" dấu tích, nó chỉ đọc ô vuông
        thành một ký tự ngẫu nhiên ("[ ]", "5D", "[L]Ì").

        Ba ô đều có cùng đường viền in sẵn, nên tín hiệu dùng được là mực TƯƠNG ĐỐI
        giữa ba ô, không phải một ngưỡng tuyệt đối. Chênh lệch quá nhỏ -> không
        đoán, trả None. Không đoán còn đỡ hơn đoán sai hình thức đăng ký.
        """
        px = np.asarray(anh, dtype=np.float32)

        # Chỉ xét vài dòng NGAY SAU mốc neo "Hình thức đăng ký:". Nếu không giới
        # hạn, tiêu đề đơn ("ĐƠN ĐĂNG KÝ MUA, THUÊ, THUÊ MUA") cũng khớp phương án.
        bd = None
        for i, dg in enumerate(dong):
            if any(_khop_moc(dg, m) is not None for m in truong.moc_neo):
                bd = i
                break
        if bd is None:
            return None

        thu: list[tuple[str, tuple[int, int, int] | None, int, int]] = []
        for dg in dong[bd:bd + 1 + len(truong.gia_tri_hop_le) * 2]:
            if len(dg.tu) > 4:
                continue                     # dòng dài không phải dòng ô tích
            nhan = _nhan_phuong_an(dg.text, truong.gia_tri_hop_le)
            if nhan is None:
                continue
            hop, cy, cao = _hop_o_tich(dg, nhan)
            thu.append((nhan, hop, cy, cao))
        if not thu:
            return None

        # Cửa sổ soi mực phải BẰNG NHAU ở cả ba ô, nếu không thì tỉ lệ mực của ô
        # to và ô nhỏ không so được với nhau. Ba ô trên biểu in thẳng cột, nên lấy
        # trung vị hoành độ và trung vị cỡ ô của những dòng OCR đọc được ô làm
        # chuẩn cho cả ba.
        co_hop = [h for _, h, _, _ in thu if h is not None]
        if not co_hop:
            return None
        cx_chuan = sorted(h[0] for h in co_hop)[len(co_hop) // 2]
        canh = sorted(h[2] for h in co_hop)[len(co_hop) // 2]
        nua = max(6, int(canh * 0.55))

        ung_vien: list[tuple[str, float]] = []
        for nhan, hop, cy, _ in thu:
            cx = hop[0] if hop is not None else cx_chuan
            y = hop[1] if hop is not None else cy
            vung = px[max(0, y - nua):y + nua, max(0, cx - nua):cx + nua]
            if vung.size:
                ung_vien.append((nhan, float((vung < 128).mean())))

        if not ung_vien:
            return None
        ung_vien.sort(key=lambda x: -x[1])
        tot, muc = ung_vien[0]
        muc_ke = ung_vien[1][1] if len(ung_vien) > 1 else 0.0
        bien = muc - muc_ke
        if muc < self.nguong_muc_o_tich or bien < 0.02:
            return None
        # Chặn trên 0.95: một luật đếm mực không có quyền báo chắc chắn 100%.
        conf = max(0.0, min(0.95, 0.55 + bien * 3))
        return TruongTraVe(truong.ten, tot, round(conf, 4), "cross_validate")


class MoHinhLuonTuChoi:
    """Model đối chứng: không bao giờ trả gì.

    Có mặt để chứng minh bộ đo không thể bị lừa — model này đạt 100% ở phần AC3
    nhưng 0% ở accuracy trên ảnh đọc được, nên điểm tổng của nó phải thấp. Nếu
    một ngày nó không thấp, bộ đo sai chứ không phải model tốt.
    """
    ten = "luon_tu_choi"
    phien_ban = "doi-chung-1.0"

    def trich_xuat(self, duong_dan_anh: str, ma_loai: str) -> KetQuaTrichXuat:
        return KetQuaTrichXuat(doc_type=ma_loai, thoi_gian_ms=0.0,
                               ly_do_tu_choi="model đối chứng luôn từ chối")

    def tu_kiem_tra(self) -> tuple[bool, str]:
        return True, "model đối chứng, không cần canary"


DANH_MUC = {
    "tesseract": lambda **kw: MoHinhTesseract(**kw),
    "tesseract_psm4": lambda **kw: MoHinhTesseract(psm=4, **kw),
    "tesseract_eng": lambda **kw: MoHinhTesseract(lang="eng", **kw),
    "luon_tu_choi": lambda **kw: MoHinhLuonTuChoi(),
}


def tao_mo_hinh(ten: str, **kw):
    if ten not in DANH_MUC:
        raise SystemExit(f"model {ten!r} chưa khai báo. Có: {', '.join(DANH_MUC)}")
    return DANH_MUC[ten](**kw)
