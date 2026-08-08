"""Xuất báo cáo Markdown cho người KHÔNG đọc code.

Quy tắc viết báo cáo ở đây: mỗi bảng phải trả lời một câu hỏi nói được thành lời,
và câu hỏi đó viết ngay trên bảng.
"""

from __future__ import annotations

from .cham_diem import PHAI_TRICH_DUNG, PHAI_TU_CHOI
from .so_khop import LOI_HE_THONG

TEN_BAC = {
    "sach": "Sạch (chụp ngay ngắn, đủ sáng)",
    "nhe": "Nhiễu nhẹ (hơi nghiêng, hơi nhoè)",
    "trung_binh": "Nhiễu trung bình (phối cảnh, loá đèn, giảm phân giải)",
    "nang": "Nhiễu nặng (tay run, dấu giáp lai đè chữ, thiếu sáng)",
    "khong_doc_duoc": "Không đọc được (người cũng không đọc nổi)",
}


def _pt(x) -> str:
    return "—" if x is None else f"{x * 100:.1f}%"


def _bang(tieu_de: list[str], dong: list[list[str]]) -> str:
    ra = ["| " + " | ".join(tieu_de) + " |",
          "|" + "|".join("---" for _ in tieu_de) + "|"]
    ra += ["| " + " | ".join(d) + " |" for d in dong]
    return "\n".join(ra)


