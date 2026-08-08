# Phụ lục — phần không nằm trong 2 trang báo cáo

`BAO-CAO.md` là bài nộp theo đúng giới hạn 2 trang của đề. File này chứa phần chi tiết
đã bị cắt ra: bảng theo từng trường, luật so khớp đầy đủ, toàn bộ giả định, và danh
sách câu hỏi muốn gửi lại. Báo cáo do máy sinh (đầy đủ hơn nữa, 8 mục, sinh lại mỗi lần
chạy) nằm ở `ket_qua/tesseract/bao_cao.md`.

## A. Luật so khớp đầy đủ (Bước 1)

Ngoài 6 tình huống đề nêu, còn ba quyết định nữa mà đề không nói tới:

| Kiểu trường | Luật | Vì sao chọn thế |
|---|---|---|
| `tien` (thu nhập) | so trên **dãy chữ số**, bỏ dấu phân cách nghìn | `8.500.000` và `8500.000` là cùng một số tiền; dấu chấm là cách trình bày. Đổi lại `8.500.000` vs `8.500.00` bị tính sai — đúng ý muốn, vì đó là lệch một chữ số thật. |
| `so_luong` (diện tích) | so theo **giá trị số**, giữ phần thập phân | Ở đây dấu phẩy MANG thông tin: `18,5` ≠ `185`. Cùng một kiểu "số" nhưng luật ngược với tiền — đó là lý do luật phải gắn với ý nghĩa nghiệp vụ của trường, không gắn với kiểu dữ liệu. |
| `dia_chi` | khớp mờ ≥ **0,90** sau khi chuẩn hoá viết tắt hành chính | Trường tự do, dài. Đòi khớp tuyệt đối thì phép đo chỉ đo được độ dài chuỗi. Ngưỡng nằm trong `so_khop.py`, đổi được. |

Chuẩn hoá chỉ được xoá những khác biệt **không mang thông tin nghiệp vụ**: khoảng
trắng, hoa/thường, dấu câu, đơn vị, dấu phân cách nghìn. Dấu tiếng Việt trong tên người
thì không — nó phân biệt hai con người.

Một quan sát nhỏ nhưng đáng giá: ở lượt gán nhãn thứ hai, người đọc ghi diện tích của
`mau_01_nang_02` là `18.5 m²` trong khi nhãn theo cấu tạo là `18,5 m²`. Hai lượt vẫn
được tính là **khớp**, vì luật ở Bước 1 coi dấu thập phân `,`/`.` là tương đương. Nếu
Bước 1 chưa chốt luật này thì đó đã thành một ca "bất đồng giữa hai người gán nhãn" —
minh hoạ đúng ý của đề: **bước 1 quyết định bước 4 đo được cái gì**.

## B. Kết quả theo từng trường

Accuracy tính trên các trường mà người gán nhãn đọc được (không tính vùng xám):

| Trường | Mức | Đọc được | Đúng | Sai | Bỏ sót | Accuracy | Conf TB |
|---|---|---|---|---|---|---|---|
| `cccd.ngay_sinh` | trung bình | 13 | 11 | 1 | 1 | **84,6 %** | 0,90 |
| `cccd.noi_thuong_tru` | trung bình | 15 | 9 | 2 | 4 | 60,0 % | 0,92 |
| `cccd.so_dinh_danh` | **nghiêm trọng** | 15 | 8 | **0** | 7 | 53,3 % | 0,94 |
| `mau_01.hinh_thuc` | trung bình | 12 | 6 | 1 | 5 | 50,0 % | 0,95 |
| `mau_01.dien_tich_binh_quan` | trung bình | 11 | 3 | 3 | 5 | 27,3 % | 0,72 |
| `mau_01.thu_nhap_hang_thang` | trung bình | 12 | 3 | 3 | 6 | 25,0 % | 0,53 |
| `cccd.ho_ten` | **nghiêm trọng** | 15 | 3 | 6 | 6 | **20,0 %** | 0,90 |
| `mau_01.ho_ten_nguoi_viet_don` | **nghiêm trọng** | 12 | 1 | 6 | 5 | **8,3 %** | 0,70 |

Hai điều đáng chú ý ngoài con số:

