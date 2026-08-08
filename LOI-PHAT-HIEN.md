# Báo cáo lỗi — US-M1-EXTRACT-001

Lượt đo: `tesseract-5.4.0.20240606-vie-psm6` · 33 ảnh · dấu vân tay dữ liệu
`46fa73e94a62a0f5`. Tái hiện toàn bộ bằng:

```bash
python scripts/sinh_du_lieu.py && python scripts/gan_nhan.py && python scripts/do_luong.py
```

**Thang mức nghiêm trọng**

| Mức | Nghĩa |
|---|---|
| Nghiêm trọng | Dữ liệu sai vào hồ sơ chính thức, hoặc vi phạm ràng buộc pháp lý (AC3 / cổng HITL) |
| Nặng | Một mảng chức năng lớn không dùng được |
| Trung bình | Giảm hiệu quả, có cách đi vòng |

**Tổng hợp**

| Mã | Tiêu đề | Mức | Trạng thái |
|---|---|---|---|
| LOI-01 | Sai dấu tiếng Việt ở họ tên với conf cao, lọt cổng HITL | **Nghiêm trọng** | Mở |
| LOI-02 | Điểm tin cậy trường ô tích là hằng số 0,95 — không lọc được gì | **Nghiêm trọng** | Mở |
| LOI-10 | **44 % hồ sơ người đọc được vẫn bị trả về bắt dân nộp lại** | **Nghiêm trọng** | Mở |
| LOI-03 | Sập gần như hoàn toàn từ bậc ảnh trung bình | Nặng | Mở |
| LOI-04 | Điểm tin cậy hiệu chuẩn kém (ECE 0,183) | Nặng | Mở |
| LOI-05 | Sai giá trị số trên chữ viết tay (thu nhập, diện tích) | Nặng | Mở |
| LOI-06 | 7 ảnh: OCR ra chữ nhưng bộ tách không neo được trường nào | Trung bình | Mở |
| LOI-07 | Đầu ra thiếu liên kết ảnh gốc + nhật ký worker — **vi phạm AC1** | Nặng | **Đã sửa** |
| LOI-08 | Trường dưới ngưỡng không được đánh dấu — **vi phạm AC2** | **Nghiêm trọng** | **Đã sửa** |
| LOI-09 | Hồ sơ không đọc được thiếu trạng thái + lý do — **vi phạm AC3** | Nặng | **Đã sửa** |

LOI-07/08/09 là lỗi của **hợp đồng đầu ra**, do chính việc viết ca kiểm thử theo
đặc tả tìm ra. Lỗi trong bộ đo (không phải trong SUT) ghi riêng ở mục cuối.

---

## LOI-01 — Sai dấu tiếng Việt ở họ tên với điểm tin cậy cao, lọt cổng HITL

**Mức:** Nghiêm trọng · **Ưu tiên:** Cao · **Trạng thái:** Mở ·
**Thành phần:** OCR (Tesseract `vie`) · **AC liên quan:** AC2 (cổng HITL không chặn được)

**Bước tái hiện**
1. Chạy ba lệnh ở đầu tài liệu.
2. Mở `ket_qua/tesseract/bao_cao.md`, mục 6, bảng "Rò rỉ ở trường nghiêm trọng".

**Kỳ vọng:** trường bị đọc sai phải mang confidence dưới ngưỡng để bị gắn cờ và
đẩy sang người duyệt.

**Thực tế:** 6 trường họ tên sai nhưng confidence **0,85–0,94**, tự động qua cổng:

| Ảnh | Nhãn | Model trả | Conf | Bậc ảnh |
|---|---|---|---|---|
| cccd_sach_01 | TRẦN THỊ MAI | TR**Ấ**N THỊ MAI | 0,91 | sạch |
| cccd_sach_02 | NGUYỄN VĂN HÙNG | NGUY**Ê**N VĂN HÙNG | 0,85 | sạch |
| cccd_sach_03 | LÊ THỊ NGỌC HUYỀN | LÊ THỊ NGỌC *(mất HUYỀN)* | 0,93 | sạch |
| cccd_nhe_02 | HOÀNG MINH TUẤN | HOÀNG MINH TU**Ầ**N | 0,86 | nhẹ |
| cccd_trung_binh_03 | NGUYỄN VĂN HÙNG | NGUY**Ê**N VĂN *(mất HÙNG)* | 0,94 | trung bình |
| mau_01_sach_02 | PHẠM ĐỨC THẮNG | PH**A**M ĐỨC THẮNG | 0,91 | sạch |

