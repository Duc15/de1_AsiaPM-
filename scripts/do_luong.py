"""Bước 4 — chạy model trên bộ ảnh, chấm điểm, xuất báo cáo. Một lệnh.

    python scripts/do_luong.py
    python scripts/do_luong.py --model tesseract --lap 3    # đo cả dao động giữa các lần
    python scripts/do_luong.py --model luon_tu_choi         # model đối chứng

Ra:
    ket_qua/<model>/ket_qua_tho.json     nguyên văn model trả về, từng ảnh
    ket_qua/<model>/cham_diem.json       toàn bộ số đo, máy đọc được
    ket_qua/<model>/bao_cao.md           báo cáo cho người không đọc code
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]

from bo_do.bao_cao import bao_cao_markdown  # noqa: E402
from bo_do.cham_diem import muc_ho_so  # noqa: E402
from bo_do.chay import GOC, do, doc_nhan  # noqa: E402
from bo_do.so_bang_chung import ghi_ra_dia, lap_so_bang_chung  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="Đo độ tin cậy model trích xuất (Bước 4)")
    ap.add_argument("--model", default="tesseract")
    ap.add_argument("--lap", type=int, default=1,
                    help="chạy lại N lần để đo dao động giữa các lần chạy")
    ap.add_argument("--nguong-hitl", type=float, default=None)
    ap.add_argument("--ra", default=None, help="thư mục ghi kết quả")
    a = ap.parse_args()

    print(f"Model: {a.model} | bộ dữ liệu: data/anh | số lần lặp: {a.lap}\n")
    kq = do(a.model, lap=a.lap, nguong_hitl=a.nguong_hitl)

    print(f"\nCanary hạ tầng: {'OK' if kq['canary_ok'] else 'VỠ'} — {kq['canary']}")
    if not kq["canary_ok"]:
        print("\nDỪNG. Canary vỡ nghĩa là lỗi ở cách gọi model, không phải ở model.\n"
              "Mọi con số đo lúc này đều vô nghĩa. Sửa hạ tầng rồi chạy lại.")
        return 2

    diem, meta, gop = kq["diem"], kq["meta"], kq["gop"]
    thu_muc = Path(a.ra) if a.ra else GOC / "ket_qua" / a.model
    thu_muc.mkdir(parents=True, exist_ok=True)

    (thu_muc / "ket_qua_tho.json").write_text(json.dumps(
        {"meta": meta, "theo_anh": {k: v.to_dict() for k, v in (kq["tho"] or {}).items()}},
        ensure_ascii=False, indent=2), encoding="utf-8")
    # AC1/AC2/AC3 — hợp đồng đầu ra, sinh độc lập với nhãn (xem bo_do/so_bang_chung.py)
    ban_ghi = doc_nhan()
    so = lap_so_bang_chung(ban_ghi, kq["tho"] or {}, meta, meta["nguong_hitl"])
    ghi_ra_dia(so, thu_muc)
    diem["muc_ho_so"] = muc_ho_so(ban_ghi, so)

    (thu_muc / "cham_diem.json").write_text(json.dumps(
        {"meta": meta, **diem, "gop_nhieu_lan": gop},
        ensure_ascii=False, indent=2), encoding="utf-8")
    (thu_muc / "bao_cao.md").write_text(
        bao_cao_markdown(diem, meta, gop), encoding="utf-8")

    t = diem["tom_tat"]
    print(f"\n{'=' * 66}")
    print(f"Điểm tin cậy (có trọng số)        : {_pt(t['diem_tin_cay'])}")
    print(f"Đúng / trường người đọc được      : {_pt(t['accuracy_truong_doc_duoc'])}")
    print(f"Đúng / trường nghiêm trọng        : {_pt(t['accuracy_truong_nghiem_trong'])}")
    print(f"AC3 từ chối đúng                  : {_pt(t['ac3_ty_le_tu_choi_dung'])}")
    print(f"AC3 bịa dữ liệu                   : {_pt(t['ac3_ty_le_bia'])} "
          f"({t['ac3_so_truong_bia']} trường)")
    print(f"Rò rỉ qua cổng HITL @{meta['nguong_hitl']}         : "
          f"{len(diem['cong_hitl']['ro_ri_nghiem_trong'])} trường nghiêm trọng "
          f"/ {diem['cong_hitl']['so_ro_ri_qua_cong']} tổng")
    print(f"Vùng xám (không kết luận được)    : {t['so_truong_vung_xam']} trường")
    print(f"Ảnh từ chối theo chính sách       : {t['so_anh_tu_choi_theo_chinh_sach']}")
    print(f"Ảnh đọc ra chữ mà không neo được  : "
          f"{t['so_anh_doc_duoc_chu_nhung_khong_neo_duoc_truong']}")
    print(f"Ảnh lỗi hạ tầng                   : {t['so_anh_loi_ha_tang']}")
    hs = diem["muc_ho_so"]
    print("-" * 66)
    print(f"MỨC HỒ SƠ — hồ sơ người đọc được  : {hs['so_ho_so_nguoi_doc_duoc']}")
    print(f"  đi tiếp được                    : {hs['so_di_tiep_duoc']} "
          f"({_pt(hs['ty_le_di_tiep_duoc'])})")
    print(f"  BỊ TRẢ VỀ BẮT DÂN NỘP LẠI       : {hs['so_day_ve_oan']} "
          f"({_pt(hs['ty_le_day_ve_oan'])})")
    if gop:
        print("-" * 66)
        for k, v in gop.items():
            if isinstance(v, dict):
                print(f"  dao động {k}: {v['trung_binh']:.4f} ± {v['sigma']:.4f} "
                      f"({gop['so_lan']} lần)")
    print(f"{'=' * 66}")
    print(f"Báo cáo: {thu_muc / 'bao_cao.md'}")
    return 0


def _pt(x) -> str:
    return "—" if x is None else f"{x * 100:5.1f}%"


if __name__ == "__main__":
    raise SystemExit(main())
