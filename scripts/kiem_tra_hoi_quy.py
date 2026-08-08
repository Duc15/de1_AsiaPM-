"""Cổng chất lượng cho CI (Bước 5). Một lệnh, một mã thoát, một câu kết luận.

    python scripts/kiem_tra_hoi_quy.py          # exit 0 = đạt, 1 = không đạt

Dùng khi không muốn cài pytest. Cùng logic với tests/test_hoi_quy.py vì cả hai
gọi bo_do/hoi_quy.py.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]

from bo_do.chay import do, doc_cau_hinh  # noqa: E402
from bo_do.hoi_quy import danh_gia, doc_baseline  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--model", default="tesseract")
ap.add_argument("--lap", type=int, default=1)
ap.add_argument("--im-lang", action="store_true")
ap.add_argument("--chi-hoi-quy", action="store_true",
                help="chỉ canh tụt so với baseline, bỏ qua cổng nghiệp vụ tuyệt đối "
                     "(dùng khi model đã biết là chưa đạt nhưng vẫn cần biết có tụt thêm)")
a = ap.parse_args()

kq = do(a.model, lap=a.lap, in_tien_do=not a.im_lang)
cong = doc_cau_hinh()["cong_chat_luong"]
bl = doc_baseline()
pq = danh_gia(kq["diem"], kq["canary_ok"], cong, bl)

loi_tinh_diem = ([l for l in pq["loi"] if not l.startswith("CỔNG")]
                 if a.chi_hoi_quy else pq["loi"])
dat = not loi_tinh_diem

print(f"\n{'=' * 66}")
print(f"KẾT LUẬN: {'ĐẠT' if dat else 'KHÔNG ĐẠT'}"
      f"{' (chỉ canh hồi quy)' if a.chi_hoi_quy else ''}   |   "
      f"So với baseline: {pq['xu_huong']}")
print(f"{'=' * 66}")

if bl is None:
    print("Chưa có baseline. Chạy: python scripts/chot_baseline.py --lap 3")
else:
    print(f"Baseline: {bl['meta']['model']} @ {bl['meta']['thoi_diem']} "
          f"| data {bl['dau_van_tay_du_lieu']} | sigma đo qua {bl['so_lan_do_sigma']} lần")
    for k, v in pq["so_sanh_baseline"].items():
        dau = "TỤT QUÁ BIÊN" if v["tut_qua_bien"] else "trong biên"
        print(f"  {k:34s} {v['baseline']:.4f} → {v['lan_nay']:.4f} "
              f"(lệch {v['lech']:+.4f}, biên ±{v['bien_cho_phep']:.4f}) {dau}")

for c in pq["ca_tot_len"]:
    print(f"  + tốt lên: {c}")
for c in pq["ca_xau_di"]:
    print(f"  - xấu đi : {c}")
for c in pq["canh_bao"]:
    print(f"  CẢNH BÁO: {c}")
for l in pq["loi"]:
    bo_qua = a.chi_hoi_quy and l.startswith("CỔNG")
    print(f"  {'(bỏ qua)' if bo_qua else 'FAIL:'} {l}")

raise SystemExit(0 if dat else 1)