**Bằng chứng:** `ket_qua/tesseract/cham_diem.json` → `cong_hitl.ro_ri_nghiem_trong`

**Tác động nghiệp vụ:** hồ sơ NƠXH mang tên sai dấu là hồ sơ của **người khác**.
Cổng HITL — thứ được đề mô tả là ràng buộc pháp lý — không chặn được, vì model
**tự tin nhất đúng ở chỗ nó sai nguy hiểm nhất**. 4/6 ca xảy ra trên ảnh **sạch**,
nên siết chất lượng ảnh đầu vào không vá được lỗi này.

**Sắc thái phải nói kèm:** lượt đọc lại cho thấy trên ảnh bậc **trung bình**, chính người
cũng không nhìn rõ dấu ngã/huyền và phải suy từ ngữ cảnh. Nên một phần lỗi `sai_dau` ở
bậc đó có thể do thông tin đã mất trong ảnh chứ không do model. Điều này **không** làm
nhẹ 4/6 ca xảy ra trên ảnh **sạch** — ở đó dấu hiện rõ với người, và model vẫn đọc sai.

**Khuyến nghị:** (a) `ho_ten` và `so_dinh_danh` luôn qua người duyệt bất kể conf;
(b) đối chiếu chéo với CSDL quốc gia về dân cư — lỗi dấu khôi phục được bằng đối
chiếu, không khôi phục được bằng OCR tốt hơn.

---

## LOI-02 — Điểm tin cậy của trường ô tích là hằng số 0,95

**Mức:** Nghiêm trọng · **Ưu tiên:** Cao · **Trạng thái:** Mở ·
**Thành phần:** bộ đọc ô tích (`_doc_o_tich`) · **AC liên quan:** AC1, AC2

**Bước tái hiện**
```bash
python -c "import json;d=json.load(open('ket_qua/tesseract/cham_diem.json',encoding='utf-8'));\
print(sorted({x['confidence'] for x in d['chi_tiet'] if x['ten_truong']=='hinh_thuc' and x['confidence']}))"
```

**Kỳ vọng:** confidence phản ánh mức độ chắc chắn, tức là phải **biến thiên** giữa
ca dễ và ca khó — như trường OCR (42 giá trị khác nhau trên 59 trường, 0,00–0,96).

**Thực tế:** cả 7 trường `hinh_thuc` có confidence **đúng bằng 0,95**, độ lệch
chuẩn **0**. Công thức `min(0,95; 0,55 + chênh_lệch_mực × 3)` luôn chạm trần vì
chênh lệch mực giữa ô có dấu tích và ô trống luôn lớn.

**Tác động:** trường này **luôn** tự động qua cổng HITL ở mọi ngưỡng ≤ 0,95, kể cả
khi sai. Đúng một ca như vậy đã xảy ra: `mau_01_trung_binh_01` — nhãn `mua`, model
trả `thuê mua`, conf 0,95 ⇒ **lọt cổng**. Hình thức đăng ký sai nghĩa là hồ sơ vào
sai luồng xét duyệt (mua / thuê / thuê mua có điều kiện và giá khác nhau).

Đây không phải "conf hơi lệch" mà là **conf không tồn tại**: một hằng số đội lốt
điểm tin cậy. Nguy hiểm hơn conf sai, vì nó qua được mọi kiểm tra hình thức của AC1.

**Khuyến nghị:** (a) trước mắt hạ trần conf của luật đếm mực xuống dưới ngưỡng cổng
để trường này luôn về tay người; (b) lâu dài thay bằng bộ phát hiện ô tích thật và
hiệu chuẩn conf theo chênh lệch mực đã chuẩn hoá; (c) thêm một ca kiểm thử canh
**phương sai** của conf theo từng trường, không chỉ canh khoảng [0,1].

---

## LOI-10 — 44 % hồ sơ người đọc được vẫn bị trả về bắt dân nộp lại

**Mức:** Nghiêm trọng · **Ưu tiên:** Cao · **Trạng thái:** Mở ·
**AC liên quan:** AC3 (mặt trái — trả về quá tay)

**Bước tái hiện:** `python scripts/do_luong.py`, đọc khối "MỨC HỒ SƠ" ở cuối output,
hoặc mục 1 của `ket_qua/tesseract/bao_cao.md`.

**Kỳ vọng:** hồ sơ mà **người** đọc được thì hệ thống phải xử lý được, hoặc chỉ gắn cờ
những trường không chắc để người duyệt điền — chứ không bắt dân đi lại.