- **`so_dinh_danh` gãy an toàn.** 15 trường: 8 đúng, 7 bỏ sót, **0 sai**. Trường nguy
  hiểm nhất lại là trường duy nhất không bao giờ trả giá trị sai — nó im lặng thay vì
  đoán. Với AC3 và với nghiệp vụ NƠXH, đây là kiểu gãy đúng.
- **`ho_ten` gãy nguy hiểm.** 6 sai, phần lớn là lỗi dấu, và conf trung bình vẫn 0,90.
  Đây là trường vừa nghiêm trọng nhất vừa có kiểu gãy tệ nhất.

**Phân loại toàn bộ lỗi** (trả lời "sai kiểu gì", không chỉ "sai bao nhiêu"):
`im_lang_tren_anh_doc_duoc` 39 · `sai_dau` 6 · `sai_vai_ky_tu` 4 · `sai_gia_tri_so` 3 ·
`sai_1_chu_so` 2 · `lech_qua_nguong` 2 · `thieu_hoac_thua_phan` 1 · `khong_phai_ngay` 1
· `sai_so_chu_so` 1 · `chon_sai_o` 1.

## C. Ba kiểu "model không trả gì" — trông giống nhau trong log

| Kiểu | Số ảnh | Nghĩa | Ai phải sửa |
|---|---|---|---|
| Từ chối theo chính sách | 7 | OCR ra quá ít chữ / conf quá thấp ⇒ cụm model chủ động im lặng | không ai — hành vi đúng theo AC3 |
| Đọc được chữ nhưng không neo được trường | 7 | OCR ra chữ, nhưng nhãn in bị đọc sai tới mức bộ tách không tìm được mốc neo nào | kỹ sư — sửa bộ tách hoặc cách gọi model |
| Lỗi hạ tầng | 0 | không gọi được model | kỹ sư — sửa trước khi tin bất kỳ con số nào |

Đề cảnh báo đúng chỗ này ("kết quả rỗng chưa chắc là lỗi model"). Cách chặn trong repo
này: một **canary** chạy trước mỗi lượt đo (render một dòng chữ sạch rồi bắt model đọc
lại); canary vỡ thì bộ đo **dừng**, không báo cáo 0 %.

## D. Vùng xám — 3 trường phép đo không kết luận được

| Ảnh | Trường | Vì sao |
|---|---|---|
| `cccd_nang_01` | `ngay_sinh` | dấu giáp lai đè đúng lên ô giá trị |
| `cccd_nang_03` | `ngay_sinh` | nhoè + thiếu sáng, không đọc ra chữ số nào |
| `mau_01_nang_03` | `dien_tich_binh_quan` | dấu giáp lai che kín giá trị |

Cả ba: người gán nhãn không đọc được **trường đó**, nhưng vẫn đọc được các trường khác
trên cùng ảnh. Đòi model trả đúng ở đây là đòi nó bịa; thưởng cho việc nó im lặng ở đây
lại làm đẹp con số AC3 một cách giả tạo. Nên chúng bị loại khỏi mọi phép tính và báo
riêng. Trong lần chạy này model im lặng ở cả ba — hành vi hợp lý, nhưng **không được
tính điểm**.

## E. Giả định (đề không nói, tôi tự quyết)

- **GĐ-1** Ngưỡng khớp mờ địa chỉ = 0,90.
- **GĐ-2** Trọng số nghiêm trọng ×3 / ×1,5 / ×1 do tôi đặt, không có căn cứ nghiệp vụ
  nào từ đề. Đây là chỗ tôi muốn nghe Ban QLDA quyết.
