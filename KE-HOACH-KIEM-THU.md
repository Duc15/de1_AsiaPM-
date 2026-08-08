# Kế hoạch kiểm thử — US-M1-EXTRACT-001

## 1. Mục tiêu

Trả lời một câu hỏi nghiệp vụ: **cụm trích xuất nằm giữa ảnh dân chụp và người
duyệt có đáng tin không, và biết điều đó bằng cách nào.** Kèm theo: để lại một
bộ đo mà tháng sau cắm model khác vào vẫn chạy được, không phải viết lại.

## 2. Đối tượng kiểm thử (SUT)

**Cụm trích xuất**, không phải Tesseract trần:

| Thành phần | Phiên bản / vị trí |
|---|---|
| OCR engine | Tesseract 5.4.0.20240606, `lang=vie`, `--psm 6` |
| Bộ tách trường (neo theo nhãn in) | `bo_do/mo_hinh/tesseract.py` |
| Bộ đọc ô tích (mật độ mực + OCR nhãn) | cùng file, `_doc_o_tich` |
| Chính sách từ chối | < 8 từ hoặc conf ảnh < 30 ⇒ trả rỗng kèm lý do |
| Hợp đồng đầu ra AC1–AC3 | `bo_do/so_bang_chung.py` (bản hiện thực tham chiếu) |

Ranh giới này quan trọng: đo Tesseract trần thì không có "trường" nào để đo — nó
chỉ trả chữ. Cái hệ thống ở mục 01 tiêu thụ là **trường có tên kèm điểm tin cậy**,
nên đó mới là thứ phải kiểm thử.

## 3. Cơ sở kiểm thử (test basis)

- US-M1-EXTRACT-001 kèm AC1 / AC2 / AC3 — mục 02 của đề
- Cấu trúc đầu ra (`doc_type`, `fields[]`, `ten_truong`, `gia_tri`, `confidence`,
  `nguon`) — mục 03
- Ràng buộc pháp lý: model không bao giờ tự quyết hồ sơ, cổng HITL bắt buộc — mục 01
- Hai loại giấy tờ và danh sách trường — mục 03

## 4. Phạm vi

**Trong phạm vi**

- Hợp đồng đầu ra AC1 / AC2 / AC3 (kiểm thử theo đặc tả)
- Độ chính xác từng trường, cắt theo loại giấy tờ × bậc chất lượng ảnh
- Hành vi trên ảnh không đọc được (không bịa / từ chối kèm lý do)
- Hiệu chuẩn điểm tin cậy và điểm đặt ngưỡng cổng HITL
- Hiệu năng: thời gian xử lý một ảnh
- Tính lặp lại giữa các lần chạy (dao động)
- Kiểm thử hồi quy khi đổi model / đổi tham số

**Ngoài phạm vi — và vì sao**

| Không kiểm | Lý do |
|---|---|
| Tích hợp với hệ thống AsiaPM | đề không cấp quyền truy cập hệ thống/API/mã nguồn |
| Phần "**hiển thị nổi bật** cho người duyệt" của AC2 | thuộc giao diện người duyệt; chỉ kiểm được tới lớp dữ liệu — xem mục 6 |
| Tải, đồng thời, chịu lỗi, phục hồi | không có môi trường; đề không nêu NFR |
| Bảo mật ở mức hệ thống | ngoài đối tượng; quyền riêng tư chỉ áp dụng khi tạo dữ liệu |
| Giấy tờ thật của người thật | ràng buộc dữ liệu cá nhân trong đề — không thương lượng |
| Loại giấy tờ ngoài CCCD và Mẫu 01 | đề giới hạn phạm vi ở hai loại này |

## 5. Chiến lược và kỹ thuật thiết kế ca kiểm thử

