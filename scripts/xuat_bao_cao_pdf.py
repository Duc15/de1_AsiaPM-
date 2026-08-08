"""Render báo cáo ra PDF A4 và báo số trang thật.

    python scripts/xuat_bao_cao_pdf.py            # BAO-CAO.md -> BAO-CAO.pdf
    python scripts/xuat_bao_cao_pdf.py --do-thu   # dò cỡ chữ lớn nhất mà vẫn ≤ 2 trang

Đề giới hạn báo cáo ở 2 trang. Đó là một tiêu chí nghiệm thu, nên nó được ĐO chứ
không ước lượng, và `tests/test_nop_bai.py::TC-NOP-01` canh nó ở mỗi lần chạy.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]

from bo_do.xuat_pdf import (CO_CHU_NOP, LE_MM_NOP, NGAT_TRANG_NOP,  # noqa: E402
                            dem_trang, xuat_pdf)

GOC = Path(__file__).resolve().parents[1]
NGAT_TRANG = "# Trả lời câu hỏi cuối"

ap = argparse.ArgumentParser()
ap.add_argument("--md", default="BAO-CAO.md")
ap.add_argument("--pdf", default=None)
ap.add_argument("--co-chu", type=float, default=CO_CHU_NOP)
ap.add_argument("--le-mm", type=float, default=LE_MM_NOP)
ap.add_argument("--toi-da", type=int, default=2, help="số trang tối đa cho phép")
ap.add_argument("--do-thu", action="store_true",
                help="dò cỡ chữ lớn nhất mà vẫn nằm trong giới hạn trang")
ap.add_argument("--ngat-trang", action="store_true",
                help="ép câu hỏi cuối sang trang mới (KHÔNG phải mặc định: nó tốn "
                     "nguyên một trang và làm bản nộp lệch khỏi cổng nghiệm thu)")
a = ap.parse_args()

md = GOC / a.md
pdf = Path(a.pdf) if a.pdf else md.with_suffix(".pdf")
ngat = NGAT_TRANG if a.ngat_trang else NGAT_TRANG_NOP

if a.do_thu:
    print(f"Dò cỡ chữ cho {md.name} (giới hạn {a.toi_da} trang, lề {a.le_mm} mm):\n")
    tot_nhat = None
    for co in [round(x * 0.25, 2) for x in range(40, 20, -1)]:   # 10,0 -> 5,25
        n = dem_trang(md, co_chu=co, le_mm=a.le_mm, ngat_trang_truoc=ngat)
        dat = n <= a.toi_da
        print(f"  cỡ chữ {co:5.2f} pt -> {n} trang  {'ĐẠT' if dat else ''}")
        if dat and tot_nhat is None:
            tot_nhat = co
    if tot_nhat is None:
        print("\nKhông cỡ chữ nào trong dải thử đạt giới hạn — phải rút gọn nội dung.")
        raise SystemExit(1)
    print(f"\nCỡ chữ lớn nhất còn ĐẠT: {tot_nhat} pt")
    raise SystemExit(0)

so_trang = xuat_pdf(md, pdf, co_chu=a.co_chu, le_mm=a.le_mm, ngat_trang_truoc=ngat)
print(f"{pdf}  —  {so_trang} trang A4 "
      f"(cỡ chữ {a.co_chu} pt, lề {a.le_mm} mm)")
if so_trang > a.toi_da:
    print(f"KHÔNG ĐẠT: vượt giới hạn {a.toi_da} trang.")
    raise SystemExit(1)
print(f"ĐẠT: trong giới hạn {a.toi_da} trang.")
