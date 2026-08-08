"""Chốt baseline cho test hồi quy (Bước 5).

    python scripts/chot_baseline.py --lap 3

`--lap` càng lớn thì sigma đo càng đáng tin, và sigma là thứ quyết định biên độ
tha thứ của test. Với model tất định (Tesseract) sigma = 0 và cổng thành so khớp
chính xác. Với model có nhiệt độ, chạy ít nhất 5 lần trước khi chốt.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]

from bo_do.chay import do  # noqa: E402
from bo_do.hoi_quy import TEP_BASELINE, chot_baseline  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--model", default="tesseract")
ap.add_argument("--lap", type=int, default=3)
a = ap.parse_args()

kq = do(a.model, lap=a.lap)
if not kq["canary_ok"]:
    raise SystemExit(f"Canary vỡ ({kq['canary']}). Không chốt baseline trên hạ tầng lỗi.")

bl = chot_baseline(kq["diem"], kq["meta"], kq["gop"])
print(f"\nĐã chốt baseline: {TEP_BASELINE}")
print(f"  model            : {bl['meta']['model']} ({bl['meta']['phien_ban']})")
print(f"  dấu vân tay data : {bl['dau_van_tay_du_lieu']}")
print(f"  số lần đo sigma  : {bl['so_lan_do_sigma']}")
for k, v in bl["chi_so"].items():
    print(f"  {k:34s} = {v}   (sigma {bl['sigma'][k]})")
print(f"  rò rỉ nghiêm trọng = {bl['so_ro_ri_nghiem_trong']}")
