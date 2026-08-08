"""Bước 3 — gộp hai lượt gán nhãn thành bộ nhãn dùng để đo, và đo luôn độ đồng thuận.

Bộ nhãn có hai lớp, cố ý tách rời:

  1. GIÁ TRỊ  — lấy từ bản kê sinh ảnh. Đúng theo cấu tạo: script biết nó đã vẽ
     chữ gì vì chính nó vẽ. Không có phiên âm tay nên không có lỗi phiên âm.

  2. KỲ VỌNG HÀNH VI — lấy từ lượt đọc lại của người (doc_lai_doc_lap.csv):
       phai_trich_dung  người đọc được -> đòi model trả đúng
       phai_tu_choi     cả ảnh không ai đọc được -> AC3 đòi model KHÔNG trả gì
       vung_xam         người không đọc được trường này nhưng ảnh vẫn đọc được
                        -> KHÔNG tính vào accuracy chính

Vì sao phải có vùng xám: trên ảnh bậc "nang", dấu giáp lai đè kín ô ngày sinh.
Người duyệt cũng không đọc nổi. Đòi model trả đúng ở đó là đòi nó bịa; đòi nó im
lặng ở đó lại thưởng cho việc im lặng. Cả hai đều bóp méo con số. Nên chỗ đó bị
loại khỏi accuracy và được báo riêng — đó là số ảnh mà phép đo này không kết
luận được gì.

Chạy:  python scripts/gan_nhan.py
"""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]

from bo_do.schema import LOAI_GIAY_TO  # noqa: E402

GOC = Path(__file__).resolve().parents[1]
THU_MUC_NHAN = GOC / "data" / "nhan"

PHAI_TRICH_DUNG = "phai_trich_dung"
PHAI_TU_CHOI = "phai_tu_choi"
VUNG_XAM = "vung_xam"


def doc_luot_hai() -> dict[tuple[str, str], dict]:
    """Đọc sổ gán nhãn của người. Khoá trùng là LỖI, không phải "dòng cuối thắng".

    Bản đầu của hàm này ghi đè im lặng khi gặp khoá trùng. Hậu quả có thật: sổ bị
    thêm một khối 72 dòng cho cùng 18 ảnh, hai khối mâu thuẫn nhau ở phần ghi chú
    (một bên ghi "không nhìn rõ dấu ngã", bên kia ghi "vẫn đọc rõ"), và bộ đo vẫn
    chạy êm ru — chỉ lấy khối cuối. Nhãn là thước đo duy nhất của cả bài, nên nó
    phải nổ chứ không được tự chọn hộ.
    """
    ra: dict[tuple[str, str], dict] = {}
    trung: list[str] = []
    tep = THU_MUC_NHAN / "doc_lai_doc_lap.csv"
    dong_sach = [d for d in tep.read_text(encoding="utf-8").splitlines()
                 if not d.startswith("#")]
    for r in csv.DictReader(dong_sach):
        if not (r.get("id") or "").strip():
            continue
        khoa = (r["id"], r["ten_truong"])
        if khoa in ra:
            trung.append(f"{khoa[0]}.{khoa[1]}")
            continue
        ra[khoa] = {
            "doc_duoc": r["doc_duoc"].strip() == "1",
            "gia_tri": (r.get("gia_tri_doc_lai") or "").strip(),
            "ghi_chu": (r.get("ghi_chu") or "").strip(),
        }
    if trung:
        raise SystemExit(
            f"{tep.name} có {len(trung)} khoá (ảnh, trường) bị ghi hai lần — "
            "không thể biết lượt đọc nào là thật.\n  "
            + "\n  ".join(trung[:10])
            + ("\n  ..." if len(trung) > 10 else "")
            + "\nXoá dòng thừa rồi chạy lại. Bộ đo KHÔNG tự chọn hộ.")
    return ra