**Thực tế:** trong 27 hồ sơ người gán nhãn đọc được, **12 hồ sơ (44,4 %)** bị đặt trạng
thái `can_bo_sung`:

| Lý do | Số hồ sơ |
|---|---|
| Đọc được chữ nhưng không xác định được trường nào (LOI-06) | 6 |
| Thiếu trường bắt buộc (`so_dinh_danh` hoặc `ho_ten`) | 4 |
| Chính sách từ chối kích hoạt **trên ảnh người đọc được** — từ chối oan | 2 |

Toàn bộ 12 hồ sơ nằm ở bậc `trung_binh` (6) và `nang` (6).

**Tác động nghiệp vụ:** đây là con số **người dân thật sự cảm nhận**, và nó tệ hơn con
số mức trường. Accuracy 41,9 % nghe như "một nửa việc vẫn xong"; ở mức hồ sơ thì nghĩa
là **gần một nửa người dân bị gọi quay lại UBND xã lần nữa** — với NƠXH thì đó thường là
một buổi nghỉ làm. Trung bình theo trường che mất tác động này, vì hồ sơ thiếu một
trường bắt buộc hỏng y như hồ sơ thiếu bốn trường.

**Khuyến nghị:** (a) không để "thiếu trường bắt buộc" tự động thành trả về — đẩy sang
người duyệt nhập tay trước, chỉ trả về khi **người duyệt** cũng không đọc được;
(b) kiểm chất lượng ảnh ngay lúc nộp để dân chụp lại **tại chỗ** thay vì bị gọi lại;
(c) xem lại 2 ca từ chối oan: chính sách từ chối (< 8 từ hoặc conf < 30) đang chặn cả
ảnh mà người đọc được.

---

## LOI-03 — Sập gần như hoàn toàn từ bậc ảnh trung bình

**Mức:** Nặng · **Ưu tiên:** Cao · **Trạng thái:** Mở

**Kỳ vọng:** chất lượng giảm dần thì độ chính xác giảm dần.

**Thực tế:** có một **vách**, không phải dốc:

| sạch | nhẹ | trung bình | nặng | không đọc được |
|---|---|---|---|---|
| 66,7 % | 66,7 % | **10,3 %** | **0 %** | 100 % *(từ chối đúng)* |

Bậc trung bình bỏ sót 18/28 trường; bậc nặng bỏ sót 21/21. Bậc trung bình mô phỏng
đúng tình huống đề mô tả: chụp nghiêng, loá đèn huỳnh quang, ảnh bị giảm phân giải
~×0,6 — tức là **ảnh điển hình của người dân chụp ở sảnh UBND xã**.

**Tác động:** ngưỡng dùng được của model nằm ở chỗ mà thực tế vận hành hiếm khi
đạt tới. **Khuyến nghị:** kiểm chất lượng ảnh **ngay lúc nộp** và bắt chụp lại —
thay đổi ở giao diện nộp hồ sơ, không phải ở model.

---

## LOI-04 — Điểm tin cậy hiệu chuẩn kém

**Mức:** Nặng · **Ưu tiên:** Cao · **Trạng thái:** Mở

**Thực tế:** ECE **0,183**; conf trung bình khi đúng 0,892, khi sai 0,742 (AUC
0,839 — có tương quan, nhưng lệch mức nghiêm trọng):

| Khoảng conf | Model tự báo | Accuracy thực tế | Lệch |
|---|---|---|---|
| 0,70–0,80 | 0,757 | **0,200** | +0,557 |
| 0,80–0,90 | 0,848 | 0,429 | +0,420 |
| 0,90–1,00 | 0,948 | 0,833 | +0,115 |

**Tác động:** cổng HITL của AC2 lọc bằng chính con số này. Conf 0,76 mà thực tế
đúng 20 % nghĩa là mọi tính toán khối lượng tái duyệt dựa trên conf đều sai lệch.

**Khuyến nghị:** hiệu chuẩn lại (Platt/isotonic) trên tập giữ riêng trước khi dùng
conf làm cổng, hoặc đặt ngưỡng theo **accuracy thực đo từng khoảng** thay vì theo
giá trị conf danh nghĩa.

---

## LOI-05 — Sai giá trị số trên chữ viết tay

**Mức:** Nặng · **Ưu tiên:** Trung bình · **Trạng thái:** Mở

`mau_01.thu_nhap_hang_thang` accuracy **25,0 %**, `mau_01.dien_tich_binh_quan`
**27,3 %**. Ví dụ: `11.000.000` → `17,000,000`; `10 m²` → `7`; `18,5 m²` → `18`.