- **GĐ-3 — ĐÃ GỠ.** Bản đầu để 18/33 ảnh (bậc sạch/nhẹ/trung bình) không lấy mẫu lượt
  gán nhãn thứ hai, mặc định coi là người đọc được. Đó là chỗ hở nặng nhất của bộ nhãn,
  vì **chính bậc trung bình** sinh ra 18 ca `BO_SOT` + 6 ca `SAI`. Nếu những ảnh đó thật
  ra người cũng không đọc nổi thì 18 ca `BO_SOT` phải thành `TU_CHOI_DUNG` (mẫu số tụt
  105 → 87, `accuracy_truong_doc_duoc` nhảy **41,9 % → 50,6 %**) và 6 ca `SAI` phải thành
  `BIA` (khẳng định **"AC3 bịa 0 %" sập, thành 12,5 %**). Tức là con số headline đang treo
  trên một giả định chưa đo.
  **Đã xử lý:** lượt đọc lại thứ ba mở nốt 18 ảnh đó, ghi thành 72 dòng mới trong
  `data/nhan/doc_lai_doc_lap.csv` (thêm nhãn = thêm dòng dữ liệu, không sửa code).
  Kết quả **18/18 ảnh đọc được rõ toàn bộ trường** ⇒ giả định được **xác nhận**, mọi con
  số giữ nguyên. Nay lượt đọc lại phủ **33/33 ảnh**, `so_truong_so_sanh_duoc` 33 → 105,
  không còn ảnh nào mang kỳ vọng hành vi do script gán mặc định.
  Việc này làm lệch dấu vân tay bộ dữ liệu nên `test_khong_tut_so_voi_baseline` đỏ đúng
  như thiết kế; baseline đã được chốt lại (`scripts/chot_baseline.py`, 3 lượt, sigma 0,0).
- **GĐ-4** "Không đọc được" phán quyết ở mức **ảnh**, không ở mức trường; trường lẻ mà
  người không đọc được thì vào vùng xám thay vì thành `phai_tu_choi`.
- **GĐ-5** Chính sách từ chối của cụm model (< 8 từ hoặc conf ảnh < 30) là tham số của
  **model**, không phải của hệ thống. Nới ra sẽ đổi cả accuracy lẫn tỉ lệ bịa.
- **GĐ-6** Chữ "viết tay" trên Mẫu 01 là font Arial nghiêng + nhiễu hình học từng ký tự
  (các font viết tay có sẵn trên Windows thiếu glyph dấu tiếng Việt — đã kiểm bằng
  `fontTools`). Nó mô phỏng nét không đều và đường cơ sở gợn, **không** mô phỏng hình
  dạng chữ viết tay thật. Con số 8–27 % của **ba trường chữ viết tay** trên Mẫu 01 vì thế
  là **chặn trên lạc quan**: chữ viết tay thật gần như chắc chắn còn tệ hơn. (Trường thứ
  tư của Mẫu 01 — `hinh_thuc` — là **ô tích, không phải chữ viết tay**, đạt 50 %; đừng gộp
  nó vào dải 8–27 %.)
- **GĐ-7** AC3 nói hồ sơ "được đặt trạng thái cần bổ sung" nhưng không nói *khi nào*.
  Tôi chốt: cần bổ sung khi model từ chối, khi không trích được trường nào, hoặc khi
  thiếu bất kỳ trường **nghiêm trọng** nào. Thiếu một trường trung bình thì hồ sơ vẫn
  đi tiếp, trường đó được gắn cờ cho người duyệt điền tay. Luật này ở
  `bo_do/so_bang_chung.py::_trang_thai_ho_so`, đổi được, và có ca kiểm thử canh cả hai
  chiều (`TC-AC3-02` và `TC-AC3-04`).
- **GĐ-8** Đề không cấp quyền truy cập hệ thống, nên hợp đồng đầu ra AC1–AC3 được dựng
  thành một **bản hiện thực tham chiếu** (`bo_do/so_bang_chung.py`) rồi kiểm model
  against nó. Nó không phải hệ thống của AsiaPM. Rủi ro còn lại: hệ thống thật có thể
  đòi định dạng khác — nhưng ba thứ AC1 liệt kê (schema + confidence từng trường, liên
  kết ảnh gốc, nhật ký worker) thì model phải sản xuất được bất kể định dạng nào.

## F. Nếu đây là việc thật, tôi sẽ hỏi lại

1. Ngưỡng conf trong AC2 đang là bao nhiêu trong hệ thống thật, và ai được quyền đổi?
   Bảng quét ngưỡng ở mục 3 của báo cáo vô nghĩa nếu con số đó bị hard-code.
2. Sai một dấu trong `ho_ten` mà hồ sơ vẫn được duyệt thì hậu quả pháp lý tới đâu? Câu
   trả lời quyết định `ho_ten` nên nặng ×3 hay phải là điều kiện chặn cứng.