def gan_nhan() -> dict:
    ban_ke = json.loads((THU_MUC_NHAN / "ban_ke_sinh.json").read_text(encoding="utf-8"))
    luot2 = doc_luot_hai()

    ban_ghi: list[dict] = []
    dem_ky_vong: Counter[str] = Counter()
    khop, lech, so_sanh_duoc = 0, [], 0
    anh_lay_mau = set()

    for anh in ban_ke["anh"]:
        ma_id = anh["id"]
        loai = LOAI_GIAY_TO[anh["doc_type"]]
        ten_truong = [t.ten for t in loai.truong]

        co_luot2 = any((ma_id, tt) in luot2 for tt in ten_truong)
        if co_luot2:
            anh_lay_mau.add(ma_id)
        # Ảnh bị phán "không đọc được" khi lượt 2 không đọc được BẤT KỲ trường nào.
        anh_khong_doc_duoc = co_luot2 and not any(
            luot2.get((ma_id, tt), {}).get("doc_duoc") for tt in ten_truong)

        truong_ra = []
        for tt in ten_truong:
            su_that = anh["noi_dung_da_ve"][tt]
            q = luot2.get((ma_id, tt))

            if anh_khong_doc_duoc:
                ky_vong, gia_tri = PHAI_TU_CHOI, None
            elif q is None:
                ky_vong, gia_tri = PHAI_TRICH_DUNG, su_that       # chưa lấy mẫu lượt 2
            elif q["doc_duoc"]:
                ky_vong, gia_tri = PHAI_TRICH_DUNG, su_that
            else:
                ky_vong, gia_tri = VUNG_XAM, su_that

            dem_ky_vong[ky_vong] += 1
            truong_ra.append({
                "ten_truong": tt,
                "gia_tri": gia_tri,
                "ky_vong": ky_vong,
                "nguon_nhan": "cau_tao" if gia_tri is not None else "hai_luot_deu_khong_doc_duoc",
                "gia_tri_luot2": (q or {}).get("gia_tri") or None,
                "ghi_chu_luot2": (q or {}).get("ghi_chu") or "",
            })

            # Độ đồng thuận: chỉ so ở những trường lượt 2 đọc được VÀ có ghi giá trị.
            if q and q["doc_duoc"] and q["gia_tri"]:
                so_sanh_duoc += 1
                if _bang_nhau(loai.ma, tt, su_that, q["gia_tri"]):
                    khop += 1
                else:
                    lech.append({"id": ma_id, "ten_truong": tt,
                                 "cau_tao": su_that, "doc_lai": q["gia_tri"]})

        ban_ghi.append({
            "id": ma_id,
            "tep": anh["tep"],
            "doc_type": anh["doc_type"],
            "muc_chat_luong": anh["muc_chat_luong"],
            "anh_doc_duoc": not anh_khong_doc_duoc,
            "lay_mau_luot2": co_luot2,
            "fields": truong_ra,
        })

    tep_nhan = THU_MUC_NHAN / "nhan.jsonl"
    with tep_nhan.open("w", encoding="utf-8", newline="\n") as f:
        for r in ban_ghi:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    dong_thuan = {
        "so_anh": len(ban_ghi),
        "so_anh_lay_mau_luot2": len(anh_lay_mau),
        "so_truong_so_sanh_duoc": so_sanh_duoc,
        "so_truong_khop": khop,
        "ty_le_khop": round(khop / so_sanh_duoc, 4) if so_sanh_duoc else None,
        "cac_cho_lech": lech,
        "phan_bo_ky_vong": dict(dem_ky_vong),
        "gioi_han": [
            "Lượt đọc lại do một mô hình ngôn ngữ đọc ảnh trong cùng phiên đã sinh ảnh; "
            "phần phiên âm giá trị KHÔNG độc lập hoàn toàn, nên ty_le_khop là chặn "
            "trên chứ không phải số đo sạch. Muốn có số sạch cần hai người thật gán nhãn "
            "mù rồi tính Cohen's kappa.",
            "Sản phẩm đáng tin của lượt đọc lại là phán quyết đọc được / không đọc được, "
            "vì phán quyết đó không thể suy ra từ bản kê.",
            "Lượt 3 đã bổ sung nốt 18 ảnh bậc sach/nhe/trung_binh, nên nay 33/33 ảnh đều "
            "có người đọc lại — không còn ảnh nào mang kỳ vọng hành vi do script gán mặc "
            "định. Giả định GĐ-3 đã được gỡ: 18/18 ảnh đọc được rõ, con số không đổi.",
            "Phát hiện của lượt 3, phải ghi lại vì nó làm nhẹ bớt lỗi LOI-01: trên 3 ảnh "
            "CCCD bậc trung_binh, người đọc lại đọc được CHỮ nhưng KHÔNG nhìn rõ DẤU THANH "
            "(dấu ngã trên NGUYỄN, dấu huyền trên HUYỀN) và phải suy từ ngữ cảnh tên phổ "
            "biến. Nghĩa là ở bậc đó thông tin dấu có thể đã bị phá huỷ trong ảnh — quy "
            "toàn bộ lỗi dấu cho model là chưa hoàn toàn công bằng. Xem cột ghi_chu_luot2.",
        ],
    }
    (THU_MUC_NHAN / "do_dong_thuan.json").write_text(
        json.dumps(dong_thuan, ensure_ascii=False, indent=2), encoding="utf-8")
    return dong_thuan


def _bang_nhau(ma_loai: str, ten_truong: str, a: str, b: str) -> bool:
    """Dùng đúng luật so khớp của Bước 1 để đo đồng thuận giữa hai người gán nhãn.

    Nếu đo đồng thuận bằng một luật khác với luật đo model thì con số đồng thuận
    không nói được gì về chất lượng của thước đo.
    """
    from bo_do.so_khop import so_khop_truong
    return so_khop_truong(ma_loai, ten_truong, a, b).la_dung


if __name__ == "__main__":
    kq = gan_nhan()
    print(f"Nhãn: {THU_MUC_NHAN / 'nhan.jsonl'}  ({kq['so_anh']} ảnh)")
    print(f"Kỳ vọng hành vi: {kq['phan_bo_ky_vong']}")
    print(f"Đồng thuận hai lượt: {kq['so_truong_khop']}/{kq['so_truong_so_sanh_duoc']} "
          f"= {kq['ty_le_khop']}  (lấy mẫu {kq['so_anh_lay_mau_luot2']}/{kq['so_anh']} ảnh)")
    for l in kq["cac_cho_lech"]:
        print(f"  LỆCH  {l['id']}.{l['ten_truong']}: cấu tạo={l['cau_tao']!r} "
              f"đọc lại={l['doc_lai']!r}")
