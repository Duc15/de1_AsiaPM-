# Prompt đã dùng với AI, và những chỗ AI viết sai phải sửa

Toàn bộ repo này viết bằng **Claude Code (Claude Opus 5)** trong một phiên làm
việc, có người ngồi lái. Đề cho phép dùng AI và yêu cầu nộp kèm prompt cùng phần
AI làm sai — dưới đây là cả hai.

## 1. Prompt đã dùng

Không có một prompt dài duy nhất. Việc chia thành các lượt, mỗi lượt một mảnh
kiểm chứng được ngay:

**Lượt 1 — khung đo và luật "đúng là gì" (Bước 1)**
> Đọc `de-bai-tuyen-kiem-thu-bai1.txt`. Làm đề 1, dùng Tesseract làm model.
> Trước khi viết bất cứ gì khác, dựng `bo_do/schema.py` + `bo_do/so_khop.py`:
> khai báo trường của CCCD và Mẫu 01, mức nghiêm trọng từng trường, và luật so
> khớp cho từng kiểu dữ liệu. Trả lời dứt khoát 6 tình huống trong bảng ở Bước 1
> của đề, mỗi quyết định kèm lý do trong comment. Chú ý AC3: ảnh không đọc được
> thì hành vi đúng là KHÔNG trả giá trị — phán quyết phải phân biệt được
> "sai", "bỏ sót", "từ chối đúng", "bịa" và "lỗi hạ tầng".

**Lượt 2 — sinh dữ liệu (Bước 2)**
> Viết `scripts/sinh_du_lieu.py` sinh ≥30 ảnh phủ cả hai loại giấy tờ, 5 bậc chất
> lượng từ sạch tới không đọc nổi. Mô phỏng đúng bối cảnh đề nêu: chụp điện thoại
> trong sảnh UBND xã, tay run, đèn huỳnh quang, dấu giáp lai đè lên chữ. Tất định
> theo seed. Không dùng số định danh thật của ai — dùng tiền tố 000 vì đó không
> phải mã tỉnh hợp lệ. Ghi bản kê: ảnh nào, seed nào, làm xấu bằng những phép nào.

**Lượt 3 — gán nhãn và tự vặn lại chất lượng nhãn (Bước 3)**
> Nhãn giá trị lấy theo cấu tạo (script biết nó vẽ gì). Nhưng phán quyết
> "đọc được / không đọc được" thì không được lấy từ bản kê — phải là người mở ảnh
> ra đọc. Mở từng ảnh bậc `nang` và `khong_doc_duoc`, đọc bằng mắt, ghi vào
> `doc_lai_doc_lap.csv` đọc được gì. Rồi tính độ đồng thuận giữa hai lượt bằng
> ĐÚNG luật so khớp của Bước 1, và viết rõ giới hạn của phép đo đồng thuận đó.

*Nói rõ chỗ này vì nó là chỗ dễ đọc nhầm nhất: lượt đọc lại rốt cuộc do **chính
AI** mở ảnh ra đọc, không phải một người thứ hai. Nên đồng thuận 105/105 là chặn
trên chứ không phải bằng chứng nhãn đúng — giới hạn đó là **GH-04**, đang mở.*

**Lượt 4 — bộ đo (Bước 4)**
> Viết adapter Tesseract + bộ tách trường neo theo nhãn in, và bộ chấm điểm.
> Báo cáo phải trả lời được cho người không đọc code: sai Ở ĐÂU (loại giấy tờ,
> trường, bậc ảnh, kiểu sai), có tuân AC3 không, và điểm tin cậy model tự báo có
> ăn khớp với đúng/sai thật không. Thêm canary chạy trước mỗi lượt đo, và tách
> "lỗi gọi model" khỏi "model đọc không ra" — đề cảnh báo đúng chỗ này.

**Lượt 5 — test tự động (Bước 5)**
> Bắc cầu giữa "test cần đạt/không đạt" và "model cho con số dao động". Đừng đoán
> sigma — chạy `--lap 3` đo thật rồi chốt vào baseline. Baseline phải gắn dấu vân
> tay bộ dữ liệu để không so nhầm hai bộ khác nhau.

**Lượt 6 — soát lại chính bộ đo**
> Xem danh sách trường SAI trên ảnh bậc `sach` và `nhe`. Với mỗi dòng, trả lời:
> đây là Tesseract đọc sai thật, hay bộ tách của mình sai? Cái nào của bộ tách
> thì sửa. Đừng tinh chỉnh riêng cho bộ ảnh này.

## 2. AI viết sai ở đâu — sáu chỗ, có ba chỗ làm lệch hẳn con số

### (a) Bộ khớp mốc neo quét cả dòng → đi lấy giá trị của trường khác
Bản đầu khớp mờ mốc neo ở **bất kỳ vị trí nào** trong dòng. Hậu quả thật:

- `"Họ và tên:"` khớp mờ được với đoạn `"...Thành phố Hà Nội"` ở giữa dòng địa
  chỉ thứ hai → bộ tách coi dòng đó là dòng họ tên, nên **không** vét dòng 2 vào
  `noi_thuong_tru`. Mọi địa chỉ đều bị cắt một nửa và tính SAI.
- `"Ngày sinh:"` khớp mờ vào dòng `"Họ và tên: HOÀNG MINH TUẦN"` → `ngay_sinh`
  của `cccd_nhe_02` nhận giá trị `"TUẦN"`.

