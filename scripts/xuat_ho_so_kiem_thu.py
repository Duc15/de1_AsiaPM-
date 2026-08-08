"""Xuất sổ ca kiểm thử — sinh tự động từ bộ nhãn + kết quả đo.

    python scripts/xuat_ho_so_kiem_thu.py

Vì sao sinh tự động thay vì viết tay: sổ ca kiểm thử viết tay sẽ lệch khỏi dữ
liệu ngay lần sinh lại đầu tiên, và một sổ ca kiểm thử nói dối còn tệ hơn không
có. File này đọc `data/nhan/nhan.jsonl` + `ket_qua/<model>/cham_diem.json` rồi
xuất `ket_qua/<model>/truong_hop_kiem_thu.md`.

Quy ước mã ca kiểm thử:
    TC-<LOAI>-<BAC>-<NN>       một ảnh = một ca kiểm thử (kiểm thử theo dữ liệu)
    TC-AC<n>-<NN>              ca theo đặc tả, nằm trong tests/test_dac_ta_ac.py
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]

from bo_do.chay import GOC, doc_nhan  # noqa: E402

BAC = {"sach": "SACH", "nhe": "NHE", "trung_binh": "TB", "nang": "NANG",
       "khong_doc_duoc": "KDD"}

KY_VONG = {
    "phai_trich_dung": "trích đúng giá trị",
    "phai_tu_choi": "KHÔNG trả giá trị (AC3)",
    "vung_xam": "không kết luận (vùng xám)",
}

DAT = {"DUNG": "ĐẠT", "TU_CHOI_DUNG": "ĐẠT", "SAI": "KHÔNG ĐẠT",
       "BO_SOT": "KHÔNG ĐẠT", "BIA": "KHÔNG ĐẠT (vi phạm AC3)",
       "LOI_HE_THONG": "KHÔNG CHẠY ĐƯỢC"}


def ma_ca(r: dict, thu_tu: int) -> str:
    return f"TC-{r['doc_type'].upper()}-{BAC[r['muc_chat_luong']]}-{thu_tu:02d}"


def xuat(ten_model: str) -> Path:
    thu_muc = GOC / "ket_qua" / ten_model
    diem = json.loads((thu_muc / "cham_diem.json").read_text(encoding="utf-8"))
    ban_ghi = doc_nhan()
    theo_ca: dict[tuple[str, str], dict] = {
        (c["id"], c["ten_truong"]): c for c in diem["chi_tiet"]}

    dem_theo_bac: dict[str, int] = defaultdict(int)
    b: list[str] = []
    b.append("# Sổ ca kiểm thử\n")
    b.append("*Sinh tự động bởi `scripts/xuat_ho_so_kiem_thu.py` — đừng sửa tay.*\n")
    b.append(f"- Model: `{diem['meta']['model']}` — {diem['meta']['phien_ban']}")
    b.append(f"- Chạy lúc: {diem['meta']['thoi_diem']}")
    b.append(f"- Ngưỡng HITL: {diem['meta']['nguong_hitl']}\n")

    b.append("## Thiết kế ca kiểm thử\n")
    b.append("**Phân hoạch tương đương**: loại giấy tờ × bậc chất lượng ảnh. "
             "Mỗi ô là một phân hoạch, mỗi ảnh trong ô là một ca kiểm thử; "
             "mỗi trường trên ảnh là một điểm kiểm.\n")
    ma_tran: dict[tuple[str, str], int] = Counter()
    for r in ban_ghi:
        ma_tran[(r["doc_type"], r["muc_chat_luong"])] += 1
    bac_ds = list(BAC)
    b.append("| Loại giấy tờ | " + " | ".join(bac_ds) + " | Tổng |")
    b.append("|" + "|".join("---" for _ in range(len(bac_ds) + 2)) + "|")
    for dt in sorted({r["doc_type"] for r in ban_ghi}):
        hang = [str(ma_tran[(dt, x)]) for x in bac_ds]
        b.append(f"| `{dt}` | " + " | ".join(hang) + f" | {sum(int(x) for x in hang)} |")
    b.append("")
    b.append("**Ca theo đặc tả** (AC1/AC2/AC3, gồm ca biên và ca cấu hình được): "
             "`tests/test_dac_ta_ac.py`, ma trận truy vết ở `KE-HOACH-KIEM-THU.md`.\n")

    b.append("## Ca kiểm thử theo dữ liệu\n")
    b.append("| Mã ca | Ảnh | Trường | Kỳ vọng | Nhãn | Model trả | Conf | Kết quả |")
    b.append("|---|---|---|---|---|---|---|---|")

    tong = Counter()
    for r in ban_ghi:
        dem_theo_bac[(r["doc_type"], r["muc_chat_luong"])] += 1
        ma = ma_ca(r, dem_theo_bac[(r["doc_type"], r["muc_chat_luong"])])
        for f in r["fields"]:
            c = theo_ca.get((r["id"], f["ten_truong"]))
            if c is None:
                continue
            kq = DAT.get(c["phan_quyet"], c["phan_quyet"])
            if f["ky_vong"] == "vung_xam":
                kq = "KHÔNG TÍNH"
            tong[kq] += 1
            nhan = "—" if f["gia_tri"] is None else str(f["gia_tri"])
            model = "—" if c["model"] is None else str(c["model"])
            conf = "—" if c["confidence"] is None else f"{c['confidence']:.2f}"
            b.append(f"| {ma} | `{r['id']}` | `{f['ten_truong']}` | "
                     f"{KY_VONG[f['ky_vong']]} | {_cat(nhan)} | {_cat(model)} | "
                     f"{conf} | {kq} |")

    b.append("")
    b.append("## Tổng hợp\n")
    b.append("| Kết quả | Số điểm kiểm |")
    b.append("|---|---|")
    for k, v in sorted(tong.items(), key=lambda x: -x[1]):
        b.append(f"| {k} | {v} |")
    b.append(f"| **Tổng** | **{sum(tong.values())}** |")
    b.append("")
    b.append(f"Tỉ lệ ĐẠT: **{tong['ĐẠT'] / max(1, sum(tong.values()) - tong['KHÔNG TÍNH']):.1%}** "
             f"(không tính {tong['KHÔNG TÍNH']} điểm kiểm thuộc vùng xám).")

    ra = thu_muc / "truong_hop_kiem_thu.md"
    ra.write_text("\n".join(b) + "\n", encoding="utf-8")
    return ra


def _cat(s: str, n: int = 42) -> str:
    s = s.replace("|", "\\|")
    return s if len(s) <= n else s[: n - 1] + "…"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="tesseract")
    a = ap.parse_args()
    p = xuat(a.model)
    print(f"Sổ ca kiểm thử: {p}")
