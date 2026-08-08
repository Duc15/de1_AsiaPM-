"""Kiểm thử chính BỘ KIỂM THỬ — gài lỗi có chủ ý rồi xem test có bắt được không.

Vì sao cần: một bộ test toàn màu xanh không chứng minh được gì. Nó xanh vì phần
mềm đúng, hay xanh vì nó không kiểm gì cả? Cách duy nhất phân biệt là **cố tình
làm hỏng** rồi xem test có đỏ đúng chỗ không. Mutation nào "sống sót" (gài lỗi mà
test vẫn xanh) là một lỗ hổng trong bộ kiểm thử, không phải tin vui.

Chạy:  python scripts/kiem_tra_bo_test.py
       python scripts/kiem_tra_bo_test.py --chi 5     # chạy riêng một mutation

Mỗi mutation được áp lên một BẢN SAO của repo trong thư mục tạm; mã nguồn thật
không bao giờ bị sửa.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]

GOC = Path(__file__).resolve().parents[1]

_TAT_CHINH_SACH_TU_CHOI = ("bo_do/mo_hinh/tesseract.py",
                           "TOI_THIEU_SO_TU = 8\nTOI_THIEU_CONF_ANH = 30.0",
                           "TOI_THIEU_SO_TU = 0\nTOI_THIEU_CONF_ANH = -1.0")

# (mã, mô tả bằng lời nghiệp vụ, [(tệp, chuỗi tìm, chuỗi thay), ...],
#  ca kiểm thử phải đỏ, lý do chấp nhận nếu sống sót)
MUTATION = [
    ("M1", "Cổng HITL so sánh sai ranh giới: dùng <= thay vì < (AC2)",
     [("bo_do/so_bang_chung.py",
       "can_xac_nhan = conf is None or conf < nguong_hitl",
       "can_xac_nhan = conf is None or conf <= nguong_hitl")],
     "TC_AC2_03", None),

    ("M2", "Cổng HITL ngừng gắn cờ: mọi trường đều coi như đủ tin cậy (AC2)",
     [("bo_do/so_bang_chung.py",
       "can_xac_nhan = conf is None or conf < nguong_hitl",
       "can_xac_nhan = False")],
     "TC_AC2_01", None),

    ("M3", "Sổ bằng chứng ghi sai băm ảnh gốc — liên kết hồ sơ↔ảnh nói dối (AC1)",
     [("bo_do/so_bang_chung.py",
       '"anh_goc": {"duong_dan": r["tep"], "sha256": sha,',
       '"anh_goc": {"duong_dan": r["tep"], "sha256": "0" * 64,')],
     "TC_AC1_04", None),

    ("M4", "Ảnh không đọc được vẫn bị đánh dấu đủ điều kiện xử lý (AC3)",
     [("bo_do/so_bang_chung.py",
       "    if kq.ly_do_tu_choi:\n        return CAN_BO_SUNG, kq.ly_do_tu_choi",
       "    if kq.ly_do_tu_choi:\n        return DU_DIEU_KIEN, None")],
     "TC_AC3_02", None),

    ("M5", "Hồ sơ cần bổ sung nhưng không kèm lý do (AC3)",
     [("bo_do/so_bang_chung.py", '"ly_do": ly_do,', '"ly_do": None,')],
     "TC_AC3_03", None),

    ("M6", "Bỏ chính sách từ chối: ép model đoán bừa trên ảnh không đọc được (AC3)",
     [_TAT_CHINH_SACH_TU_CHOI],
     "TC_AC3_01",
     "Đã truy nguyên: bỏ chính sách từ chối KHÔNG sinh ra hành vi bịa, vì bộ tách "
     "còn một lớp phòng vệ thứ hai — nó chỉ trả giá trị khi khớp được mốc neo, và "
     "trên 6 ảnh không đọc được thì OCR ra toàn rác nên không mốc neo nào khớp. "
     "Mutation này không tạo được lỗi cần bắt, nên nó không chứng minh gì về "
     "TC_AC3_01. Ca đó được chứng minh bằng M8 thay thế."),

    ("M7", "Trường mất điểm tin cậy — cổng HITL không phân loại được nó (AC1)",
     [("bo_do/mo_hinh/tesseract.py",
       'return TruongTraVe(truong.ten, gia_tri, round(conf, 4), "ocr")',
       'return TruongTraVe(truong.ten, gia_tri, None, "ocr")')],
     "TC_AC1_02", None),

    # M8 là mutation quan trọng nhất trong danh sách: nó gài đúng cái lỗi mà AC3
    # cấm. Bộ tách được thêm một nhánh "cố gắng hết sức" — khi không khớp mốc neo
    # nào thì lấy luôn dòng OCR đầu tiên làm giá trị. Đây là kiểu bug rất thật:
    # một lập trình viên thêm fallback cho "đỡ trả về rỗng". Kèm theo phải tắt
    # chính sách từ chối, nếu không pipeline chặn trước khi tới bộ tách.
    ("M8", "Bộ tách bịa: không khớp mốc neo thì lấy dòng OCR đầu tiên làm giá trị (AC3)",
     [_TAT_CHINH_SACH_TU_CHOI,
      ("bo_do/mo_hinh/tesseract.py",
       '            conf = float(np.mean([t["conf"] for t in tu])) / 100.0\n'
       '            return TruongTraVe(truong.ten, gia_tri, round(conf, 4), "ocr")\n'
       '        return None',
       '            conf = float(np.mean([t["conf"] for t in tu])) / 100.0\n'
       '            return TruongTraVe(truong.ten, gia_tri, round(conf, 4), "ocr")\n'
       '        if dong:\n'
       '            return TruongTraVe(truong.ten, dong[0].text, 0.5, "ocr")\n'
       '        return None')],
     "TC_AC3_01", None),
]


def _ban_sao(dich: Path) -> None:
    for ten in ("bo_do", "scripts", "tests", "data", "cau_hinh.json", "pytest.ini"):
        nguon = GOC / ten
        if nguon.is_dir():
            shutil.copytree(nguon, dich / ten,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        else:
            shutil.copy2(nguon, dich / ten)


def chay_mot(m, thu_muc_tam: Path) -> dict:
    ma, mo_ta, sua, ca, ly_do_chap_nhan = m
    lam_viec = thu_muc_tam / ma
    lam_viec.mkdir(parents=True, exist_ok=True)
    _ban_sao(lam_viec)

    for tep, tim, thay in sua:
        p = lam_viec / tep
        s = p.read_text(encoding="utf-8")
        if tim not in s:
            return {"ma": ma, "mo_ta": mo_ta, "ca": ca,
                    "trang_thai": "KHONG_AP_DUOC",
                    "ghi_chu": f"không tìm thấy đoạn cần thay trong {tep} — "
                               "mã nguồn đã đổi, cập nhật lại mutation này"}
        p.write_text(s.replace(tim, thay, 1), encoding="utf-8")

    moi_truong = dict(os.environ, PYTHONIOENCODING="utf-8")
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_dac_ta_ac.py",
         "-k", ca, "-q", "-p", "no:cacheprovider"],
        cwd=lam_viec, capture_output=True, text=True, encoding="utf-8",
        errors="replace", env=moi_truong)
    ra = (r.stdout or "") + (r.stderr or "")
    bi_bat = r.returncode != 0
    khong_chay = "no tests ran" in ra or "collected 0 items" in ra
    trang_thai = ("KHONG_CHAY_DUOC_CA" if khong_chay
                  else "BI_BAT" if bi_bat else "SONG_SOT")
    return {
        "ma": ma, "mo_ta": mo_ta, "ca": ca, "trang_thai": trang_thai,
        "song_sot_da_truy_nguyen": bool(ly_do_chap_nhan) and trang_thai == "SONG_SOT",
        "ly_do_chap_nhan": ly_do_chap_nhan,
        "duoi_log": ra.strip().splitlines()[-1] if ra.strip() else "",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--chi", help="chỉ chạy mutation có mã này, ví dụ M5")
    a = ap.parse_args()
    ds = [m for m in MUTATION if not a.chi or m[0] == a.chi.upper()]

    print(f"Gài {len(ds)} lỗi có chủ ý, mỗi lỗi chạy lại ca kiểm thử tương ứng.\n"
          f"Mã nguồn thật không bị sửa — mọi thứ diễn ra trên bản sao trong thư mục tạm.\n")
    ket_qua = []
    with tempfile.TemporaryDirectory(prefix="dot_bien_") as tam:
        for m in ds:
            print(f"  {m[0]} … ", end="", flush=True)
            kq = chay_mot(m, Path(tam))
            ket_qua.append(kq)
            print(f"{kq['trang_thai']}  ({m[1]})")

    bi_bat = [k for k in ket_qua if k["trang_thai"] == "BI_BAT"]
    da_truy = [k for k in ket_qua if k.get("song_sot_da_truy_nguyen")]
    lo_hong = [k for k in ket_qua
               if k["trang_thai"] != "BI_BAT" and not k.get("song_sot_da_truy_nguyen")]

    print(f"\n{'=' * 70}")
    print(f"Bị bắt: {len(bi_bat)}/{len(ket_qua)}  |  "
          f"sống sót đã truy nguyên: {len(da_truy)}  |  "
          f"lỗ hổng chưa giải thích: {len(lo_hong)}")
    for k in da_truy:
        print(f"\n  SỐNG SÓT (đã truy nguyên) {k['ma']} — {k['mo_ta']}")
        print(f"    {k['ly_do_chap_nhan']}")
    for k in lo_hong:
        print(f"\n  LỖ HỔNG {k['ma']} — {k['mo_ta']}")
        print(f"    ca {k['ca']} vẫn xanh khi đã gài lỗi ({k['trang_thai']}) — "
              "phải truy nguyên hoặc bổ sung ca kiểm thử")
    print(f"{'=' * 70}")

    ra = GOC / "ket_qua" / "kiem_tra_bo_test.json"
    ra.parent.mkdir(parents=True, exist_ok=True)
    ra.write_text(json.dumps({"so_mutation": len(ket_qua),
                              "so_bi_bat": len(bi_bat),
                              "so_song_sot_da_truy_nguyen": len(da_truy),
                              "so_lo_hong": len(lo_hong),
                              "chi_tiet": ket_qua}, ensure_ascii=False, indent=2),
                  encoding="utf-8")
    print(f"Chi tiết: {ra}")
    return 0 if not lo_hong else 1


if __name__ == "__main__":
    raise SystemExit(main())