Sửa: mốc neo phải bắt đầu trong 8 ký tự đầu dòng (`_LECH_DAU_DONG_TOI_DA`), và
chọn dòng khớp **tốt nhất** thay vì dòng khớp đầu tiên.

Lượt sửa này (mốc neo + hậu xử lý giá trị theo kiểu trường + chốt luật so khớp
tiền theo dãy chữ số) đưa accuracy trên trường người đọc được từ **32,4% lên
39,1%**; sửa tiếp hai lỗi (b) và (c) thì lên **41,9%**. Không tách được riêng
phần đóng góp của từng sửa mà không chạy lại từng phiên bản, nên không quy con số
cụ thể cho từng lỗi — nhưng riêng lỗi mốc neo thì đếm được: nó cắt đôi địa chỉ
trên **cả 15 ảnh CCCD** người đọc được và làm hỏng thêm một trường `ngay_sinh`.

### (b) Cắt rìa theo confidence, cắt luôn cả giá trị
Để bỏ rác từ dòng kẻ chấm của biểu in sẵn (`"mm"`, `"—¬"`, `"_—X"`), AI viết hàm
cắt các từ conf thấp ở **hai đầu**. Nhưng chữ viết tay chính là phần conf thấp
nhất của dòng, nên hàm đó xoá luôn giá trị: hai trường `thu_nhap_hang_thang` từ
`SAI` thành `BO_SOT` — bộ đo tự tạo ra lỗi rồi ghi vào sổ của model. Sửa: chỉ cắt
ở đuôi. Ghi lại nguyên nhân trong docstring của `_cat_ria_conf_thap`.

### (c) Đọc ô tích chọn sai cả ba tầng
1. Nhận nhầm **tiêu đề đơn** `"ĐƠN ĐĂNG KÝ MUA, THUÊ, THUÊ MUA"` là một phương án
   → sửa: chỉ xét vài dòng ngay sau mốc neo `"Hình thức đăng ký:"`, và bỏ dòng dài.
2. Soi mực ở vùng **bên trái từ đầu tiên của dòng** — chỗ đó là giấy trắng, vì
   Tesseract đọc chính ô vuông thành một "từ" (`"[ ]"`, `"5D"`, `"[LI"`) nên từ đầu
   tiên **đã là** cái ô. Cả ba ô đều ra mật độ mực 0.000. Sửa: dùng hộp của từ rác
   đó làm vùng soi.
3. So mật độ mực giữa ba ô có **cửa sổ khác cỡ nhau** (31 vs 48 vs 57 px) → chênh
   lệch còn 0,002, dưới ngưỡng, nên trả về "không biết" trên đúng những ảnh sạch.
   Sửa: chuẩn hoá cửa sổ về cùng một cỡ, lấy trung vị hoành độ ô làm chuẩn (ba ô
   trên biểu in thẳng cột).

Sau ba sửa này: `hinh_thuc` đúng **7/7** ảnh mà OCR còn neo được, và từ chối đúng
trên 5 ảnh xấu còn lại.

### (d) Chọn font viết tay không có dấu tiếng Việt
AI đề xuất `Inkfree.ttf` / `segoepr.ttf` cho phần chữ viết tay. Kiểm bằng
`fontTools` thì cả hai **thiếu glyph** cho `ầ ặ ễ ộ ử ỳ đ ơ ư` — nếu cứ dùng, ảnh
sinh ra sẽ mất dấu, tức là **nhãn không khớp với chữ trên ảnh**, và toàn bộ phép
đo dấu tiếng Việt trở thành vô nghĩa mà không có dấu hiệu gì. Bắt được trước khi
sinh dữ liệu. Đổi sang Arial nghiêng + nhiễu hình học từng ký tự, và ghi rõ đó là
mô phỏng nét viết chứ không phải hình dạng chữ viết tay thật.

### (e) Hai lỗi API nhỏ
- Vẽ chữ viết tay bằng cách chọc vào thuộc tính riêng `ImageDraw._image`. Chạy
  được, nhưng là API nội bộ của Pillow. Sửa: truyền ảnh vào tham số.
- Dùng `ImageFilter.Kernel` để làm nhoè chuyển động — Pillow chỉ nhận kernel 3×3
  và 5×5, không đủ dài cho vệt tay run. Sửa: cộng nhiều bản dịch chuyển bằng numpy.

### (f) Confidence 1.0 từ một luật đếm mực
Luật đọc ô tích trả `confidence = 1.0` khi chênh lệch mực lớn. Một luật đếm pixel
không có quyền báo chắc chắn 100%, nhất là khi con số đó đi vào bảng hiệu chuẩn
và bảng ngưỡng HITL. Chặn trên 0,95.

## 3. Rút ra

Ba lỗi (a), (b), (c) đều **không làm chương trình gãy** — chúng chỉ làm con số
xấu đi và trông vẫn hợp lý. Nếu chỉ đọc `accuracy = 32%` rồi kết luận "Tesseract
kém với tiếng Việt" thì kết luận đó đúng một phần vì lý do sai.

Cái chặn được cả ba không phải review code, mà là ép bộ đo phải **in ra từng
trường sai kèm nhãn và giá trị model trả về**, rồi đọc bằng mắt từng dòng trên
những ảnh *sạch nhất*. Ảnh sạch mà sai thì gần như luôn là lỗi của bộ đo. Đó là
lý do `ket_qua/*/cham_diem.json` giữ nguyên mảng `chi_tiet` của cả 132 trường,
và là lý do có canary chạy trước mỗi lượt đo.