3. Đã có API đối chiếu CSDL quốc gia về dân cư chưa? Nếu có, phần lớn lỗi dấu ở trên
   biến thành lỗi vô hại và bài toán đổi hẳn.
4. Người dân nộp hồ sơ qua kênh nào — app có kiểm chất lượng ảnh tại chỗ, hay ảnh gửi
   qua email/Zalo? Điều kiện (2) trong kết luận chỉ khả thi ở kênh thứ nhất.
5. Có ảnh thật (đã che dữ liệu cá nhân, có thoả thuận xử lý dữ liệu) để hiệu chuẩn lại
   bộ ảnh mô phỏng không? Đây là thứ duy nhất phá được giới hạn lớn nhất của bài này.
6. Mẫu 01 bắt buộc phải viết tay, hay có bản khai điện tử? Nếu có bản điện tử thì phần
   khó nhất của bài toán biến mất mà không cần model nào tốt hơn.

## G. Giới hạn — bản đầy đủ

- **Dữ liệu là giấy tờ mô phỏng.** Bố cục do tôi vẽ, phông chữ Arial, hoa văn nền là
  các đường chéo. CCCD thật có hoa văn bảo an, mực in khác, thẻ ép plastic phản sáng
  khác. Con số **41,9 % nói về bộ ảnh này**, không suy trực tiếp ra giấy tờ thật — nó
  dùng để *so sánh giữa các model trên cùng bộ ảnh*, và đó là mục đích chính của bộ đo.
- **n = 33 quá nhỏ để nói về từng trường.** `cccd.ngay_sinh` = 84,6 % dựa trên 13 mẫu;
  khoảng tin cậy 95 % rộng cỡ ±20 điểm phần trăm. Bảng mục B là để chỉ *hướng* điều
  tra, không phải để cam kết SLA.
- **Cái được đo là cụm "OCR + bộ tách", không phải Tesseract trần.** Một bộ tách khác
  cho số khác. Ba lỗi của bộ tách đã bị bắt trong quá trình làm và chúng đưa con số từ
  32,4 % lên 41,9 % (chi tiết ở `PROMPTS.md` mục 2) — gần một phần tư "lỗi của model"
  ban đầu hoá ra là lỗi của người đo. Không có gì bảo đảm đã hết lỗi loại đó.
- **Dấu thanh ở bậc trung_binh nằm ở ranh giới đọc được của NGƯỜI.** Lượt đọc lại đọc
  được chữ nhưng không nhìn rõ dấu ngã/huyền trên 3 ảnh CCCD bậc đó, phải suy từ ngữ
  cảnh. Hệ quả: một phần lỗi `sai_dau` của model ở bậc trung_binh có thể là do **thông
  tin không còn trong ảnh**, không phải do model kém. Muốn tách bạch thì phải có ảnh
  gốc độ phân giải cao làm đối chứng — bộ này chưa có.
- **Lượt gán nhãn thứ hai không độc lập hoàn toàn.** Người đọc lại có biết bộ ảnh được
  sinh ra thế nào, nên `ty_le_khop = 100 %` là **chặn trên**, không phải số đo sạch.
  Phần đáng tin của lượt đó là phán quyết *đọc được / không đọc được*, vì phán quyết
  này không suy ra được từ bản kê.
- **Mức hồ sơ đã đo được, nhưng dựa trên một định nghĩa tôi tự đặt.** Chỉ số
  `ty_le_day_ve_oan` = 44,4 % (LOI-10) dựa vào GĐ-7 — quy ước "khi nào hồ sơ cần bổ
  sung". Đề không định nghĩa "hồ sơ đạt", nên đổi GĐ-7 là đổi con số này. Nếu Ban QLDA
  cho phép người duyệt nhập tay trường bắt buộc bị thiếu thì 4/12 ca biến mất ngay.
- **Không đo được tác động dây chuyền.** Một hồ sơ bị trả về làm dân đi lại một lần —
  bộ đo đếm được số hồ sơ, không đếm được chi phí thật (thời gian, chi phí đi lại, tỉ lệ
  bỏ giữa cuộc). Muốn con số đó thì cần dữ liệu vận hành, không phải bộ ảnh kiểm thử.

