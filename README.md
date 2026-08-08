# Bài 1 — Kiểm thử độ tin cậy mô hình trích xuất giấy tờ

Bộ đo độ tin cậy cho US-M1-EXTRACT-001 (AsiaPM · NƠXH). Model đang cắm vào:
**Tesseract 5.4 (`lang=vie`)** — nhưng model là biến, không phải hằng: xem
[Cắm model khác](#cắm-model-khác) ở dưới.

**Đọc theo thứ tự này nếu bạn đang chấm bài:**
[`BAO-CAO.md`](BAO-CAO.md) (≤2 trang, có kết luận go/no-go) →
[`LOI-PHAT-HIEN.md`](LOI-PHAT-HIEN.md) (10 lỗi, có mã và mức nghiêm trọng) →
[`KE-HOACH-KIEM-THU.md`](KE-HOACH-KIEM-THU.md) (phạm vi, ma trận truy vết AC, sổ rủi ro).

| Bước của đề | Ở đâu trong repo |
|---|---|
| 1. Chốt "đúng" nghĩa là gì | [`bo_do/so_khop.py`](bo_do/so_khop.py), [`bo_do/schema.py`](bo_do/schema.py), [`bo_do/chuan_hoa.py`](bo_do/chuan_hoa.py) |
| 2. Xây bộ dữ liệu (33 ảnh) | [`scripts/sinh_du_lieu.py`](scripts/sinh_du_lieu.py) → `data/anh/`, `data/nhan/ban_ke_sinh.json` |
| 3. Gán nhãn + chứng minh nhãn đáng tin | [`scripts/gan_nhan.py`](scripts/gan_nhan.py), [`data/nhan/doc_lai_doc_lap.csv`](data/nhan/doc_lai_doc_lap.csv) → `data/nhan/nhan.jsonl`, `do_dong_thuan.json` |
| 4. Script đo tự động | [`scripts/do_luong.py`](scripts/do_luong.py) → `ket_qua/tesseract/bao_cao.md` |
| 5. Chạy, kết luận, test tự động | [`BAO-CAO.md`](BAO-CAO.md), [`tests/test_hoi_quy.py`](tests/test_hoi_quy.py), [`bo_do/hoi_quy.py`](bo_do/hoi_quy.py) |
| Prompt đã dùng với AI | [`PROMPTS.md`](PROMPTS.md) |
| Báo cáo ≤ 2 trang + câu hỏi cuối (mục 05) | [`BAO-CAO.md`](BAO-CAO.md) |
| Phần chi tiết bị cắt khỏi 2 trang | [`PHU-LUC.md`](PHU-LUC.md) |

**Sản phẩm kiểm thử (ngoài 5 bước đề yêu cầu):**

| Sản phẩm | Ở đâu |
|---|---|
| Kế hoạch kiểm thử: phạm vi / ngoài phạm vi, kỹ thuật thiết kế ca, tiêu chí vào-ra, sổ rủi ro | [`KE-HOACH-KIEM-THU.md`](KE-HOACH-KIEM-THU.md) |
| **Ma trận truy vết AC ↔ ca kiểm thử** (14/15 điều khoản kiểm được) | cùng file, mục 6 |
| **Kiểm thử theo đặc tả** — 15 ca truy vết 1:1 tới AC1/AC2/AC3 | [`tests/test_dac_ta_ac.py`](tests/test_dac_ta_ac.py) |
| **Báo cáo lỗi** — 10 lỗi (7 mở, 3 đã sửa), có mã, mức nghiêm trọng, bước tái hiện, bằng chứng | [`LOI-PHAT-HIEN.md`](LOI-PHAT-HIEN.md) |
| **Kiểm thử chính bộ test** (mutation) — gài 8 lỗi, 7 bị bắt, 1 sống sót đã truy nguyên | [`scripts/kiem_tra_bo_test.py`](scripts/kiem_tra_bo_test.py) |
| Sổ ca kiểm thử (sinh tự động, 132 điểm kiểm) | `scripts/xuat_ho_so_kiem_thu.py` → `ket_qua/tesseract/truong_hop_kiem_thu.md` |
| Hợp đồng đầu ra AC1/AC2/AC3: sổ bằng chứng, cờ HITL, nhật ký worker | [`bo_do/so_bang_chung.py`](bo_do/so_bang_chung.py) |

## Cài

```bash
pip install -r requirements.txt
```

Cần Tesseract 5 kèm dữ liệu tiếng Việt (`vie`) trên máy:

- Windows: cài bản của UB Mannheim, tick gói **Vietnamese**. Bộ đo tự tìm ở
  `C:\Program Files\Tesseract-OCR\tesseract.exe`, hoặc đặt biến môi trường
  `TESSERACT_CMD`.
- Linux: `apt install tesseract-ocr tesseract-ocr-vie`
- Kiểm tra: `tesseract --list-langs` phải có `vie`.

## Chạy — đề yêu cầu **một lệnh**, đây là lệnh đó

```bash
python scripts/do_luong.py     # đo + xuất báo cáo, ~40 s (ảnh và nhãn đã có sẵn trong repo)
```

Dựng lại toàn bộ từ đầu thì chạy bảy lệnh sau theo thứ tự:

```bash
python scripts/sinh_du_lieu.py         # 1. sinh 33 ảnh (tất định theo seed)
python scripts/gan_nhan.py             # 2. gộp các lượt nhãn + đo độ đồng thuận
python scripts/do_luong.py             # 3. ĐO + xuất báo cáo   <-- lệnh chính
pytest                                 # 4. 296 ca kiểm thử
python scripts/xuat_ho_so_kiem_thu.py  # 5. xuất sổ ca kiểm thử
python scripts/xuat_bao_cao_pdf.py     # 6. render BAO-CAO.pdf + đếm số trang thật
python scripts/kiem_tra_bo_test.py     # 7. kiểm chính bộ test (mutation, ~7 phút)
```

Ràng buộc "báo cáo ≤ 2 trang" của đề được **đo chứ không ước lượng**: báo cáo được dàn
trang bằng reportlab ra A4 (10 pt, lề 12 mm) → **2 trang**, và `tests/test_nop_bai.py`
canh nó cùng với "không mục nào bị cắt cho vừa trang". Dò cỡ chữ tối đa còn vừa:
`python scripts/xuat_bao_cao_pdf.py --do-thu`.

Ba tham số dàn trang là **hằng số dùng chung** ở `bo_do/xuat_pdf.py`, và `TC-NOP-16` mở
thẳng `BAO-CAO.pdf` trong repo để đếm trang rồi đối chiếu với bản render hiện tại. Trước
đó script và bộ test mỗi bên tự khai một bộ tham số, nên cổng báo "2 trang ĐẠT" trong khi
tệp PDF nộp đi dày 3 trang — lỗi **BD-08**, chi tiết ở `LOI-PHAT-HIEN.md`.

Chỉ cần đo lại (ảnh và nhãn đã có trong repo): **`python scripts/do_luong.py`**.
Khoảng 40 giây cho 33 ảnh. Kết quả ra `ket_qua/tesseract/`:

- `bao_cao.md` — báo cáo cho người không đọc code (8 mục, mỗi bảng trả lời một câu hỏi)
- `cham_diem.json` — toàn bộ số đo, máy đọc được
- `ket_qua_tho.json` — nguyên văn model trả về từng ảnh, để truy lại khi nghi ngờ

Tuỳ chọn hay dùng:

```bash
python scripts/do_luong.py --lap 5              # đo dao động giữa các lần chạy (sigma)
python scripts/do_luong.py --nguong-hitl 0.9    # thử ngưỡng cổng HITL khác
python scripts/do_luong.py --model luon_tu_choi # model đối chứng (xem dưới)
```

## Bộ kiểm thử — 296 ca, kiến trúc BDD ba tầng

```bash
pytest                        # tất cả: 230 passed · 61 xfailed · 3 skipped · 2 failed*
pytest -m "not cong_nghiep_vu"   # bỏ cổng nghiệp vụ -> xanh hoàn toàn
pytest tests/test_luat_so_khop.py   # 47 ca, 0,1 giây, không cần OCR
pytest tests/test_du_lieu.py -k "cccd_sach_01"   # chạy đúng một ảnh
pytest tests/test_du_lieu.py -k "ho_ten"         # chạy đúng một trường, mọi ảnh
```

\* Hai ca đỏ đều là **cùng một cổng nghiệp vụ** (bản Gherkin + bản hồi quy) —
**đó là kết luận, không phải test hỏng** (xem dưới).

| Tệp | Ca | Kiểm cái gì | Thời gian |
|---|---|---|---|
| `features/*.feature` | 38 ca | **Gherkin tiếng Việt** — 14 kịch bản, trong đó 5 khung kịch bản nở theo bảng Dữ liệu thành 38 ca chạy. AC1/AC2/AC3 chép gần nguyên văn từ đề, góc nhìn nghiệp vụ, và sổ giới hạn. Ban QLDA đọc được mà không mở code | 12 s |
| `test_kien_truc.py` | 13 | **Fitness function kiến trúc** — feature không được dính từ kỹ thuật, bước Gherkin không được import driver, lớp đối tượng không được chứa assert | 0,2 s |
| `test_luat_so_khop.py` | 47 | **Luật "đúng là gì" của Bước 1** — 6 tình huống đề nêu, từng kiểu trường, 6 phán quyết, ranh giới ngưỡng khớp mờ. Đây là *cái thước đo*: sai ở đây thì mọi con số trong báo cáo sai theo, kiểu im lặng | 0,1 s |
| `test_nop_bai.py` | 28 | **Ràng buộc nghiệm thu của đề**: render báo cáo ra PDF A4 rồi ĐẾM SỐ TRANG THẬT (≤2), canh không mục nào bị cắt cho vừa trang, dấu tiếng Việt không vỡ, và đủ danh sách nộp bài ở mục 06 | 1 s |
| `test_bo_tach.py` | 11 | Đường lỗi của adapter: tệp không tồn tại, ảnh hỏng, ảnh rỗng, doc_type lạ, **tính tất định**, không bịa khi tắt lớp phòng vệ thứ nhất | 4 s |
| `test_dac_ta_ac.py` | 15 | Hợp đồng **AC1/AC2/AC3**, gồm ca **biên** (conf đúng bằng ngưỡng) và ca **cấu hình được** | 30 s |
| `test_du_lieu.py` | 134 | **Mỗi (ảnh × trường) là một ca riêng** — 132 điểm kiểm, có tên riêng trong báo cáo, chạy lẻ được; + 2 ca canh toàn vẹn (số ca = số điểm kiểm trong bộ nhãn, sổ lỗi đã biết khớp báo cáo lỗi) | 33 s |
| `test_hoi_quy.py` | 10 | Chất lượng so với baseline + toàn vẹn bộ nhãn | 35 s |
| `scripts/kiem_tra_bo_test.py` | 8 mutation | **Chính bộ test** — gài lỗi rồi xem có bắt được | 7 phút |

### Xử lý 61 điểm kiểm đang hỏng

Model thật sự yếu, nên 61/129 điểm kiểm KHÔNG ĐẠT. Để nguyên thì bộ test đỏ rực và
không ai đọc nữa — mà một bộ test luôn đỏ thì bằng không có. Cách xử lý: mỗi điểm kiểm
hỏng được gắn vào **một mã lỗi** trong `data/nhan/loi_da_biet.json` và đánh dấu
`xfail(strict=True)`:

| Diễn biến | Kết quả | Nghĩa là |
|---|---|---|
| hỏng → vẫn hỏng | `xfail` | im lặng, đã có mã lỗi theo dõi |
| hỏng → **ĐẠT** | `XPASS` ⇒ **ĐỎ** | lỗi đã được sửa, bắt phải đóng lỗi và chốt lại sổ |
| ĐẠT → hỏng | `FAIL` ⇒ **ĐỎ** | hồi quy thật |

Nên bộ test **chỉ đỏ khi hành vi đổi** — đúng thứ cần biết khi thay model.
Chốt lại sổ: `python scripts/chot_loi_da_biet.py`.
Phân bố hiện tại: LOI-03 ×42 · LOI-01 ×12 · LOI-05 ×6 · LOI-02 ×1.

### Kiến trúc ba tầng — để bài 2 (web) và mobile dùng lại

```
features/*.feature      Gherkin nghiệp vụ. KHÔNG đổi khi thêm nền tảng.
      ↓
tests/test_bdd_*.py     Bước Cho/Khi/Thì. Chỉ gọi qua lớp đối tượng.
      ↓
doi_tuong/              ĐÂY là chỗ duy nhất đổi khi thêm nền tảng.
    co_so.py              DoiTuongKiemThu · KetQuaTruong · KetQuaXuLy
    ho_so_giay_to.py      bài 1  — model trích xuất
    (trang_tiep_nhan.py)  bài 2  — web, chưa có
    (man_hinh_*.py)       mobile — chưa có
```

Thêm web = viết một lớp cài `mo() / xu_ly() / tu_kiem_tra()` rồi đổi **một fixture**;
bộ bước Gherkin dùng lại nguyên vẹn. Cách làm chi tiết: [`doi_tuong/README.md`](doi_tuong/README.md).

Ranh giới không giữ bằng thiện chí mà bằng `test_kien_truc.py` — nó đã bắt được đúng
một vi phạm của tôi ngay khi vừa viết xong: tên model `"tesseract"` lọt vào kịch bản
nghiệp vụ ở `02-do-tin-cay.feature`.

> **Ghi chú về POM.** Page Object sinh ra để giấu *locator* của một trang web. Bài 1
> không có trang, không có locator, không có trình duyệt — nên lớp ở đây tên là
> `DoiTuongKiemThu` chứ không phải `Page`. Nguyên lý thì giữ nguyên: giấu **cách**
> tương tác, phơi ra **hành vi nghiệp vụ**. Đó mới là thứ làm web và mobile dùng
> chung được bộ bước.

### CI

`.github/workflows/kiem-thu.yml` — cài Tesseract + gói `vie`, chạy theo thứ tự fail
nhanh (luật so khớp → adapter → đặc tả → đo → hồi quy), xuất JUnit XML và đính kèm báo
cáo. Cổng nghiệp vụ chạy ở chế độ `continue-on-error` vì nó đang đỏ có chủ ý; cổng
**hồi quy** mới là cái chặn merge.

> **`test_cong_chat_luong_tuyet_doi` đang ĐỎ, và đó là kết luận của bài.**
> Tesseract không đạt ngưỡng nghiệp vụ trong `cau_hinh.json`
> (điểm tin cậy 49,4% < 55%; trường nghiêm trọng 28,6% < 60%). Test không hỏng —
> nó đang nói đúng cái phải nói. Phần canh hồi quy (9 test) xanh, tức là bộ đo
> vẫn dùng được để theo dõi model tiếp theo.

Kiến trúc cổng gồm ba tầng, để một model dao động vẫn cho được đạt/không đạt:

| Tầng | Canh cái gì | Biên độ tha thứ |
|---|---|---|
| 1. Bất biến | bịa dữ liệu (AC3), lỗi hạ tầng, canary | **không có** — vi phạm là FAIL |
| 2. Biên độ | các chỉ số tổng so với baseline | `max(3·sigma, 0.05)`, sigma **đo được** bằng `--lap` |
| 3. Ca cụ thể | trường nào từ đúng thành sai | báo tên ảnh + tên trường, kể cả khi số tổng còn trong biên |

Đo thật trên máy này: **sigma = 0.0000 qua 3 lần chạy** — Tesseract tất định, nên
tầng 2 thu về so khớp chính xác. Cơ chế biên vẫn nằm đó cho model có nhiệt độ.

Thử xem cổng có thật sự bắt được hồi quy (đổi `lang=vie` → `eng`, mô phỏng
"ai đó đổi tham số"):

```bash
python scripts/kiem_tra_hoi_quy.py --model tesseract_eng
# → KHÔNG ĐẠT, exit 1, chỉ đúng 21 trường từ ĐÚNG thành SAI/BỎ SÓT, kèm tên ảnh
```

## Cắm model khác

Bộ đo không biết gì về Tesseract. Viết một lớp cài `trich_xuat(duong_dan_anh,
ma_loai) -> KetQuaTrichXuat` (xem [`bo_do/mo_hinh/co_so.py`](bo_do/mo_hinh/co_so.py)),
khai vào `DANH_MUC` trong [`bo_do/mo_hinh/tesseract.py`](bo_do/mo_hinh/tesseract.py),
rồi `--model <tên>`. Không phải sửa `so_khop.py`, `cham_diem.py` hay `bao_cao.py`.

Trong repo có sẵn 4 mục: `tesseract`, `tesseract_psm4`, `tesseract_eng` và
`luon_tu_choi`.

`luon_tu_choi` là **model đối chứng**: nó không bao giờ trả gì. Nó có mặt để
chứng minh bộ đo không bị lừa — model này đạt 100% phần AC3 nhưng 0% accuracy,
nên điểm tổng phải thấp. Nếu một ngày nó không thấp thì bộ đo sai, không phải
model tốt.

```bash
python scripts/do_luong.py --model luon_tu_choi
```

## Cấu trúc

```
cau_hinh.json                ngưỡng HITL + ngưỡng đạt/không đạt (đổi ở đây, không sửa code)
bo_do/
  schema.py                  trường nào, mức nghiêm trọng nào, mốc neo nào
  chuan_hoa.py               chuẩn hoá giá trị trước khi so khớp
  so_khop.py                 BƯỚC 1: luật "đúng là gì" -> 6 phán quyết
  cham_diem.py               tổng hợp số đo, hiệu chuẩn conf, quét ngưỡng HITL
  bao_cao.py                 xuất Markdown cho người không đọc code
  hoi_quy.py                 BƯỚC 5: ba tầng cổng + baseline
  chay.py                    chỗ duy nhất biết cách chạy một lượt đo
  mo_hinh/co_so.py           giao diện model (đổi model chỉ sửa ở tầng này)
  mo_hinh/tesseract.py       model đang đo + bộ tách trường + canary
data/
  anh/                       33 ảnh sinh ra (tái lập được bằng seed)
  nhan/ban_ke_sinh.json      bản kê: sinh gì, seed nào, làm xấu bằng phép nào
  nhan/doc_lai_doc_lap.csv   lượt gán nhãn thứ hai (annotator #2 mở ảnh đọc lại — xem GH-04)
  nhan/nhan.jsonl            BỘ NHÃN dùng để đo (máy đọc được, tách rời code)
  nhan/do_dong_thuan.json    độ đồng thuận giữa hai lượt + giới hạn của nó
ket_qua/baseline.json        baseline đã chốt, gắn dấu vân tay bộ dữ liệu
tests/test_hoi_quy.py        bộ test tự động
```

## Hai điều cần biết trước khi đọc con số

**Dữ liệu là giấy tờ mô phỏng, không phải giấy tờ thật.** Số định danh dùng tiền
tố `000` — không phải mã tỉnh hợp lệ, nên không thể trùng số của người thật. Không
có ảnh giấy tờ của bất kỳ ai trong repo này. Đổi lại, con số đo được nói về
*giấy tờ mô phỏng*, không nói trực tiếp về giấy tờ thật. Xem mục Giới hạn trong
[`BAO-CAO.md`](BAO-CAO.md).

**Có 3 trường bị loại khỏi mọi phép tính** ("vùng xám"): dấu giáp lai đè kín đúng
ô giá trị, người gán nhãn cũng không đọc được, nhưng ảnh vẫn đọc được ở các
trường khác. Đòi model trả đúng ở đó là đòi nó bịa; thưởng cho việc nó im lặng ở
đó cũng sai. Nên chỗ đó được báo riêng, không cộng vào accuracy.
