"""Chốt sổ LỖI ĐÃ BIẾT cho bộ test theo dữ liệu.

    python scripts/chot_loi_da_biet.py

Vấn đề cần giải: 61/129 điểm kiểm đang KHÔNG ĐẠT vì model thật sự yếu. Nếu để
nguyên, bộ test đỏ rực và không ai đọc nữa — mà một bộ test luôn đỏ thì bằng
không có bộ test.

Cách xử lý chuẩn của kiểm thử tự động: mỗi điểm kiểm đang hỏng được gắn vào một
LỖI CÓ MÃ và đánh dấu `xfail(strict=True)`. Từ đó:

    điểm kiểm đang hỏng, vẫn hỏng   -> xfail   (im lặng, đã có mã lỗi theo dõi)
    điểm kiểm đang hỏng, bỗng ĐẠT   -> XPASS   -> ĐỎ, bắt phải đóng lỗi
    điểm kiểm đang ĐẠT, bỗng hỏng   -> FAIL    -> ĐỎ, hồi quy thật

Tức là bộ test chỉ đỏ khi hành vi ĐỔI, đúng thứ cần biết khi thay model.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]

from bo_do.chay import GOC  # noqa: E402

TEP = GOC / "data" / "nhan" / "loi_da_biet.json"

# Quy điểm kiểm hỏng về mã lỗi trong LOI-PHAT-HIEN.md. Thứ tự có ý nghĩa:
# luật đầu tiên khớp thì thắng.
QUY_VE_LOI = [
    (lambda c: c["ten_truong"] in ("ho_ten", "ho_ten_nguoi_viet_don")
     and c["loai_sai"] in ("sai_dau", "sai_vai_ky_tu", "thieu_hoac_thua_phan",
                           "sai_hoan_toan"), "LOI-01"),
    (lambda c: c["ten_truong"] == "hinh_thuc" and c["loai_sai"] == "chon_sai_o", "LOI-02"),
    (lambda c: c["loai_sai"] in ("sai_gia_tri_so", "sai_1_chu_so", "sai_so_chu_so",
                                 "khong_phai_so"), "LOI-05"),
    (lambda c: c["loai_sai"] == "im_lang_tren_anh_doc_duoc"
     and c["muc_chat_luong"] in ("trung_binh", "nang"), "LOI-03"),
    (lambda c: c["loai_sai"] == "im_lang_tren_anh_doc_duoc", "LOI-06"),
    (lambda c: c["loai_sai"] in ("lech_qua_nguong", "khong_phai_ngay",
                                 "sai_gia_tri_ngay"), "LOI-03"),
]


def quy_ve_loi(c: dict) -> str:
    for dieu_kien, ma in QUY_VE_LOI:
        if dieu_kien(c):
            return ma
    return "CHUA-PHAN-LOAI"


def chot(ten_model: str) -> dict:
    diem = json.loads((GOC / "ket_qua" / ten_model / "cham_diem.json")
                      .read_text(encoding="utf-8"))
    so: dict[str, dict] = {}
    for c in diem["chi_tiet"]:
        if c["ky_vong"] == "vung_xam":
            continue
        if c["phan_quyet"] in ("DUNG", "TU_CHOI_DUNG"):
            continue
        so[f"{c['id']}::{c['ten_truong']}"] = {
            "loi": quy_ve_loi(c),
            "phan_quyet": c["phan_quyet"],
            "loai_sai": c["loai_sai"],
            "nhan": c["nhan"],
            "model_tra": c["model"],
        }

    ra = {
        "_ghi_chu": ("Sổ lỗi đã biết cho tests/test_du_lieu.py. Mỗi khoá là một điểm "
                     "kiểm đang hỏng, gắn vào một mã lỗi trong LOI-PHAT-HIEN.md. "
                     "Sửa được lỗi nào thì xoá khoá đó đi — hoặc chạy lại script này."),
        "model": diem["meta"]["model"],
        "phien_ban": diem["meta"]["phien_ban"],
        "so_diem_kiem_hong": len(so),
        "theo_ma_loi": dict(Counter(v["loi"] for v in so.values())),
        "diem_kiem": dict(sorted(so.items())),
    }
    TEP.write_text(json.dumps(ra, ensure_ascii=False, indent=2), encoding="utf-8")
    return ra


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="tesseract")
    a = ap.parse_args()
    kq = chot(a.model)
    print(f"Đã chốt {kq['so_diem_kiem_hong']} điểm kiểm đang hỏng vào {TEP}")
    for ma, n in sorted(kq["theo_ma_loi"].items(), key=lambda x: -x[1]):
        print(f"  {ma:16s} {n}")
    if kq["theo_ma_loi"].get("CHUA-PHAN-LOAI"):
        print("\nCẢNH BÁO: có điểm kiểm hỏng chưa quy được về mã lỗi nào — "
              "bổ sung luật vào QUY_VE_LOI hoặc mở lỗi mới.")