| Kỹ thuật | Áp dụng vào đâu | Ca |
|---|---|---|
| **Phân hoạch tương đương** | 2 loại giấy tờ × 5 bậc chất lượng ảnh = 10 phân hoạch, mỗi phân hoạch ≥ 3 ảnh; mỗi (ảnh × trường) là một ca độc lập trong runner | 132 |
| **Phân tích giá trị biên** | ngưỡng HITL: conf `<`, `=`, `>` ngưỡng (TC-AC2-01/02/03); ngưỡng khớp mờ địa chỉ (TC-LUAT-50); ranh giới đọc được / không đọc được | 6 |
| **Bảng quyết định** | nhãn có/không giá trị × model trả/không trả ⇒ 6 phán quyết (TC-LUAT-40..47) | 8 |
| **Kiểm thử đơn vị cho thước đo** | luật so khớp Bước 1 + chuẩn hoá — kiểm *cái thước*, không kiểm *cái được đo*; chạy 0,1 s nên gắn được vào mọi commit | 47 |
| **Kiểm thử theo đặc tả** | `tests/test_dac_ta_ac.py` — truy vết 1:1 tới AC1/AC2/AC3 | 15 |
| **Kiểm thử đường lỗi (negative)** | tệp không tồn tại · ảnh hỏng · ảnh rỗng · ảnh 1×1 · doc_type lạ · tên model lạ · tính tất định | 11 |
| **Kiểm thử dựa trên rủi ro** | trọng số ×3 cho trường mà sai một ký tự là sai người (`so_dinh_danh`, `ho_ten`) | — |
| **Kiểm thử thăm dò** | đọc bằng mắt từng trường sai **trên ảnh sạch nhất**; cách tìm ra BD-01…BD-04 | — |
| **Kiểm thử đột biến** | `scripts/kiem_tra_bo_test.py` — gài lỗi có chủ ý để chứng minh bộ test có răng | 8 |
| **Kiểm thử hồi quy** | baseline + cổng 3 tầng + sổ lỗi đã biết `xfail(strict)` | 10 |
| **Kiểm thử chính bài nộp** | mục 06 của đề là danh sách nghiệm thu: render báo cáo ra PDF rồi đếm số trang thật, canh không mục nào bị cắt cho vừa trang, đủ sản phẩm phải nộp | 27 |

**Tổng: 244 ca tự động.** Không có ca nào chạy tay — kể cả lượt gán nhãn thứ hai
(việc của người) cũng được đóng băng thành `doc_lai_doc_lap.csv` để máy đọc lại.

**Xử lý điểm kiểm đang hỏng.** 61/129 điểm kiểm KHÔNG ĐẠT vì model thật sự yếu. Để
nguyên thì bộ test đỏ rực và mất tác dụng cảnh báo. Mỗi điểm kiểm hỏng vì thế được quy
về **một mã lỗi** (`data/nhan/loi_da_biet.json`) và đánh `xfail(strict=True)`:
*hỏng → vẫn hỏng* = im lặng; *hỏng → ĐẠT* = **XPASS ⇒ đỏ**, bắt đóng lỗi; *ĐẠT → hỏng*
= **FAIL ⇒ đỏ**. Bộ test chỉ đỏ khi **hành vi đổi**.

**Nguyên tắc chọn dữ liệu:** không dùng giấy tờ thật của bất kỳ ai. Số định danh
dùng tiền tố `000` — không phải mã tỉnh hợp lệ theo TT 59/2021, nên không thể
trùng số của người thật. Bộ ảnh sinh bằng script, tất định theo seed, gắn dấu vân
tay SHA-256 để baseline không so nhầm hai bộ dữ liệu khác nhau.

## 6. Ma trận truy vết đặc tả ↔ ca kiểm thử