## H. Bảng quét ngưỡng HITL và kết quả kiểm thử đột biến

**Quét ngưỡng.** Mẫu số là **105 điểm kiểm phải có giá trị trong hồ sơ**, không phải 66
điểm kiểm model chịu trả lời: điểm kiểm model im lặng cũng về tay người duyệt y như điểm
kiểm bị gắn cờ. Bản đầu của bộ đo chia cho 66 và báo tái duyệt 25,8 % — sai một nửa
(lỗi BD-04).

| Ngưỡng | Tự động qua cổng | Tỉ lệ tự động | Tái duyệt | Rò rỉ | Rò rỉ nghiêm trọng |
|---|---|---|---|---|---|
| 0,50 | 63/105 | 60,0 % | 40,0 % | 20 | 12 |
| 0,70 | 54/105 | 51,4 % | 48,6 % | 15 | 8 |
| **0,80** *(đang dùng)* | 49/105 | 46,7 % | 53,3 % | 11 | **6** |
| 0,90 | 42/105 | 40,0 % | 60,0 % | 7 | 4 |
| **0,95** *(khuyến nghị)* | 28/105 | 26,7 % | **73,3 %** | 1 | **0** |
| 1,00 | 0/105 | 0 % | 100 % | 0 | 0 |

Rò rỉ duy nhất còn lại ở ngưỡng 0,95 là `mau_01_trung_binh_01.hinh_thuc` — chọn sai ô,
conf 0,95 vì luật đếm mực bị chặn trên đúng bằng ngưỡng (LOI-02).

**Kiểm thử đột biến** (`scripts/kiem_tra_bo_test.py`, ~7 phút): gài 8 lỗi có chủ ý vào
một bản sao mã nguồn trong thư mục tạm rồi chạy lại ca kiểm thử tương ứng.

| Mã | Lỗi gài vào | Ca phải đỏ | Kết quả |
|---|---|---|---|
| M1 | Cổng HITL dùng `<=` thay vì `<` | TC-AC2-03 | bị bắt |
| M2 | Cổng HITL ngừng gắn cờ hoàn toàn | TC-AC2-01 | bị bắt |
| M3 | Sổ bằng chứng ghi sai băm ảnh gốc | TC-AC1-04 | bị bắt |
| M4 | Ảnh không đọc được vẫn "đủ điều kiện xử lý" | TC-AC3-02 | bị bắt |
| M5 | Hồ sơ cần bổ sung không kèm lý do | TC-AC3-03 | bị bắt |
| M6 | Bỏ chính sách từ chối | TC-AC3-01 | **sống sót** |
| M7 | Trường mất điểm tin cậy | TC-AC1-02 | bị bắt |
| M8 | Bộ tách lấy dòng OCR đầu tiên làm giá trị | TC-AC3-01 | bị bắt |

**M6 sống sót — đã truy nguyên, và nó là kết quả đáng giá nhất của cả lượt này.** Bỏ
chính sách từ chối **không** sinh ra hành vi bịa, vì cụm model còn một lớp phòng vệ thứ
hai: bộ tách chỉ trả giá trị khi khớp được mốc neo, mà trên 6 ảnh không đọc được thì OCR
ra toàn rác (`'0—_“————a“"e—*m | ¬'`) nên không mốc neo nào khớp. Hai kết luận:

1. **Về SUT:** hành vi "không bịa" mạnh hơn con số 0 % gợi ý — nó không phụ thuộc vào
   một tham số ngưỡng duy nhất, mà có hai cơ chế độc lập cùng chặn.
2. **Về bộ test:** M6 không tạo được lỗi cần bắt, nên nó **không chứng minh gì** về
   `TC-AC3-01`. Ca đó chỉ được chứng minh sau khi thêm **M8** — gài đúng kiểu bug thật
   (lập trình viên thêm nhánh "cố gắng hết sức" cho đỡ trả về rỗng), và M8 bị bắt.

Một mutation sống sót mà không truy nguyên là một lỗ hổng chưa biết trong bộ kiểm thử.
Script phân biệt hai trạng thái này và chỉ trả exit code 1 khi có lỗ hổng **chưa** giải
thích được.