**Tác động:** hai trường này quyết định điều kiện hưởng chính sách NƠXH. Sai một
chữ số trong thu nhập thì người duyệt nhìn ra, nhưng `18,5 → 18` thì **không ai
nhìn ra** — nó vẫn là một con số hợp lý.

**Khuyến nghị:** không dùng OCR cho Mẫu 01 viết tay; nhập tay có kiểm tra chéo,
hoặc chuyển sang biểu khai điện tử.

---

## LOI-06 — OCR ra chữ nhưng bộ tách không neo được trường nào

**Mức:** Trung bình · **Ưu tiên:** Trung bình · **Trạng thái:** Mở

7/33 ảnh: `cccd_nang_01`, `cccd_nang_02`, `mau_01_trung_binh_02`,
`mau_01_trung_binh_03`, `mau_01_nang_01`, `mau_01_nang_02`,
`mau_01_khong_doc_duoc_03`.

Ở những ảnh này Tesseract vẫn đọc ra chữ, nhưng nhãn in bị đọc sai tới mức không
khớp được mốc neo nào ⇒ trả về rỗng. Trong log nó trông **giống hệt** hành vi từ
chối đúng theo AC3, nhưng nguyên nhân khác hẳn và người phải sửa cũng khác.

**Tác động:** nếu không tách riêng, chỉ số "từ chối đúng theo AC3" bị thổi phồng
bằng các ca thực chất là bộ tách gãy. Bộ đo hiện đã đếm riêng ba cột (`từ chối
theo chính sách` 7 · `không neo được trường` 7 · `lỗi hạ tầng` 0).

---

## LOI-07 — Đầu ra thiếu liên kết ảnh gốc và nhật ký worker (vi phạm AC1)

**Mức:** Nặng · **Trạng thái:** **Đã sửa** · **Phát hiện bởi:** viết ca `TC-AC1-04`, `TC-AC1-05`

AC1 đòi "*ảnh gốc được liên kết trong sổ bằng chứng, và nhật ký worker được ghi*".
Đầu ra ban đầu (`ket_qua_tho.json`) chỉ có `doc_type`, `fields`, `thoi_gian_ms` —
**không có đường dẫn ảnh, không có băm, không có nhật ký**. Không truy ngược được
một trường về đúng file ảnh đã sinh ra nó, tức là mất khả năng đối chứng khi có
khiếu nại.

**Sửa:** thêm `bo_do/so_bang_chung.py` — sinh `so_bang_chung.json` (đường dẫn +
SHA-256 + kích thước mỗi ảnh) và `nhat_ky_worker.log` (một dòng một ảnh).
**Chặn hồi quy:** `TC-AC1-04` kiểm lại SHA-256 với file trên đĩa, `TC-AC1-05` kiểm
số dòng nhật ký khớp số ảnh. Mutation M3 xác nhận ca này bắt được lỗi.

---

## LOI-08 — Trường dưới ngưỡng không được đánh dấu (vi phạm AC2)

**Mức:** Nghiêm trọng · **Trạng thái:** **Đã sửa** · **Phát hiện bởi:** viết ca `TC-AC2-01`

AC2 đòi trường dưới ngưỡng "*bị đánh dấu cần người xác nhận*". Đầu ra ban đầu chỉ
có `confidence`, **không có cờ nào** — bộ đo tính rò rỉ ở mức tổng hợp nhưng không
sinh ra tín hiệu mà hệ thống HITL tiêu thụ được. Nếu đem tích hợp, cổng HITL sẽ
không có gì để lọc.

**Sửa:** mỗi trường mang cờ `can_nguoi_xac_nhan`, quy ước **so sánh ngặt**
(`conf < ngưỡng`), ngưỡng đọc từ `cau_hinh.json`.
**Chặn hồi quy:** `TC-AC2-01` (dưới ngưỡng phải gắn cờ), `TC-AC2-02` (trên ngưỡng
không gắn thừa), `TC-AC2-03` (ca **biên**: conf đúng bằng ngưỡng thì không gắn),
`TC-AC2-04` (ngưỡng phải thật sự cấu hình được, không bị hard-code). Mutation
M1/M2 xác nhận các ca này bắt được lỗi.

---

## LOI-09 — Hồ sơ không đọc được thiếu trạng thái và lý do (vi phạm AC3)

