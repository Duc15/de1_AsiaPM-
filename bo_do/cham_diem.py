"""Bước 4 — tính điểm. Ba câu hỏi mà báo cáo phải trả lời được:

  1. Model sai Ở ĐÂU (loại giấy tờ nào, trường nào, bậc chất lượng nào, kiểu sai gì)
  2. Nó có tuân AC3 không (im lặng trên ảnh không đọc được, hay bịa ra giá trị)
  3. Điểm tin cậy nó tự báo có ăn khớp với đúng/sai thật không

Không có một con số duy nhất nào trả lời được cả ba, nên ở đây không có "accuracy"
đứng một mình. Có `diem_tin_cay` (có trọng số theo mức nghiêm trọng) để so sánh
giữa các lần chạy, và luôn kèm ba khối chi tiết bên dưới.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict

from .mo_hinh.co_so import KetQuaTrichXuat
from .schema import LOAI_GIAY_TO, MUC_CHAT_LUONG
from .so_khop import (BIA, BO_SOT, DUNG, LOI_HE_THONG, SAI, TU_CHOI_DUNG,
                      so_khop_truong)

PHAI_TRICH_DUNG = "phai_trich_dung"
PHAI_TU_CHOI = "phai_tu_choi"
VUNG_XAM = "vung_xam"

MOC_TIN_CAY = (0.0, 0.5, 0.6, 0.7, 0.8, 0.9, 1.01)


def cham(ban_ghi_nhan: list[dict],
         ket_qua: dict[str, KetQuaTrichXuat],
         nguong_hitl: float = 0.80) -> dict:
    """Chấm một lượt chạy. `ket_qua` khoá theo id ảnh."""
    chi_tiet: list[dict] = []

    for r in ban_ghi_nhan:
        kq = ket_qua.get(r["id"])
        loi = kq.loi_he_thong if kq is not None else "không có kết quả cho ảnh này"
        for f in r["fields"]:
            tt = f["ten_truong"]
            truong = LOAI_GIAY_TO[r["doc_type"]].lay(tt)
            gia_tri_model = kq.gia_tri(tt) if kq else None
            conf = kq.do_tin_cay(tt) if kq else None
            pq = so_khop_truong(r["doc_type"], tt, f["gia_tri"], gia_tri_model,
                                loi_he_thong=loi is not None)
            chi_tiet.append({
                "id": r["id"], "doc_type": r["doc_type"],
                "muc_chat_luong": r["muc_chat_luong"], "ten_truong": tt,
                "muc_do": truong.muc_do, "trong_so": truong.trong_so,
                "ky_vong": f["ky_vong"],
                "nhan": f["gia_tri"], "model": gia_tri_model,
                "confidence": conf, "nguon": kq.nguon(tt) if kq else None,
                "phan_quyet": pq.phan_quyet, "loai_sai": pq.loai_sai,
                "do_giong": pq.do_giong, "ghi_chu": pq.ghi_chu,
                "ly_do_tu_choi": kq.ly_do_tu_choi if kq else None,
                "bo_tach_khong_neo_duoc": bool(kq and kq.chan_doan.get("bo_tach_khong_neo_duoc")),
                "thoi_gian_ms": kq.thoi_gian_ms if kq else None,
            })

    # ---- tách ba nhóm trước khi cộng bất cứ thứ gì -------------------------
    ha_tang = [c for c in chi_tiet if c["phan_quyet"] == LOI_HE_THONG]
    xam = [c for c in chi_tiet if c["ky_vong"] == VUNG_XAM
           and c["phan_quyet"] != LOI_HE_THONG]
    tinh_diem = [c for c in chi_tiet if c["ky_vong"] in (PHAI_TRICH_DUNG, PHAI_TU_CHOI)
                 and c["phan_quyet"] != LOI_HE_THONG]

    doc_duoc = [c for c in tinh_diem if c["ky_vong"] == PHAI_TRICH_DUNG]
    khong_doc = [c for c in tinh_diem if c["ky_vong"] == PHAI_TU_CHOI]

    def ty_le(ds, dieu_kien) -> float | None:
        return round(sum(1 for c in ds if dieu_kien(c)) / len(ds), 4) if ds else None

    def co_trong_so(ds) -> float | None:
        tong = sum(c["trong_so"] for c in ds)
        if not tong:
            return None
        dung = sum(c["trong_so"] for c in ds if c["phan_quyet"] in (DUNG, TU_CHOI_DUNG))
        return round(dung / tong, 4)

    tom_tat = {
        "so_anh": len(ban_ghi_nhan),
        "so_truong_tinh_diem": len(tinh_diem),
        "so_truong_vung_xam": len(xam),
        "so_truong_loi_ha_tang": len(ha_tang),

        # Chỉ số chính để so giữa các lần chạy: có trọng số theo mức nghiêm trọng,
        # tính trên cả nhóm phải trích đúng và nhóm phải từ chối.
        "diem_tin_cay": co_trong_so(tinh_diem),

        "accuracy_truong_doc_duoc": ty_le(doc_duoc, lambda c: c["phan_quyet"] == DUNG),
        "accuracy_co_trong_so_doc_duoc": co_trong_so(doc_duoc),
        "ty_le_bo_sot": ty_le(doc_duoc, lambda c: c["phan_quyet"] == BO_SOT),
        "ty_le_sai": ty_le(doc_duoc, lambda c: c["phan_quyet"] == SAI),

        # AC3
        "ac3_ty_le_tu_choi_dung": ty_le(khong_doc, lambda c: c["phan_quyet"] == TU_CHOI_DUNG),
        "ac3_ty_le_bia": ty_le(khong_doc, lambda c: c["phan_quyet"] == BIA),
        "ac3_so_truong_bia": sum(1 for c in khong_doc if c["phan_quyet"] == BIA),
    }

    # accuracy riêng cho trường nghiêm trọng — con số mà nghiệp vụ NƠXH quan tâm nhất
    nghiem = [c for c in doc_duoc if c["muc_do"] == "nghiem_trong"]
    tom_tat["accuracy_truong_nghiem_trong"] = ty_le(nghiem, lambda c: c["phan_quyet"] == DUNG)

    # Ba kiểu "không trả gì" khác nhau về bản chất, đếm riêng từng kiểu.
    tom_tat["so_anh_tu_choi_theo_chinh_sach"] = len(
        {c["id"] for c in chi_tiet if c["ly_do_tu_choi"]})
    tom_tat["so_anh_doc_duoc_chu_nhung_khong_neo_duoc_truong"] = len(
        {c["id"] for c in chi_tiet if c["bo_tach_khong_neo_duoc"]})
    tom_tat["so_anh_loi_ha_tang"] = len(
        {c["id"] for c in chi_tiet if c["phan_quyet"] == LOI_HE_THONG})

    ket_qua_cham = {
        "tom_tat": tom_tat,
        "theo_bac_chat_luong": _theo_khoa(tinh_diem, "muc_chat_luong", MUC_CHAT_LUONG),
        "theo_loai_giay_to": _theo_khoa(tinh_diem, "doc_type", tuple(LOAI_GIAY_TO)),
        "theo_truong": _theo_truong(tinh_diem),
        "kieu_sai": dict(Counter(c["loai_sai"] for c in doc_duoc
                                 if c["phan_quyet"] in (SAI, BO_SOT) and c["loai_sai"])),
        "hieu_chuan_tin_cay": _hieu_chuan(doc_duoc),
        "quet_nguong_hitl": _quet_nguong(doc_duoc, khong_doc),
        "nguong_hitl_dang_dung": nguong_hitl,
        "cong_hitl": _cong_hitl(doc_duoc, khong_doc, nguong_hitl),
        "thoi_gian": _thoi_gian(ban_ghi_nhan, ket_qua),
        "loi_ha_tang": [{"id": c["id"], "ghi_chu": c["ghi_chu"]} for c in ha_tang][:20],
        "vung_xam": [{"id": c["id"], "ten_truong": c["ten_truong"],
                      "model_tra": c["model"], "phan_quyet": c["phan_quyet"]} for c in xam],
        "chi_tiet": chi_tiet,
    }
    return ket_qua_cham


def _theo_khoa(ds: list[dict], khoa: str, thu_tu: tuple[str, ...]) -> dict:
    nhom: dict[str, list[dict]] = defaultdict(list)
    for c in ds:
        nhom[c[khoa]].append(c)
    ra = {}
    for k in thu_tu:
        g = nhom.get(k)
        if not g:
            continue
        dem = Counter(c["phan_quyet"] for c in g)
        tong_ts = sum(c["trong_so"] for c in g)
        dung_ts = sum(c["trong_so"] for c in g if c["phan_quyet"] in (DUNG, TU_CHOI_DUNG))
        ra[k] = {
            "so_truong": len(g),
            "dung": dem[DUNG], "sai": dem[SAI], "bo_sot": dem[BO_SOT],
            "tu_choi_dung": dem[TU_CHOI_DUNG], "bia": dem[BIA],
            "diem_tin_cay": round(dung_ts / tong_ts, 4) if tong_ts else None,
        }
    return ra


def _theo_truong(ds: list[dict]) -> dict:
    nhom: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for c in ds:
        nhom[(c["doc_type"], c["ten_truong"])].append(c)
    ra = {}
    for (dt, tt), g in nhom.items():
        dem = Counter(c["phan_quyet"] for c in g)
        doc_duoc = [c for c in g if c["ky_vong"] == PHAI_TRICH_DUNG]
        conf = [c["confidence"] for c in g if c["confidence"] is not None]
        ra[f"{dt}.{tt}"] = {
            "muc_do": g[0]["muc_do"],
            "so_truong": len(g),
            "so_doc_duoc": len(doc_duoc),
            "dung": dem[DUNG], "sai": dem[SAI], "bo_sot": dem[BO_SOT],
            "tu_choi_dung": dem[TU_CHOI_DUNG], "bia": dem[BIA],
            "accuracy_doc_duoc": (round(dem[DUNG] / len(doc_duoc), 4)
                                  if doc_duoc else None),
            "conf_trung_binh": round(sum(conf) / len(conf), 4) if conf else None,
            "kieu_sai": dict(Counter(c["loai_sai"] for c in doc_duoc
                                     if c["phan_quyet"] in (SAI, BO_SOT) and c["loai_sai"])),
        }
    return dict(sorted(ra.items(), key=lambda kv: (kv[1]["accuracy_doc_duoc"] is not None,
                                                   kv[1]["accuracy_doc_duoc"] or 0)))


def _hieu_chuan(doc_duoc: list[dict]) -> dict:
    """Điểm tin cậy model tự báo có ăn khớp với đúng/sai thật không.

    Chỉ xét những trường model CÓ trả giá trị — chỗ nó im lặng thì không có điểm
    tin cậy nào để hiệu chuẩn.
    """
    co_conf = [c for c in doc_duoc
               if c["confidence"] is not None and c["phan_quyet"] in (DUNG, SAI)]
    if not co_conf:
        return {"so_mau": 0, "ghi_chu": "không có trường nào vừa có giá trị vừa có conf"}

    thung = []
    ece = 0.0
    for i in range(len(MOC_TIN_CAY) - 1):
        lo, hi = MOC_TIN_CAY[i], MOC_TIN_CAY[i + 1]
        g = [c for c in co_conf if lo <= c["confidence"] < hi]
        if not g:
            continue
        acc = sum(1 for c in g if c["phan_quyet"] == DUNG) / len(g)
        conf_tb = sum(c["confidence"] for c in g) / len(g)
        ece += len(g) / len(co_conf) * abs(acc - conf_tb)
        thung.append({"khoang": f"[{lo:.2f},{min(hi, 1.0):.2f})", "so_mau": len(g),
                      "conf_trung_binh": round(conf_tb, 4),
                      "accuracy_thuc_te": round(acc, 4),
                      "lech": round(conf_tb - acc, 4)})

    dung_conf = [c["confidence"] for c in co_conf if c["phan_quyet"] == DUNG]
    sai_conf = [c["confidence"] for c in co_conf if c["phan_quyet"] == SAI]
    # AUC = P(conf của một trường đúng > conf của một trường sai). 0.5 = vô dụng.
    auc = None
    if dung_conf and sai_conf:
        thang = sum((1.0 if a > b else 0.5 if a == b else 0.0)
                    for a in dung_conf for b in sai_conf)
        auc = round(thang / (len(dung_conf) * len(sai_conf)), 4)

    return {
        "so_mau": len(co_conf),
        "ece": round(ece, 4),
        "auc_phan_biet_dung_sai": auc,
        "conf_tb_khi_dung": round(sum(dung_conf) / len(dung_conf), 4) if dung_conf else None,
        "conf_tb_khi_sai": round(sum(sai_conf) / len(sai_conf), 4) if sai_conf else None,
        "thung": thung,
    }


def _quet_nguong(doc_duoc: list[dict], khong_doc: list[dict]) -> list[dict]:
    """Chọn ngưỡng HITL là một đánh đổi, không phải một hằng số đẹp.

    ro_ri     = trường SAI hoặc BỊA nhưng conf >= ngưỡng -> lọt vào hồ sơ
    tai_duyet = phần việc còn lại trên tay người

    Mẫu số của tái duyệt là toàn bộ trường PHẢI CÓ giá trị trong hồ sơ (nhóm
    phai_trich_dung), không phải chỉ những trường model chịu trả lời. Trường model
    im lặng cũng về tay người duyệt y như trường bị gắn cờ — bỏ nó khỏi mẫu số là
    tự khai giảm chi phí nhân sự. Bản đầu của hàm này chia cho 66 thay vì 105 và
    báo tái duyệt 25,8% ở ngưỡng 0,8, trong khi con số thật là 53,3%.
    """
    tong_phai_dien = len(doc_duoc)
    co_gia_tri = [c for c in doc_duoc + khong_doc
                  if c["model"] is not None and c["confidence"] is not None]
    if not co_gia_tri or not tong_phai_dien:
        return []
    ra = []
    for i in range(0, 21):
        t = i / 20
        tren = [c for c in co_gia_tri if c["confidence"] >= t]
        ro_ri = [c for c in tren if c["phan_quyet"] in (SAI, BIA)]
        ro_ri_nghiem = [c for c in ro_ri if c["muc_do"] == "nghiem_trong"]
        tu_dong = [c for c in tren if c["ky_vong"] == PHAI_TRICH_DUNG]
        ra.append({
            "nguong": round(t, 2),
            "so_truong_tu_dong_qua": len(tu_dong),
            "tong_truong_phai_dien": tong_phai_dien,
            "ty_le_tu_dong": round(len(tu_dong) / tong_phai_dien, 4),
            "ty_le_tai_duyet": round(1 - len(tu_dong) / tong_phai_dien, 4),
            "so_ro_ri": len(ro_ri),
            "so_ro_ri_nghiem_trong": len(ro_ri_nghiem),
            "ty_le_ro_ri_trong_so_tu_dong_qua": round(len(ro_ri) / len(tren), 4) if tren else 0.0,
        })
    return ra


def _cong_hitl(doc_duoc: list[dict], khong_doc: list[dict], nguong: float) -> dict:
    co_gia_tri = [c for c in doc_duoc + khong_doc if c["model"] is not None]
    tren = [c for c in co_gia_tri if (c["confidence"] or 0) >= nguong]
    ro_ri = [c for c in tren if c["phan_quyet"] in (SAI, BIA)]
    tu_dong = [c for c in tren if c["ky_vong"] == PHAI_TRICH_DUNG]
    im_lang = [c for c in doc_duoc if c["model"] is None]
    return {
        "nguong": nguong,
        "tong_truong_phai_dien": len(doc_duoc),
        "so_truong_model_tra_gia_tri": len(co_gia_tri),
        "tu_dong_qua_cong": len(tu_dong),
        "day_sang_nguoi_duyet": len(doc_duoc) - len(tu_dong),
        "trong_do_model_im_lang": len(im_lang),
        "trong_do_bi_gan_co_vi_conf_thap": len(doc_duoc) - len(tu_dong) - len(im_lang),
        "ty_le_tu_dong": round(len(tu_dong) / len(doc_duoc), 4) if doc_duoc else None,
        "so_ro_ri_qua_cong": len(ro_ri),
        "ro_ri_nghiem_trong": [{"id": c["id"], "ten_truong": c["ten_truong"],
                                "nhan": c["nhan"], "model": c["model"],
                                "confidence": c["confidence"],
                                "loai_sai": c["loai_sai"]}
                               for c in ro_ri if c["muc_do"] == "nghiem_trong"],
    }


def _thoi_gian(ban_ghi_nhan: list[dict], ket_qua: dict[str, KetQuaTrichXuat]) -> dict:
    theo_bac: dict[str, list[float]] = defaultdict(list)
    for r in ban_ghi_nhan:
        kq = ket_qua.get(r["id"])
        if kq is not None and kq.loi_he_thong is None:
            theo_bac[r["muc_chat_luong"]].append(kq.thoi_gian_ms)
    ra = {}
    for k, v in theo_bac.items():
        v = sorted(v)
        ra[k] = {"n": len(v), "trung_vi_ms": round(v[len(v) // 2], 1),
                 "min_ms": round(v[0], 1), "max_ms": round(v[-1], 1)}
    tat_ca = sorted(x for v in theo_bac.values() for x in v)
    if tat_ca:
        ra["tat_ca"] = {"n": len(tat_ca),
                        "trung_vi_ms": round(tat_ca[len(tat_ca) // 2], 1),
                        "tong_giay": round(sum(tat_ca) / 1000, 1)}
    return ra


def muc_ho_so(ban_ghi_nhan: list[dict], so_bang_chung: dict) -> dict:
    """Chấm ở mức HỒ SƠ, không phải mức trường.

    Vì sao cần riêng: người dân không cảm nhận "41,9 % trường đúng". Họ cảm nhận
    "hồ sơ của tôi bị trả về, phải chụp lại và đi lại một lần nữa". Một hồ sơ
    thiếu một trường bắt buộc hỏng y như hồ sơ thiếu bốn trường, nên trung bình
    theo trường che mất tác động thật.

    Chỉ số quan trọng nhất ở đây là `ty_le_day_ve_oan`: hồ sơ mà NGƯỜI đọc được
    nhưng hệ thống vẫn bắt dân nộp lại.
    """
    theo_id = {h["id"]: h for h in so_bang_chung["ho_so"]}
    doc_duoc = [r for r in ban_ghi_nhan if r["anh_doc_duoc"]]
    khong_doc = [r for r in ban_ghi_nhan if not r["anh_doc_duoc"]]

    def can_bo_sung(ds):
        return [r for r in ds
                if theo_id.get(r["id"], {}).get("trang_thai_ho_so") == "can_bo_sung"]

    oan = can_bo_sung(doc_duoc)
    dung = can_bo_sung(khong_doc)

    ly_do = Counter()
    for r in oan:
        ly_do[(theo_id[r["id"]]["ly_do"] or "").split(":")[0]] += 1
    theo_bac = Counter(r["muc_chat_luong"] for r in oan)

    return {
        "so_ho_so": len(ban_ghi_nhan),
        "so_ho_so_nguoi_doc_duoc": len(doc_duoc),
        "so_day_ve_oan": len(oan),
        "ty_le_day_ve_oan": round(len(oan) / len(doc_duoc), 4) if doc_duoc else None,
        "so_di_tiep_duoc": len(doc_duoc) - len(oan),
        "ty_le_di_tiep_duoc": (round((len(doc_duoc) - len(oan)) / len(doc_duoc), 4)
                               if doc_duoc else None),
        # AC3 đòi ảnh không đọc được PHẢI bị đặt trạng thái cần bổ sung.
        "ac3_khong_doc_duoc_dat_dung_trang_thai": (
            round(len(dung) / len(khong_doc), 4) if khong_doc else None),
        "day_ve_oan_theo_bac": dict(theo_bac),
        "day_ve_oan_theo_ly_do": dict(ly_do),
        "danh_sach_day_ve_oan": [r["id"] for r in oan],
    }


def gop_nhieu_lan(cac_lan: list[dict]) -> dict:
    """Chạy N lần rồi tính trung bình / độ lệch chuẩn cho các chỉ số chính.

    Đây là cầu nối sang Bước 5: test tự động cần một con số ổn định, model cho
    một con số dao động. Không biết sigma thì không đặt được ngưỡng fail.
    """
    khoa = ["diem_tin_cay", "accuracy_truong_doc_duoc", "accuracy_truong_nghiem_trong",
            "ac3_ty_le_tu_choi_dung", "ac3_ty_le_bia"]
    ra: dict[str, dict] = {"so_lan": len(cac_lan)}
    for k in khoa:
        v = [l["tom_tat"][k] for l in cac_lan if l["tom_tat"].get(k) is not None]
        if not v:
            continue
        tb = sum(v) / len(v)
        sigma = math.sqrt(sum((x - tb) ** 2 for x in v) / len(v)) if len(v) > 1 else 0.0
        ra[k] = {"trung_binh": round(tb, 4), "sigma": round(sigma, 4),
                 "min": round(min(v), 4), "max": round(max(v), 4), "cac_lan": v}
    return ra
