"""Chỗ duy nhất biết cách chạy một lượt đo. CLI, test hồi quy và CI đều gọi vào đây.

Tách ra để test hồi quy không sao chép lại logic chạy — nếu sao chép, một ngày nào
đó bộ đo và bộ test sẽ đo hai thứ khác nhau mà không ai biết.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .cham_diem import cham, gop_nhieu_lan
from .mo_hinh.tesseract import tao_mo_hinh

GOC = Path(__file__).resolve().parents[1]
TEP_NHAN = GOC / "data" / "nhan" / "nhan.jsonl"
TEP_CAU_HINH = GOC / "cau_hinh.json"


def doc_cau_hinh() -> dict:
    return json.loads(TEP_CAU_HINH.read_text(encoding="utf-8"))


def doc_nhan() -> list[dict]:
    if not TEP_NHAN.exists():
        raise SystemExit("Chưa có nhãn. Chạy: python scripts/sinh_du_lieu.py "
                         "&& python scripts/gan_nhan.py")
    return [json.loads(d) for d in TEP_NHAN.read_text(encoding="utf-8").splitlines()
            if d.strip()]


def chay_mot_lan(mo_hinh, ban_ghi: list[dict], in_tien_do: bool = True) -> dict:
    ra = {}
    for i, r in enumerate(ban_ghi, 1):
        kq = mo_hinh.trich_xuat(str(GOC / r["tep"]), r["doc_type"])
        ra[r["id"]] = kq
        if in_tien_do:
            if kq.loi_he_thong:
                trang_thai = f"LỖI HẠ TẦNG: {kq.loi_he_thong}"
            elif kq.ly_do_tu_choi:
                trang_thai = (f"từ chối ({kq.chan_doan.get('so_tu')} từ, "
                              f"conf {kq.chan_doan.get('conf_tb_anh')})")
            elif kq.chan_doan.get("bo_tach_khong_neo_duoc"):
                trang_thai = "đọc được chữ nhưng KHÔNG neo được trường nào"
            else:
                trang_thai = f"{len(kq.fields)} trường"
            print(f"  [{i:2d}/{len(ban_ghi)}] {r['id']:32s} "
                  f"{kq.thoi_gian_ms:6.0f}ms  {trang_thai}")
    return ra


def do(ten_model: str = "tesseract", lap: int = 1, nguong_hitl: float | None = None,
       in_tien_do: bool = True) -> dict:
    """Chạy đủ một lượt đo. Trả về dict có: diem, meta, gop, canary_ok, tho."""
    cau_hinh = doc_cau_hinh()
    nguong = cau_hinh["nguong_hitl"] if nguong_hitl is None else nguong_hitl
    ban_ghi = doc_nhan()
    mo_hinh = tao_mo_hinh(ten_model)

    canary_ok, canary_ghi_chu = mo_hinh.tu_kiem_tra()

    cac_lan, tho = [], None
    if canary_ok:
        for lan in range(max(1, lap)):
            if lap > 1 and in_tien_do:
                print(f"--- lần {lan + 1}/{lap} ---")
            kq_tho = chay_mot_lan(mo_hinh, ban_ghi, in_tien_do and lan == 0)
            cac_lan.append(cham(ban_ghi, kq_tho, nguong_hitl=nguong))
            if lan == 0:
                tho = kq_tho

    return {
        "canary_ok": canary_ok,
        "canary": canary_ghi_chu,
        "diem": cac_lan[0] if cac_lan else None,
        "gop": gop_nhieu_lan(cac_lan) if len(cac_lan) > 1 else None,
        "tho": tho,
        "cau_hinh": cau_hinh,
        "meta": {"model": mo_hinh.ten, "phien_ban": mo_hinh.phien_ban,
                 "thoi_diem": datetime.now().isoformat(timespec="seconds"),
                 "canary": canary_ghi_chu, "nguong_hitl": nguong, "so_lan_lap": lap},
    }
