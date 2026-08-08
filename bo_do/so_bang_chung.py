"""Sổ bằng chứng + cổng HITL + nhật ký worker — hiện thực hợp đồng đầu ra của AC1/AC2/AC3.

Vì sao file này tồn tại: đề cho đặc tả AC1–AC3 nhưng KHÔNG cho quyền truy cập hệ
thống. Nếu chỉ đo accuracy thì AC1 và AC2 không hề bị kiểm thử — mà hai AC đó
mới là chỗ quy định hình dạng đầu ra mà hệ thống thật sẽ tiêu thụ.

Nên ở đây dựng một **bản hiện thực tham chiếu của hợp đồng đầu ra**: nhận kết quả
model, sinh ra đúng ba thứ AC1–AC3 đòi, rồi bộ test kiểm ba thứ đó. Nó không phải
hệ thống của AsiaPM và không giả vờ là. Nó là cái khuôn để kiểm xem model có sản
xuất đủ dữ liệu cho hệ thống đó hay không — thiếu confidence, thiếu liên kết ảnh
gốc, hay thiếu lý do từ chối thì hỏng ngay ở đây, chứ không đợi tích hợp.

Ba thứ được sinh ra:

  so_bang_chung.json   AC1: mỗi hồ sơ ↔ ảnh gốc (đường dẫn + sha256), từng trường
                       kèm confidence và nguồn
                       AC2: từng trường có cờ `can_nguoi_xac_nhan` theo ngưỡng cấu hình
                       AC3: hồ sơ không đọc được mang trạng thái `can_bo_sung` + lý do
  nhat_ky_worker.log   AC1: nhật ký worker, một dòng một ảnh
  (giá trị trả về)     bản tóm tắt để bộ test khỏi phải đọc lại file
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .mo_hinh.co_so import KetQuaTrichXuat
from .schema import LOAI_GIAY_TO

GOC = Path(__file__).resolve().parents[1]

DU_DIEU_KIEN = "du_dieu_kien_xu_ly"
CAN_BO_SUNG = "can_bo_sung"


def _bam_tep(duong_dan: Path) -> tuple[str, int]:
    b = duong_dan.read_bytes()
    return hashlib.sha256(b).hexdigest(), len(b)


def _trang_thai_ho_so(kq: KetQuaTrichXuat, ma_loai: str) -> tuple[str, str | None]:
    """AC3: khi nào hồ sơ bị đặt trạng thái "cần bổ sung", và lý do là gì.

    Giả định GĐ-7 (đề không nói): hồ sơ cần bổ sung khi model từ chối, khi không
    trích được trường nào, hoặc khi thiếu bất kỳ trường NGHIÊM TRỌNG nào. Thiếu
    một trường trung bình thì hồ sơ vẫn đi tiếp, trường đó được gắn cờ cho người
    duyệt điền tay.
    """
    if kq.loi_he_thong:
        return CAN_BO_SUNG, f"không xử lý được ảnh: {kq.loi_he_thong}"
    if kq.ly_do_tu_choi:
        return CAN_BO_SUNG, kq.ly_do_tu_choi
    if not kq.fields:
        return CAN_BO_SUNG, ("đọc được chữ nhưng không xác định được trường nào "
                             "trên giấy tờ")
    thieu = [t.ten for t in LOAI_GIAY_TO[ma_loai].truong
             if t.muc_do == "nghiem_trong" and not kq.gia_tri(t.ten)]
    if thieu:
        return CAN_BO_SUNG, f"thiếu trường bắt buộc: {', '.join(thieu)}"
    return DU_DIEU_KIEN, None


def lap_so_bang_chung(ban_ghi_nhan: list[dict],
                      ket_qua: dict[str, KetQuaTrichXuat],
                      meta: dict,
                      nguong_hitl: float) -> dict:
    """Sinh sổ bằng chứng. KHÔNG dùng nhãn — chỉ dùng đầu ra của model.

    Cố ý không nhận nhãn vào: sổ bằng chứng là thứ hệ thống thật sinh ra khi chạy
    trên hồ sơ của dân, lúc đó không có nhãn nào cả. Nếu hàm này nhìn thấy nhãn
    thì bộ test AC1/AC2 sẽ kiểm một thứ không tồn tại ngoài đời.
    """
    ho_so = []
    for r in ban_ghi_nhan:
        kq = ket_qua.get(r["id"])
        duong_dan = GOC / r["tep"]
        sha, kich_thuoc = _bam_tep(duong_dan)

        truong = []
        for f in (kq.fields if kq else []):
            conf = f.confidence
            # AC2: "dưới ngưỡng cấu hình" -> so sánh NGẶT. Trường có conf đúng
            # bằng ngưỡng KHÔNG bị gắn cờ. Đây là ranh giới, và nó được kiểm
            # riêng bằng một ca biên trong tests/test_dac_ta_ac.py.
            can_xac_nhan = conf is None or conf < nguong_hitl
            truong.append({
                "ten_truong": f.ten_truong,
                "gia_tri": f.gia_tri,
                "confidence": conf,
                "nguon": f.nguon,
                "can_nguoi_xac_nhan": can_xac_nhan,
            })

        trang_thai, ly_do = (_trang_thai_ho_so(kq, r["doc_type"])
                             if kq else (CAN_BO_SUNG, "không có kết quả cho ảnh này"))

        ho_so.append({
            "id": r["id"],
            "doc_type": r["doc_type"],
            # AC1: ảnh gốc được liên kết trong sổ bằng chứng.
            "anh_goc": {"duong_dan": r["tep"], "sha256": sha,
                        "kich_thuoc_byte": kich_thuoc},
            "trang_thai_ho_so": trang_thai,
            "ly_do": ly_do,
            "fields": truong,
            "so_truong_can_nguoi_xac_nhan": sum(1 for t in truong
                                                if t["can_nguoi_xac_nhan"]),
            "thoi_gian_ms": round(kq.thoi_gian_ms, 1) if kq else None,
            "loi_he_thong": kq.loi_he_thong if kq else "không có kết quả",
        })

    return {
        "meta": meta,
        "nguong_hitl": nguong_hitl,
        "quy_uoc_nguong": "trường bị gắn cờ khi confidence < ngưỡng (so sánh ngặt)",
        "so_ho_so": len(ho_so),
        "so_ho_so_can_bo_sung": sum(1 for h in ho_so
                                    if h["trang_thai_ho_so"] == CAN_BO_SUNG),
        "ho_so": ho_so,
    }


def ghi_nhat_ky_worker(so: dict, duong_dan: Path) -> None:
    """AC1: "nhật ký worker được ghi". Một dòng một ảnh, đọc được bằng mắt."""
    dong = [
        f"# nhật ký worker trích xuất | model={so['meta']['model']} "
        f"({so['meta']['phien_ban']}) | chạy lúc {so['meta']['thoi_diem']} "
        f"| ngưỡng HITL={so['nguong_hitl']}",
        "# thoi_diem_chay | anh | sha256(12) | ms | trang_thai | so_truong | can_xac_nhan | ly_do",
    ]
    for h in so["ho_so"]:
        dong.append(
            f"{so['meta']['thoi_diem']} | {h['id']} | {h['anh_goc']['sha256'][:12]} | "
            f"{h['thoi_gian_ms']} | {h['trang_thai_ho_so']} | {len(h['fields'])} | "
            f"{h['so_truong_can_nguoi_xac_nhan']} | {h['ly_do'] or '-'}")
    duong_dan.write_text("\n".join(dong) + "\n", encoding="utf-8")


def ghi_ra_dia(so: dict, thu_muc: Path) -> None:
    thu_muc.mkdir(parents=True, exist_ok=True)
    (thu_muc / "so_bang_chung.json").write_text(
        json.dumps(so, ensure_ascii=False, indent=2), encoding="utf-8")
    ghi_nhat_ky_worker(so, thu_muc / "nhat_ky_worker.log")
