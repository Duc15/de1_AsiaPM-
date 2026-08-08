"""Bước 5 — biến bộ đo thành thứ chạy lại được và tự nói "tốt lên / xấu đi / không đổi".

Vấn đề đề nêu: test tự động cần đạt/không đạt, mô hình AI chỉ cho một con số dao
động. Cách bắc cầu ở đây là ba tầng, mỗi tầng chịu một loại nhiễu khác nhau:

  Tầng 1 — BẤT BIẾN. Những thứ không được phép sai dù nhiễu tới đâu:
           bịa dữ liệu = 0, không có lỗi hạ tầng, canary sống.
           Vi phạm là FAIL, không có biên độ tha thứ.

  Tầng 2 — BIÊN ĐỘ. Các chỉ số tổng chỉ FAIL khi tụt quá max(3·sigma, biên tối
           thiểu) so với baseline. Sigma KHÔNG phải hằng số đoán bừa: nó đo được
           bằng `do_luong.py --lap N` và chốt vào baseline. Model tất định thì
           sigma = 0 và cổng trở thành so khớp chính xác; model có nhiệt độ thì
           sigma > 0 và biên tự nới ra.

  Tầng 3 — CA CỤ THỂ. Trường nào đang đúng mà thành sai thì báo tên ảnh và tên
           trường, kể cả khi con số tổng vẫn trong biên. Chỉ số tổng che được
           việc "5 trường tốt lên, 5 trường xấu đi".

Baseline gắn chặt với dấu vân tay bộ dữ liệu. Đổi bộ ảnh mà không chốt lại
baseline thì so sánh vô nghĩa, nên trường hợp đó là FAIL ngay, không phải cảnh báo.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

GOC = Path(__file__).resolve().parents[1]
TEP_BASELINE = GOC / "ket_qua" / "baseline.json"

# Chỉ số nào bị canh theo biên độ, và canh theo chiều nào.
CHI_SO_CANH = {
    "diem_tin_cay": "cang_cao_cang_tot",
    "accuracy_truong_doc_duoc": "cang_cao_cang_tot",
    "accuracy_truong_nghiem_trong": "cang_cao_cang_tot",
    "ac3_ty_le_tu_choi_dung": "cang_cao_cang_tot",
    "ac3_ty_le_bia": "cang_thap_cang_tot",
}

TOT_LEN, XAU_DI, KHONG_DOI = "TỐT LÊN", "XẤU ĐI", "KHÔNG ĐỔI"


def dau_van_tay_du_lieu() -> str:
    """Băm CƠ SỞ ĐO: ảnh + phần nhãn thật sự quyết định điểm số.

    Cố ý KHÔNG băm nguyên tệp nhãn. Nhãn còn mang siêu dữ liệu của việc gán nhãn
    (giá trị người đọc lại đọc ra, ghi chú của họ) — bổ sung ghi chú không đổi
    một điểm nào của phép đo, nhưng nếu băm cả tệp thì baseline bị vô hiệu và
    người ta sẽ quen tay chốt lại baseline mà không xem vì sao. Baseline mất
    tác dụng cảnh báo đúng lúc cần nhất.

    Đã xảy ra thật: bổ sung lượt đọc lại cho 18 ảnh làm đổi dấu vân tay trong khi
    `gia_tri` và `ky_vong` của cả 132 điểm kiểm y nguyên.

    Nên chỉ băm: bytes ảnh, và với mỗi điểm kiểm là (ảnh, trường, giá trị nhãn,
    kỳ vọng hành vi). Đổi một nhãn hay thêm/bớt ảnh thì vân tay đổi — đúng lúc
    phải đổi.
    """
    h = hashlib.sha256()
    for tep in sorted((GOC / "data" / "anh").glob("*.jpg")):
        h.update(tep.name.encode())
        h.update(tep.read_bytes())
    for dong in (GOC / "data" / "nhan" / "nhan.jsonl").read_text(
            encoding="utf-8").splitlines():
        if not dong.strip():
            continue
        r = json.loads(dong)
        h.update(f"{r['id']}|{r['doc_type']}|{r['muc_chat_luong']}"
                 f"|{r['anh_doc_duoc']}".encode())
        for f in r["fields"]:
            h.update(f"{f['ten_truong']}|{f['gia_tri']}|{f['ky_vong']}".encode())
    return h.hexdigest()[:16]


def _ca_theo_truong(diem: dict) -> dict[str, str]:
    return {f"{c['id']}::{c['ten_truong']}": c["phan_quyet"] for c in diem["chi_tiet"]}


def chot_baseline(diem: dict, meta: dict, gop: dict | None) -> dict:
    bl = {
        "meta": meta,
        "dau_van_tay_du_lieu": dau_van_tay_du_lieu(),
        "chi_so": {k: diem["tom_tat"].get(k) for k in CHI_SO_CANH},
        "so_ro_ri_nghiem_trong": len(diem["cong_hitl"]["ro_ri_nghiem_trong"]),
        "sigma": {k: (gop.get(k, {}).get("sigma", 0.0) if gop else 0.0)
                  for k in CHI_SO_CANH},
        "so_lan_do_sigma": (gop or {}).get("so_lan", 1),
        "phan_quyet_tung_truong": _ca_theo_truong(diem),
    }
    TEP_BASELINE.parent.mkdir(parents=True, exist_ok=True)
    TEP_BASELINE.write_text(json.dumps(bl, ensure_ascii=False, indent=2), encoding="utf-8")
    return bl


def danh_gia(diem: dict, canary_ok: bool, cong: dict,
             baseline: dict | None = None) -> dict:
    """Trả về phán quyết đầy đủ. `dat = False` nghĩa là test FAIL."""
    t = diem["tom_tat"]
    loi: list[str] = []
    canh_bao: list[str] = []

    # ---- Tầng 1: bất biến ------------------------------------------------
    if not canary_ok:
        loi.append("BẤT BIẾN: canary hạ tầng vỡ — không kết luận gì về model được")
    if (t["ac3_ty_le_bia"] or 0) > cong["ac3_ty_le_bia_toi_da"]:
        loi.append(f"BẤT BIẾN (AC3): model bịa dữ liệu trên ảnh không đọc được — "
                   f"{t['ac3_so_truong_bia']} trường, mức cho phép "
                   f"{cong['ac3_ty_le_bia_toi_da']}")
    if t["so_truong_loi_ha_tang"] > 0:
        loi.append(f"BẤT BIẾN: {t['so_truong_loi_ha_tang']} trường lỗi hạ tầng — "
                   "sửa hạ tầng trước khi tin số đo")

    # ---- Cổng tuyệt đối (ngưỡng nghiệp vụ, không liên quan baseline) -----
    if (t["diem_tin_cay"] or 0) < cong["diem_tin_cay_toi_thieu"]:
        loi.append(f"CỔNG: điểm tin cậy {t['diem_tin_cay']:.4f} < "
                   f"{cong['diem_tin_cay_toi_thieu']}")
    if (t["accuracy_truong_nghiem_trong"] or 0) < cong["accuracy_truong_nghiem_trong_toi_thieu"]:
        loi.append(f"CỔNG: accuracy trường nghiêm trọng "
                   f"{t['accuracy_truong_nghiem_trong']:.4f} < "
                   f"{cong['accuracy_truong_nghiem_trong_toi_thieu']}")
    so_ro_ri = len(diem["cong_hitl"]["ro_ri_nghiem_trong"])
    if so_ro_ri > cong["so_ro_ri_nghiem_trong_toi_da"]:
        loi.append(f"CỔNG: {so_ro_ri} trường nghiêm trọng SAI mà vẫn lọt qua cổng HITL "
                   f"(mức cho phép {cong['so_ro_ri_nghiem_trong_toi_da']})")

    # ---- Tầng 2 + 3: so với baseline -------------------------------------
    so_sanh: dict[str, dict] = {}
    ca_xau_di: list[str] = []
    ca_tot_len: list[str] = []
    xu_huong = KHONG_DOI

    if baseline is None:
        canh_bao.append("Chưa có baseline — chỉ chạy cổng tuyệt đối. "
                        "Chốt baseline: python scripts/chot_baseline.py")
    elif baseline["dau_van_tay_du_lieu"] != dau_van_tay_du_lieu():
        loi.append("Bộ dữ liệu đã đổi so với baseline (dấu vân tay lệch). So sánh "
                   "hai bộ khác nhau là vô nghĩa — chốt lại baseline rồi chạy lại.")
    else:
        bien_toi_thieu = cong["bien_do_tut_cho_phep"]
        for k, chieu in CHI_SO_CANH.items():
            moi, cu = t.get(k), baseline["chi_so"].get(k)
            if moi is None or cu is None:
                continue
            sigma = baseline["sigma"].get(k) or 0.0
            bien = max(3 * sigma, bien_toi_thieu)
            lech = moi - cu if chieu == "cang_cao_cang_tot" else cu - moi
            vuot = lech < -bien
            so_sanh[k] = {"baseline": cu, "lan_nay": moi, "lech": round(lech, 4),
                          "sigma": sigma, "bien_cho_phep": round(bien, 4),
                          "tut_qua_bien": vuot}
            if vuot:
                loi.append(f"BIÊN ĐỘ: {k} tụt {abs(lech):.4f} (baseline {cu} → {moi}), "
                           f"quá biên {bien:.4f} = max(3·sigma={3 * sigma:.4f}, "
                           f"{bien_toi_thieu})")

        cu_ca = baseline["phan_quyet_tung_truong"]
        moi_ca = _ca_theo_truong(diem)
        tot = ("DUNG", "TU_CHOI_DUNG")
        for khoa, pq_cu in cu_ca.items():
            pq_moi = moi_ca.get(khoa)
            if pq_moi is None:
                continue
            if pq_cu in tot and pq_moi not in tot:
                ca_xau_di.append(f"{khoa}: {pq_cu} → {pq_moi}")
            elif pq_cu not in tot and pq_moi in tot:
                ca_tot_len.append(f"{khoa}: {pq_cu} → {pq_moi}")
        if ca_xau_di:
            canh_bao.append(f"{len(ca_xau_di)} trường từ đúng thành sai (xem ca_xau_di) "
                            "— con số tổng có thể vẫn trong biên nhưng hành vi đã đổi")

        tut = [k for k, v in so_sanh.items() if v["lech"] < -1e-9]
        len_ = [k for k, v in so_sanh.items() if v["lech"] > 1e-9]
        if any(v["tut_qua_bien"] for v in so_sanh.values()) or (ca_xau_di and not ca_tot_len):
            xu_huong = XAU_DI
        elif len_ and not tut and not ca_xau_di:
            xu_huong = TOT_LEN
        else:
            xu_huong = KHONG_DOI

    return {
        "dat": not loi,
        "xu_huong": xu_huong,
        "loi": loi,
        "canh_bao": canh_bao,
        "so_sanh_baseline": so_sanh,
        "ca_xau_di": ca_xau_di,
        "ca_tot_len": ca_tot_len,
        "tom_tat_lan_nay": t,
    }


def doc_baseline() -> dict | None:
    if not TEP_BASELINE.exists():
        return None
    return json.loads(TEP_BASELINE.read_text(encoding="utf-8"))
