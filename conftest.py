"""Bootstrap cho bộ test — bảo đảm `pytest` chạy được ngay sau khi clone.

VÌ SAO CẦN:
    `ket_qua/` bị gitignore (nó là sản phẩm sinh ra, không phải mã nguồn), nhưng
    các kịch bản BDD ở `features/02` và `features/03` lại ĐỌC kết quả đo. Hệ quả
    trên bản clone sạch: 29 ca đỏ với `FileNotFoundError`, trong khi không có gì
    hỏng cả — chỉ là thiếu bước dựng.

    Lỗi này chỉ lộ ra khi làm đúng thứ người chấm sẽ làm: clone về rồi chạy
    `pytest`. Chạy trên máy đã làm việc cả buổi thì không bao giờ thấy.

CÁCH XỬ LÝ:
    Fixture `da_co_ket_qua_do` chạy `scripts/do_luong.py` MỘT lần nếu chưa có kết
    quả. Nó KHÔNG autouse — chỉ ca nào thật sự cần mới yêu cầu, nên
    `pytest tests/test_luat_so_khop.py` vẫn xong trong 0,1 giây.

    Phép đo tất định (sigma = 0,0000 qua 3 lần chạy), nên tự chạy lại không làm
    kết quả dao động.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parent
MODEL_MAC_DINH = "tesseract"


def _tep_ket_qua(ten_model: str) -> Path:
    return GOC / "ket_qua" / ten_model / "cham_diem.json"


@pytest.fixture(scope="session")
def da_co_ket_qua_do() -> Path:
    """Bảo đảm đã có một lượt đo. Chạy `scripts/do_luong.py` nếu chưa."""
    tep = _tep_ket_qua(MODEL_MAC_DINH)
    if tep.exists():
        return tep

    print(f"\n[bootstrap] chưa có {tep.relative_to(GOC)} — chạy scripts/do_luong.py "
          "một lần (~40 giây, OCR 33 ảnh)...", flush=True)
    r = subprocess.run(
        [sys.executable, "scripts/do_luong.py"], cwd=GOC,
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=dict(os.environ, PYTHONIOENCODING="utf-8"), timeout=600)
    if not tep.exists():
        pytest.fail(
            "không dựng được kết quả đo. Thường là do thiếu Tesseract hoặc thiếu gói "
            f"ngôn ngữ `vie` — xem README, mục Cài.\n"
            f"--- stdout ---\n{r.stdout[-1500:]}\n--- stderr ---\n{r.stderr[-1500:]}")
    print(f"[bootstrap] xong, mã thoát {r.returncode}", flush=True)
    return tep


@pytest.fixture(scope="session")
def da_co_ket_qua_doi_chung() -> Path | None:
    """Kết quả của model đối chứng — có thì dùng, không thì để ca tự bỏ qua."""
    tep = _tep_ket_qua("luon_tu_choi")
    if tep.exists():
        return tep
    subprocess.run(
        [sys.executable, "scripts/do_luong.py", "--model", "luon_tu_choi"], cwd=GOC,
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=dict(os.environ, PYTHONIOENCODING="utf-8"), timeout=300)
    return tep if tep.exists() else None