**Mức:** Nặng · **Trạng thái:** **Đã sửa** · **Phát hiện bởi:** viết ca `TC-AC3-02`, `TC-AC3-03`

AC3 đòi "*hồ sơ được đặt trạng thái 'cần bổ sung' kèm lý do*". Đầu ra ban đầu có
`ly_do_tu_choi` ở mức model nhưng **không có trạng thái hồ sơ** — người duyệt không
biết phải bảo dân nộp lại cái gì.

**Sửa:** mỗi hồ sơ mang `trang_thai_ho_so` (`du_dieu_kien_xu_ly` / `can_bo_sung`)
kèm `ly_do` bằng tiếng người. Giả định GĐ-7: cần bổ sung khi model từ chối, khi
không trích được trường nào, hoặc khi thiếu trường **nghiêm trọng**.
**Chặn hồi quy:** `TC-AC3-02`, `TC-AC3-03`, và `TC-AC3-04` canh mặt trái (hồ sơ đã
cho đi tiếp thì không được thiếu trường bắt buộc). Mutation M4/M5 xác nhận.

---

## Phụ lục — lỗi trong chính bộ kiểm thử

Ghi lại để minh bạch: bốn lỗi dưới đây nằm ở **bộ đo**, không ở SUT, và chúng đã
làm con số báo cáo sai trước khi bị bắt. Chi tiết kỹ thuật ở `PROMPTS.md`.

| Mã | Lỗi | Hậu quả trước khi sửa | Tìm ra bằng |
|---|---|---|---|
| BD-01 | Mốc neo khớp mờ ở giữa dòng | Cắt đôi địa chỉ trên cả 15 ảnh CCCD; lấy `TUẦN` làm ngày sinh | thăm dò |
| BD-02 | Cắt rìa theo conf ở cả hai đầu | Xoá mất chính giá trị viết tay; 2 trường từ `SAI` thành `BO_SOT` | thăm dò |
| BD-03 | Đọc ô tích sai cả ba tầng | Nhận nhầm tiêu đề đơn là phương án; soi mực vào giấy trắng; so mực giữa cửa sổ khác cỡ | thăm dò |
| BD-04 | Mẫu số tỉ lệ tái duyệt tính trên 66 thay vì 105 trường | Báo cáo nói tái duyệt **25,8 %** trong khi số thật là **53,3 %** — tự khai giảm chi phí nhân sự hơn một nửa | rà lại số |
| BD-05 | `chuan_hoa.so()` vét chữ số **sau khi** đã có đơn vị: `'15 m2'` → **152** | Trường diện tích bị tính sai bất cứ khi nào OCR đọc `m²` thành `m2` — mà Tesseract đọc như thế rất thường xuyên (`'7 m2 mm -'`). Hiện chưa bung ra vì bộ tách bóc số trước, nhưng adapter khác cắm vào là dính ngay | **unit test `TC-LUAT-32`** |
| BD-06 | Canary hard-code `C:/Windows/Fonts/arial.ttf` | Canary vỡ trên Linux ⇒ bộ đo **dừng** và báo "lỗi hạ tầng" ở CI, dù model không sao | dựng CI |
| BD-07 | `doc_luot_hai()` cho khoá (ảnh, trường) trùng lặp, **dòng cuối thắng, im lặng** | Sổ gán nhãn bị thêm một khối 72 dòng cho cùng 18 ảnh, hai khối mâu thuẫn ở phần ghi chú, bộ đo vẫn chạy êm và chỉ lấy khối cuối. Nhãn là thước đo duy nhất — nó phải nổ chứ không được tự chọn hộ. Nay ném lỗi kèm danh sách khoá trùng | rà tính toàn vẹn dữ liệu |

BD-01 → BD-03 cộng lại đưa accuracy đo được từ 32,4 % lên 41,9 %. **Gần một phần
tư "lỗi của model" ban đầu thật ra là lỗi của người đo.**

Bốn lỗi đầu tìm ra bằng **kiểm thử thăm dò** — đọc từng dòng kết quả sai *trên ảnh
sạch nhất*, vì ảnh sạch mà sai thì gần như luôn là lỗi bộ đo. Nhưng BD-05 thì thăm
dò **không** bắt được: nó chỉ bung ra với dữ liệu mà bộ ảnh hiện tại chưa có. Nó bị
bắt vì có **unit test trực tiếp cho luật so khớp** — và đó là lý do `test_luat_so_khop.py`
tồn tại: 47 ca chạy trong 0,1 giây, kiểm *cái thước đo* chứ không kiểm *cái được đo*.