def bao_cao_markdown(kq: dict, meta: dict, gop: dict | None = None) -> str:
    t = kq["tom_tat"]
    b: list[str] = []
    b.append("# Báo cáo đo độ tin cậy mô hình trích xuất\n")
    b.append(f"- **Model đo**: `{meta['model']}` — {meta['phien_ban']}")
    b.append(f"- **Bộ dữ liệu**: {t['so_anh']} ảnh, {t['so_truong_tinh_diem']} trường tính điểm")
    b.append(f"- **Thời điểm chạy**: {meta.get('thoi_diem', '')}")
    b.append(f"- **Canary hạ tầng**: {meta.get('canary', '')}\n")

    # ---------------------------------------------------------------- kết luận
    so_doc_duoc = sum(1 for c in kq["chi_tiet"] if c["ky_vong"] == PHAI_TRICH_DUNG
                      and c["phan_quyet"] != LOI_HE_THONG)
    so_phai_tu_choi = sum(1 for c in kq["chi_tiet"] if c["ky_vong"] == PHAI_TU_CHOI
                          and c["phan_quyet"] != LOI_HE_THONG)
    b.append("## 1. Ba con số cần nhớ\n")
    b.append(_bang(
        ["Chỉ số", "Giá trị", "Nghĩa là gì"],
        [["Điểm tin cậy (có trọng số)", _pt(t["diem_tin_cay"]),
          "Chỉ số duy nhất dùng để so giữa các lần chạy. Tính trên cả "
          f"{so_doc_duoc} trường phải trích đúng và {so_phai_tu_choi} trường phải "
          "từ chối. Trường sai gây hậu quả pháp lý (số định danh, họ tên) được "
          "tính nặng gấp 3 lần."],
         ["Đúng trên trường người đọc được", _pt(t["accuracy_truong_doc_duoc"]),
          f"Trên {so_doc_duoc} trường mà người gán nhãn đọc được, "
          "model điền đúng bao nhiêu phần."],
         ["Đúng ở trường nghiêm trọng", _pt(t["accuracy_truong_nghiem_trong"]),
          "Riêng số định danh và họ tên. Sai ở đây nghĩa là hồ sơ của người khác."]]))
    b.append("")
    b.append(_bang(
        ["Hành vi", "Tỉ lệ", "Ghi chú"],
        [["Trả sai giá trị", _pt(t["ty_le_sai"]), "có giá trị nhưng khác nhãn"],
         ["Bỏ sót (im lặng dù ảnh đọc được)", _pt(t["ty_le_bo_sot"]),
          "không trả gì trong khi người đọc được"],
         ["AC3 — từ chối đúng trên ảnh không đọc được", _pt(t["ac3_ty_le_tu_choi_dung"]),
          "càng cao càng tốt, 100% là đạt AC3"],
         ["AC3 — **bịa dữ liệu**", _pt(t["ac3_ty_le_bia"]),
          f"{t['ac3_so_truong_bia']} trường. AC3 cấm tuyệt đối hành vi này."]]))
    b.append("")

    # --------------------------------------------------------- mức hồ sơ
    hs = kq.get("muc_ho_so")
    if hs:
        b.append("### Nhưng người dân không cảm nhận con số theo trường\n")
        b.append("*Họ cảm nhận: hồ sơ có bị trả về hay không. Một hồ sơ thiếu một "
                 "trường bắt buộc hỏng y như hồ sơ thiếu bốn trường.*\n")
        b.append(_bang(
            ["Ở mức hồ sơ", "Số", "Tỉ lệ"],
            [["Hồ sơ người đọc được", str(hs["so_ho_so_nguoi_doc_duoc"]), "100 %"],
             ["→ đi tiếp được", str(hs["so_di_tiep_duoc"]),
              _pt(hs["ty_le_di_tiep_duoc"])],
             ["→ **bị trả về bắt dân nộp lại dù người đọc được**",
              f"**{hs['so_day_ve_oan']}**", f"**{_pt(hs['ty_le_day_ve_oan'])}**"],
             ["AC3: ảnh không đọc được được đặt đúng trạng thái", "—",
              _pt(hs["ac3_khong_doc_duoc_dat_dung_trang_thai"])]]))
        if hs["day_ve_oan_theo_ly_do"]:
            b.append("\nLý do bị trả về oan: " + " · ".join(
                f"{v}× {k}" for k, v in
                sorted(hs["day_ve_oan_theo_ly_do"].items(), key=lambda x: -x[1])))
            b.append("\nTheo bậc ảnh: " + " · ".join(
                f"{TEN_BAC.get(k, k).split(' (')[0]} {v}"
                for k, v in sorted(hs["day_ve_oan_theo_bac"].items())))
        b.append("")

    # -------------------------------------------------------- sai ở đâu: bậc ảnh
    b.append("## 2. Sai ở đâu — theo chất lượng ảnh\n")
    b.append("*Câu hỏi: chất lượng ảnh tụt tới mức nào thì model gãy?*\n")
    b.append(_bang(
        ["Bậc chất lượng", "Số trường", "Đúng", "Sai", "Bỏ sót", "Từ chối đúng", "Bịa", "Điểm tin cậy"],
        [[TEN_BAC.get(k, k), str(v["so_truong"]), str(v["dung"]), str(v["sai"]),
          str(v["bo_sot"]), str(v["tu_choi_dung"]), str(v["bia"]), _pt(v["diem_tin_cay"])]
         for k, v in kq["theo_bac_chat_luong"].items()]))
    b.append("")

    b.append("## 3. Sai ở đâu — theo loại giấy tờ\n")
    b.append("*Câu hỏi: chữ in trên bố cục cố định và chữ viết tay trên biểu, "
             "cái nào là điểm yếu?*\n")
    b.append(_bang(
        ["Loại giấy tờ", "Số trường", "Đúng", "Sai", "Bỏ sót", "Bịa", "Điểm tin cậy"],
        [[k, str(v["so_truong"]), str(v["dung"]), str(v["sai"]), str(v["bo_sot"]),
          str(v["bia"]), _pt(v["diem_tin_cay"])]
         for k, v in kq["theo_loai_giay_to"].items()]))
    b.append("")

    # -------------------------------------------------------- sai ở đâu: trường
    b.append("## 4. Sai ở đâu — theo từng trường (xếp từ tệ nhất)\n")
    b.append(_bang(
        ["Trường", "Mức nghiêm trọng", "Đọc được", "Đúng", "Sai", "Bỏ sót",
         "Accuracy", "Conf TB model tự báo", "Kiểu sai hay gặp"],
        [[f"`{k}`", v["muc_do"], str(v["so_doc_duoc"]), str(v["dung"]), str(v["sai"]),
          str(v["bo_sot"]), _pt(v["accuracy_doc_duoc"]),
          "—" if v["conf_trung_binh"] is None else f"{v['conf_trung_binh']:.2f}",
          ", ".join(f"{a}×{c}" for a, c in
                    sorted(v["kieu_sai"].items(), key=lambda x: -x[1])[:3]) or "—"]
         for k, v in kq["theo_truong"].items()]))
    b.append("")
    if kq["kieu_sai"]:
        b.append("**Phân loại toàn bộ lỗi** (không phải \"sai bao nhiêu\" mà \"sai kiểu gì\"):\n")
        for k, v in sorted(kq["kieu_sai"].items(), key=lambda x: -x[1]):
            b.append(f"- `{k}`: {v}")
        b.append("")

    # ------------------------------------------------------------- hiệu chuẩn
    hc = kq["hieu_chuan_tin_cay"]
    b.append("## 5. Điểm tin cậy model tự báo có đáng tin không?\n")
    b.append("*Câu hỏi: cổng HITL lọc theo điểm tin cậy. Nếu điểm đó không phân biệt "
             "được đúng với sai thì cổng lọc nhầm.*\n")
    if hc.get("so_mau"):
        b.append(f"- Số trường có cả giá trị và điểm tin cậy: **{hc['so_mau']}**")
        b.append(f"- Conf trung bình khi ĐÚNG: **{hc['conf_tb_khi_dung']}** — "
                 f"khi SAI: **{hc['conf_tb_khi_sai']}**")
        b.append(f"- AUC phân biệt đúng/sai: **{hc['auc_phan_biet_dung_sai']}** "
                 f"(0.5 = điểm tin cậy vô dụng, 1.0 = hoàn hảo)")
        b.append(f"- ECE (độ lệch hiệu chuẩn): **{hc['ece']}** — "
                 f"conf lệch khỏi accuracy thực tế trung bình bấy nhiêu\n")
        b.append(_bang(["Khoảng conf", "Số trường", "Conf TB", "Accuracy thực tế", "Lệch"],
                       [[x["khoang"], str(x["so_mau"]), f"{x['conf_trung_binh']:.3f}",
                         _pt(x["accuracy_thuc_te"]), f"{x['lech']:+.3f}"]
                        for x in hc["thung"]]))
    else:
        b.append(f"Không đo được: {hc.get('ghi_chu')}")
    b.append("")

    # --------------------------------------------------------------- ngưỡng
    ch = kq["cong_hitl"]
    b.append("## 6. Đặt ngưỡng HITL ở đâu — bảng đánh đổi\n")
    b.append("*`rò rỉ` = trường SAI mà điểm tin cậy vẫn trên ngưỡng, tức là lọt qua "
             "cổng người duyệt và vào hồ sơ. `tự động` và `tái duyệt` tính trên cả "
             f"{ch['tong_truong_phai_dien']} trường phải có giá trị trong hồ sơ — "
             "trường model im lặng cũng về tay người y như trường bị gắn cờ.*\n")
    quet = [x for x in kq["quet_nguong_hitl"] if x["nguong"] in
            (0.0, 0.5, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1.0)]
    b.append(_bang(["Ngưỡng", "Tự động qua cổng", "Tỉ lệ tự động", "Tỉ lệ tái duyệt",
                    "Số rò rỉ", "Rò rỉ ở trường nghiêm trọng"],
                   [[f"{x['nguong']:.2f}",
                     f"{x['so_truong_tu_dong_qua']}/{x['tong_truong_phai_dien']}",
                     _pt(x["ty_le_tu_dong"]), _pt(x["ty_le_tai_duyet"]),
                     str(x["so_ro_ri"]), str(x["so_ro_ri_nghiem_trong"])] for x in quet]))
    b.append(f"\nVới ngưỡng đang dùng **{ch['nguong']}**: "
             f"{ch['tu_dong_qua_cong']}/{ch['tong_truong_phai_dien']} trường tự động qua "
             f"cổng ({_pt(ch['ty_le_tu_dong'])}), trong đó **{ch['so_ro_ri_qua_cong']}** "
             f"trường sai bị lọt. {ch['day_sang_nguoi_duyet']} trường về tay người duyệt: "
             f"{ch['trong_do_model_im_lang']} do model không trả gì, "
             f"{ch['trong_do_bi_gan_co_vi_conf_thap']} do bị gắn cờ vì conf dưới ngưỡng.")
    if ch["ro_ri_nghiem_trong"]:
        b.append("\n**Rò rỉ ở trường nghiêm trọng — đây là danh sách phải đọc từng dòng:**\n")
        b.append(_bang(["Ảnh", "Trường", "Nhãn", "Model trả", "Conf", "Kiểu sai"],
                       [[r["id"], r["ten_truong"], f"`{r['nhan']}`", f"`{r['model']}`",
                         f"{r['confidence']:.2f}", f"`{r['loai_sai']}`"]
                        for r in ch["ro_ri_nghiem_trong"]]))
    b.append("")

    # ------------------------------------------------------- vùng xám + hạ tầng
    b.append("## 7. Chỗ phép đo này KHÔNG kết luận được\n")
    b.append(f"- **Vùng xám: {t['so_truong_vung_xam']} trường.** Người gán nhãn không "
             "đọc được trường đó nhưng ảnh vẫn đọc được ở các trường khác (dấu giáp lai "
             "đè đúng ô giá trị). Không tính vào bất kỳ con số nào ở trên.")
    for x in kq["vung_xam"]:
        b.append(f"  - `{x['id']}` / `{x['ten_truong']}`: model trả `{x['model_tra']}` "
                 f"→ phán quyết `{x['phan_quyet']}` (đã loại khỏi accuracy)")
    b.append(f"- **Lỗi hạ tầng: {t['so_truong_loi_ha_tang']} trường.** Không gọi được "
             "model — lỗi của bộ đo, không phải của model, nên không tính vào accuracy.")
    b.append("")
    b.append("**Ba kiểu \"model không trả gì\" — trông giống nhau trong log, khác nhau "
             "về nguyên nhân:**\n")
    b.append(_bang(["Kiểu", "Số ảnh", "Nghĩa là gì", "Ai phải sửa"],
                   [["Từ chối theo chính sách",
                     str(t["so_anh_tu_choi_theo_chinh_sach"]),
                     "OCR ra quá ít chữ / conf quá thấp → cụm model chủ động im lặng",
                     "không ai — đây là hành vi đúng theo AC3"],
                    ["Đọc được chữ nhưng không neo được trường",
                     str(t["so_anh_doc_duoc_chu_nhung_khong_neo_duoc_truong"]),
                     "OCR ra chữ nhưng nhãn in bị đọc sai tới mức bộ tách không "
                     "tìm được mốc neo nào",
                     "kỹ sư — sửa bộ tách hoặc đổi cách gọi model"],
                    ["Lỗi hạ tầng", str(t["so_anh_loi_ha_tang"]),
                     "không gọi được model (thiếu binary, sai đường dẫn, vỡ ảnh)",
                     "kỹ sư — sửa trước khi tin bất kỳ con số nào"]]))
    for x in kq["loi_ha_tang"]:
        b.append(f"  - `{x['id']}`: {x['ghi_chu']}")
    b.append("")

    # ---------------------------------------------------------------- tốc độ
    b.append("## 8. Tốc độ\n")
    b.append(_bang(["Bậc chất lượng", "n", "Trung vị (ms)", "Min", "Max"],
                   [[TEN_BAC.get(k, k), str(v["n"]), str(v["trung_vi_ms"]),
                     str(v["min_ms"]), str(v["max_ms"])]
                    for k, v in kq["thoi_gian"].items() if k != "tat_ca"]))
    if "tat_ca" in kq["thoi_gian"]:
        v = kq["thoi_gian"]["tat_ca"]
        b.append(f"\nToàn bộ {v['n']} ảnh: trung vị {v['trung_vi_ms']} ms, "
                 f"tổng {v['tong_giay']} giây.")
    b.append("")

    # ------------------------------------------------------------ nhiều lần
    if gop and gop.get("so_lan", 0) > 1:
        b.append("## 9. Dao động giữa các lần chạy\n")
        b.append(f"*Chạy lại {gop['so_lan']} lần trên đúng bộ ảnh và tham số đó. "
                 "Sigma ở đây là cái quyết định ngưỡng fail của test tự động.*\n")
        b.append(_bang(["Chỉ số", "Trung bình", "Sigma", "Min", "Max"],
                       [[k, _pt(v["trung_binh"]), f"{v['sigma']:.4f}",
                         _pt(v["min"]), _pt(v["max"])]
                        for k, v in gop.items() if isinstance(v, dict)]))
        b.append("")

    return "\n".join(b)