| AC | Điều khoản | Ca kiểm thử | Kết quả |
|---|---|---|---|
| Bước 1 | luật "đúng là gì" — 6 tình huống đề nêu | `TC-LUAT-01..06` | ĐẠT |
| Bước 1 | luật theo từng kiểu trường + 6 phán quyết + biên | `TC-LUAT-10..52` | ĐẠT (bắt được BD-05) |
| — | đường lỗi adapter, tính tất định | `TC-BT-01..11` | ĐẠT (bắt được BD-06) |
| AC1 | trường được điền vào **schema chuẩn** | `TC-AC1-01` | ĐẠT |
| AC1 | **mỗi trường kèm một điểm tin cậy** | `TC-AC1-02` | ĐẠT *(sau khi sửa LOI-04)* |
| AC1 | `nguon` thuộc tập đặc tả | `TC-AC1-03` | ĐẠT |
| AC1 | **ảnh gốc được liên kết trong sổ bằng chứng** | `TC-AC1-04` | ĐẠT *(sau khi sửa LOI-04)* |
| AC1 | **nhật ký worker được ghi** | `TC-AC1-05` | ĐẠT *(sau khi sửa LOI-04)* |
| AC2 | trường **dưới ngưỡng** bị đánh dấu cần người xác nhận | `TC-AC2-01` | ĐẠT *(sau khi sửa LOI-05)* |
| AC2 | trường trên ngưỡng **không** bị đánh dấu thừa | `TC-AC2-02` | ĐẠT |
| AC2 | ranh giới: conf **đúng bằng** ngưỡng | `TC-AC2-03` | ĐẠT |
| AC2 | ngưỡng **cấu hình được** | `TC-AC2-04` | ĐẠT |
| AC2 | "được **hiển thị nổi bật** cho người duyệt" | — | **KHÔNG KIỂM ĐƯỢC** (giao diện người duyệt ngoài phạm vi). Kiểm tới lớp dữ liệu: cờ `can_nguoi_xac_nhan` có mặt và đúng. |
| AC3 | hệ thống **KHÔNG bịa dữ liệu** | `TC-AC3-01` | ĐẠT (0/24 trường) |
| AC3 | hồ sơ đặt trạng thái **"cần bổ sung"** | `TC-AC3-02` | ĐẠT *(sau khi sửa LOI-06)* |
| AC3 | **kèm lý do** | `TC-AC3-03` | ĐẠT *(sau khi sửa LOI-06)* |
| AC3 | mặt trái: hồ sơ đi tiếp phải đủ trường bắt buộc | `TC-AC3-04` | ĐẠT |
| — | bao phủ của chính bộ test | `TC-BAO-PHU-01/02` | ĐẠT |

Ba dòng ghi *"sau khi sửa"* là lỗi do chính việc viết ca kiểm thử theo đặc tả tìm
ra — trước đó đầu ra thiếu hẳn liên kết ảnh gốc, nhật ký worker, cờ HITL và trạng
thái hồ sơ. Chi tiết: `LOI-PHAT-HIEN.md` (LOI-04, LOI-05, LOI-06).

**Bao phủ đặc tả: 14/15 điều khoản kiểm được, 1 điều khoản ngoài phạm vi và được
ghi rõ là không kiểm được.** Không có điều khoản nào bị bỏ quên trong im lặng.

## 7. Tiêu chí vào / ra

**Vào (không đủ thì không chạy đo):**

1. Canary hạ tầng xanh — render một dòng chữ sạch, model phải đọc lại đúng.
2. Bộ nhãn tồn tại, đúng schema, độ đồng thuận hai lượt ≥ 95 %.
3. Dấu vân tay bộ dữ liệu khớp baseline (nếu so hồi quy).

**Ra (điều kiện tuyên bố "đã kiểm thử xong"):**

| # | Tiêu chí | Trạng thái |
|---|---|---|
| 1 | Toàn bộ ca AC ĐẠT, hoặc ca không đạt được ghi thành lỗi có mã | ✅ 15/15 ĐẠT |
| 2 | Không mutation nào sống sót mà chưa truy nguyên | ✅ 7 bị bắt, 1 sống sót đã truy nguyên |
| 3 | Không có lỗi hạ tầng (`LOI_HE_THONG`) trong lượt đo cuối | ✅ 0 |
| 4 | Mọi điểm kiểm hỏng quy được về một mã lỗi | ✅ 61/61, 0 "chưa phân loại" |
| 5 | Mọi lỗi mức Nghiêm trọng có khuyến nghị xử lý | ✅ 3/3 |
| 6 | Báo cáo nêu **kết luận go / no-go** kèm điều kiện, và nêu rõ phần phép đo không chứng minh được | ✅ |
| 7 | Bộ đo chạy được ở máy khác máy người viết | ✅ CI Ubuntu, `.github/workflows/kiem-thu.yml` |

## 8. Sổ rủi ro

| Mã | Rủi ro | Khả năng | Tác động | Giảm thiểu |
|---|---|---|---|---|
| R1 | **Nhãn sai ⇒ mọi kết luận sai.** Nhãn là thước đo duy nhất. | Trung bình | Rất cao | Hai lượt gán nhãn độc lập; đo đồng thuận bằng đúng luật của Bước 1; vùng xám cho trường người cũng không đọc được |
| R2 | **Lỗi của bộ đo bị quy cho model** | **Cao** (đã xảy ra 3 lần) | Cao | Canary trước mỗi lượt; tách `LOI_HE_THONG` khỏi accuracy; đọc từng dòng lỗi trên ảnh sạch; mutation testing |
| R3 | Dữ liệu mô phỏng không đại diện giấy tờ thật | Cao | Cao | Ghi rõ là giả định lớn nhất; con số chỉ dùng để **so sánh model trên cùng bộ ảnh** |
| R4 | Model đổi ⇒ bộ đo lỗi thời | Cao | Trung bình | Adapter tách rời; bộ đo không biết gì về Tesseract; baseline + cổng hồi quy |
| R5 | Chọn ngưỡng khớp quá sát bộ ảnh nhỏ (overfit) | Trung bình | Trung bình | Báo cả bảng quét ngưỡng thay vì một con số "tối ưu"; ngưỡng nằm trong `cau_hinh.json` |
| R6 | Lộ dữ liệu cá nhân | Thấp | Rất cao | 100 % dữ liệu tổng hợp; tiền tố `000` không phải mã tỉnh hợp lệ; không tải ảnh giấy tờ từ internet |
| R7 | Một người vừa tạo dữ liệu vừa gán nhãn vừa đo | **Cao** | Trung bình | Ghi nhận thẳng là giới hạn; lượt gán nhãn 2 chỉ dùng cho phán quyết đọc được/không, phần dễ thiên vị nhất bị loại khỏi kết luận |

## 9. Môi trường kiểm thử

| | |
|---|---|
| Hệ điều hành | Windows 10 Pro 22H2 (build 19045) |
| Python | 3.14.7 |
| OCR | Tesseract 5.4.0.20240606 — gói ngôn ngữ: `eng`, `osd`, `vie` |
| Thư viện | pytesseract, Pillow 12.3.0, numpy 2.5.1, pytest 8.x |
| Phần cứng | CPU (AVX2/FMA), không dùng GPU, chạy tuần tự một ảnh một lần |
| Tất định | seed cố định; đo được **sigma = 0,0000 qua 3 lần chạy** |

Thời gian đo phụ thuộc máy — con số trong báo cáo là **để so tương đối giữa các
bậc ảnh trên cùng một máy**, không phải cam kết SLA.

## 10. Sản phẩm bàn giao

| Sản phẩm | Vị trí |
|---|---|
| Kế hoạch kiểm thử (tài liệu này) | `KE-HOACH-KIEM-THU.md` |
| Bộ dữ liệu + cách sinh | `data/anh/`, `scripts/sinh_du_lieu.py`, `data/nhan/ban_ke_sinh.json` |
| Bộ nhãn máy đọc được | `data/nhan/nhan.jsonl` + `do_dong_thuan.json` |
| Sổ ca kiểm thử (sinh tự động) | `ket_qua/tesseract/truong_hop_kiem_thu.md` |
| Kiểm thử theo đặc tả | `tests/test_dac_ta_ac.py` |
| Kiểm thử hồi quy | `tests/test_hoi_quy.py`, `bo_do/hoi_quy.py` |
| Kiểm thử chính bộ test | `scripts/kiem_tra_bo_test.py` |
| Báo cáo lỗi | `LOI-PHAT-HIEN.md` |
| Báo cáo kiểm thử (≤ 2 trang) | `BAO-CAO.md` |
| Phụ lục | `PHU-LUC.md` |
| Prompt AI đã dùng + chỗ AI sai | `PROMPTS.md` |
