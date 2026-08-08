# Báo cáo kiểm thử — US-M1-EXTRACT-001 (mô hình trích xuất giấy tờ)

**SUT:** Tesseract 5.4 `lang=vie` + bộ tách trường neo theo nhãn in + chính sách từ chối.
**Dữ liệu:** 33 ảnh mô phỏng (18 CCCD, 15 Mẫu 01) = 132 điểm kiểm. **Tái hiện:**
`python scripts/do_luong.py` (~36 s). *Kế hoạch + ma trận truy vết AC:
`KE-HOACH-KIEM-THU.md` · Lỗi: `LOI-PHAT-HIEN.md` · Chi tiết: `PHU-LUC.md`*

## 1. "Đúng" nghĩa là gì (Bước 1)

| Nhãn → model trả | | Vì sao |
|---|---|---|
| TRẦN THỊ MAI → Trần Thị Mai | **ĐÚNG** | hoa/thường là cách trình bày |
| → TRAN THI MAI · TRÀN THỊ MAI | **SAI** | mất dấu hay sai dấu đều là tên người khác |
| 01/03/1990 → 1/3/1990 | **ĐÚNG** | chuẩn hoá về ISO rồi so |
| 000301001234 → 000301001284 | **SAI** | không khớp mờ: lệch 1 chữ số là hồ sơ người khác |
| 15 m² → 15 | **ĐÚNG** | đơn vị do schema quy định |

Bất đối xứng nghiêm trọng xử lý bằng **trọng số** (`so_dinh_danh`, `ho_ten` ×3). Vì AC3,
phán quyết có **6 giá trị**: `DUNG`, `SAI`, `BO_SOT`, `TU_CHOI_DUNG` (im lặng trên ảnh
không đọc được — **đúng**), `BIA` (**vi phạm AC3**), `LOI_HE_THONG` (không tính điểm).
**Nhãn:** giá trị theo cấu tạo; *kỳ vọng hành vi* từ lượt **đọc lại 33/33 ảnh** — chỉ
lượt này có quyền phán "ảnh không đọc được"; đồng thuận **105/105**. Nói thẳng: annotator
#2 là **một mô hình ngôn ngữ trong cùng phiên**, nên 105/105 là **chặn trên**, không phải
bằng chứng nhãn đúng (GH-04, đang mở — số sạch cần hai người gán nhãn mù + kappa). Ba
điểm kiểm vào **vùng xám** (giáp lai đè kín ô giá trị) bị loại khỏi mọi con số. Lượt đọc
lại cũng làm nhẹ bớt LOI-01: 3 ảnh CCCD bậc trung bình đọc ra *chữ* nhưng **không rõ dấu
thanh**, nên quy toàn bộ lỗi dấu cho model là chưa công bằng.

## 2. Bao phủ đặc tả và kết quả

**296 ca tự động** (+8 đột biến), không ca nào chạy tay: 38 Gherkin · 47 unit test cho
*thước đo* · 15 đặc tả AC · 13 fitness kiến trúc · 11 đường lỗi adapter · 134 dữ liệu (mỗi
ảnh × trường một ca) · 10 hồi quy · 28 nghiệm thu bài nộp.
**Bao phủ AC: 14/15**, toàn bộ ĐẠT; điều khoản còn lại — *"hiển thị nổi bật cho người
duyệt"* — **không kiểm được** vì giao diện ngoài phạm vi, ghi rõ chứ không bỏ quên.

| Chỉ số | | | Bậc chất lượng ảnh | Điểm tin cậy |
|---|---|---|---|---|
| Điểm tin cậy (có trọng số) | **49,4 %** | | sạch · nhẹ | 66,7 % |
| Điểm kiểm ĐẠT (không trọng số) | 68/129 | | trung bình | **10,3 %** |
| Đúng / trường nghiêm trọng | **28,6 %** | | nặng | **0 %** |
| AC3 — từ chối đúng (24 điểm kiểm) | **100 %** | | không đọc được | 100 % *(đúng)* |
| AC3 — **bịa dữ liệu** | **0 %** | | *lỗi hạ tầng* | *0* |

Gãy **có một vách**: từ bậc trung bình trở đi model gần như ngừng hoạt động. Chữ viết
tay 8–27 %, chữ in 20–85 %.

**Ở mức hồ sơ con số đổi nghĩa** — người dân không cảm nhận accuracy theo trường: trong 27
hồ sơ đọc được chỉ **15 (55,6 %) đi tiếp**, **12 (44,4 %) bị trả về** — 6 vì bộ tách không
neo được trường nào, 4 vì thiếu trường bắt buộc, 2 vì từ chối oan. "41,9 % trường đúng"
nghĩa là gần một nửa người dân bị gọi quay lại xã.

## 3. Lỗi — 3 Nghiêm trọng, 3 Nặng, 1 Trung bình (`LOI-PHAT-HIEN.md`)

| Mã | Lỗi | Mức |
|---|---|---|
| **LOI-01** | Sai dấu họ tên với conf **0,85–0,94** ⇒ lọt cổng HITL: `TRẦN`→`TRẤN`, `NGUYỄN`→`NGUYÊN`, `TUẤN`→`TUẦN`, `PHẠM`→`PHAM`, 2 ca mất một phần tên. **6/6 rò rỉ nghiêm trọng đều là họ tên, 4/6 trên ảnh sạch** ⇒ siết chất lượng ảnh không vá được. Model tự tin nhất đúng ở chỗ nó sai nguy hiểm nhất. | **Nghiêm trọng** |
| **LOI-02** | Conf trường ô tích là **hằng số 0,95** trên cả 7 ca (độ lệch chuẩn 0) — hằng số đội lốt điểm tin cậy; cổng HITL không lọc được gì, đã có 1 ca tick sai ô lọt qua | **Nghiêm trọng** |
| **LOI-10** | **44 % hồ sơ người đọc được vẫn bị trả về** bắt dân nộp lại | **Nghiêm trọng** |
| LOI-03/04/05 | Sập từ bậc ảnh trung bình · conf hiệu chuẩn kém (ECE 0,183; khoảng 0,70–0,80 tự báo 0,76 nhưng đúng **0,20**) · sai giá trị số trên chữ viết tay (`11.000.000`→`17,000,000`, `18,5`→`18`) | Nặng |
| LOI-06 | 7 ảnh: OCR ra chữ nhưng bộ tách không neo được trường nào | Trung bình |
| LOI-07/08/09 | Đầu ra thiếu liên kết ảnh gốc, cờ HITL, trạng thái hồ sơ ⇒ **vi phạm AC1/AC2/AC3** — do viết ca kiểm thử theo đặc tả tìm ra | **đã sửa** |
| BD-01…08 | 8 lỗi trong **chính bộ đo**: `'15 m2'` → **152** (unit test bắt), canary hard-code font Windows (CI lộ), sổ nhãn trùng khoá bị nuốt im lặng, cổng đếm trang đo bản render khác bản nộp | **đã sửa** |

Quét ngưỡng (bảng đầy đủ `PHU-LUC.md` §H): ở **0,80** có 6 rò rỉ nghiêm trọng và 46,7 %
điểm kiểm tự động qua cổng; phải lên **0,95** mới hết rò rỉ nghiêm trọng, khi đó chỉ còn
**26,7 %** tự động. Mẫu số là 105 điểm kiểm phải có giá trị — model im lặng cũng về tay
người duyệt y như điểm kiểm bị gắn cờ.

## 4. Kết luận: **KHÔNG ĐẠT — chưa dùng được**

`test_cong_chat_luong_tuyet_doi` đang đỏ, và đó là kết luận chứ không phải test hỏng.
Dùng được **nếu đủ cả bốn**: (1) **ngưỡng ≥ 0,95**, họ tên + số định danh + hình thức luôn
qua người bất kể conf — cái giá là chỉ **26,7 %** điểm kiểm được tự động, nên phải trả lời
*27 % có đủ hoàn vốn không* trước khi bàn kỹ thuật; (2) **chặn ảnh ở cửa vào, không ở cửa
ra** (việc của UI nộp hồ sơ); (3) **chỉ dùng cho CCCD**; (4) **đối chiếu chéo họ tên + số
định danh với CSDL quốc gia về dân cư** — lỗi dấu khôi phục được bằng đối chiếu, không
bằng OCR tốt hơn.

**Điểm mạnh thật:** cụm này **không bịa** — 0/24 điểm kiểm trên ảnh không đọc được, và
kiểm thử đột biến cho thấy hành vi đó có **hai lớp phòng vệ độc lập**. `so_dinh_danh` không
một lần trả sai (8 đúng, 7 bỏ sót, **0 sai**). Rủi ro của nó là **im lặng quá mức** ⇒ đội
chi phí nhân sự, không phải đưa dữ liệu sai vào hồ sơ.

## 5. Phép đo này không chứng minh được gì

**11 giới hạn được khai thành DỮ LIỆU** (`gioi_han/so_gioi_han.json`), mỗi cái nêu rõ nó
chặn chỉ số nào, **cần bằng chứng gì để gỡ**, và hậu quả nếu bỏ qua. Ba cái nặng nhất:
giấy tờ **mô phỏng** nên 41,9 % chỉ dùng để so các model trên *cùng bộ ảnh này*; **n = 33**
quá nhỏ để kết luận theo từng trường (±20 điểm phần trăm);
**cái được đo là cụm OCR + bộ tách của tôi, không phải Tesseract** —
8 lỗi của chính bộ đo đã bị bắt, 3 trong số đó đưa
con số từ 32,4 % lên 41,9 %, tức gần một phần tư "lỗi của model" ban đầu là lỗi của người
đo. Bộ đo cũng **không đo được chi phí thật** của việc hồ sơ bị trả về, nên *"27 % tự động
có đủ hoàn vốn không"* là câu tôi nêu ra chứ không phải câu tôi trả lời được.

Giới hạn **không** nằm dưới dạng đoạn văn cuối báo cáo — chỗ dễ viết cho có rồi quên.
`features/03-gioi-han-phep-do.feature` canh chúng như canh hành vi: công bố chỉ số mà quên
khai giới hạn ⇒ ĐỎ; khai mà không nói cần bằng chứng gì để gỡ ⇒ ĐỎ; tuyên bố đã gỡ mà
không dẫn được bằng chứng ⇒ ĐỎ. Cổng vừa bắt một lỗ hổng thật: công bố ECE 0,183 và AUC
0,839 mà sổ giới hạn chưa phủ chỉ số hiệu chuẩn (nay là GH-11). GH-10 thì đã được **gỡ**
đúng cách — 33/33 ảnh nay đều đã đọc lại, con số không đổi.

Bộ đo còn bị kiểm ngược ba lớp: **47 unit test cho luật so khớp** (bắt BD-05: `'15 m2'` →
152, lỗi thăm dò không bắt nổi); **8 mutation** ⇒ 7 bị bắt, 1 sống sót đã truy nguyên; và
**CI Ubuntu** — dựng CI mới làm lộ BD-06. Cổng hồi quy **ba tầng**: bất biến / biên độ
`max(3·sigma, 0,05)`, sigma **đo được** = 0,0000 / ca cụ thể gọi tên ảnh + trường. 61 điểm
kiểm hỏng gắn mã lỗi + `xfail(strict)` nên bộ test **chỉ đỏ khi hành vi đổi**. Thử ngược
`lang=eng` ⇒ 21 điểm kiểm ĐẠT → KHÔNG ĐẠT.

---

# Trả lời câu hỏi cuối (mục 05)

**Không đồng ý với "Model B tốt hơn hẳn, chốt dùng B."** Hướng có thể đúng, nhưng bảng
đó không đỡ nổi chữ "hẳn", càng không đỡ chữ "chốt".

**Bằng chứng mỏng tới đâu.** Mỗi ô là **một lần chạy trên một ảnh**: "đúng 5/5" không
phải một tỉ lệ, nó là một lần bốc thăm. Không có lần lặp ⇒ **không biết sigma** ⇒ không
tách được model khỏi nhiễu. Ô "B / CCCD ảnh sạch" còn ghi *chưa đo*, nên kết luận dựa
trên 2 điều kiện so với 3 — thiếu đúng điều kiện phổ biến nhất ngoài đời. Và chưa thấy
nhắc tới **nhãn**: ai quyết "đúng 3/3"? Quyết bằng mắt, không luật viết ra, thì hai
người chấm cùng bảng này ra hai kết quả.

**Cần thêm gì.** ≥ 30 ảnh **có nhãn cho mỗi ô**, điền cả ô đang trống; luật "đúng là gì"
viết thành script **trước** khi chạy; chạy **k ≥ 5 lần**/cấu hình, báo trung vị và sigma;
tách **lỗi gọi model** khỏi **model đọc không ra** bằng nguyên văn output + tham số gọi
+ canary mỗi lượt; thời gian báo **p50/p95**; kiểm **hiệu chuẩn conf**, vì hệ thống ở
mục 01 lọc bằng conf; kiểm AC3 riêng — model nào bịa thì loại thẳng.

**Chỗ bất thường.** *Một:* Model A, cùng CCCD, sạch 11,2 s → nhiễu **46,5 s**, gấp **4,15
lần** — cùng model, cùng máy, đó là dấu hiệu của **một đường thực thi khác** (ảnh nhiễu độ
phân giải lớn hơn hẳn, retry/timeout im lặng, nhánh dự phòng, hay bị tráo CPU), không phải
"khó hơn nên chậm hơn". Truy: chạy lại đúng hai ảnh đó 10 lần, log mốc thời gian **từng
giai đoạn** (đọc ảnh → tiền xử lý → suy luận → hậu xử lý) kèm cỡ ảnh sau tiền xử lý.
Không lặp lại ⇒ nhiễu môi trường; lặp lại ⇒ gần như chắc là tiền xử lý hoặc cỡ ảnh, tức
**lỗi ở cách gọi model**. *Hai:* A **"trả về rỗng"** trên Mẫu 01 — rỗng có hai nghĩa trái
ngược: model đọc không ra (theo AC3 là **đúng**), hay lời gọi bị lỗi. Một cái là điểm cộng
cho A, cái kia là bug của kỹ sư, mà bảng ghi chung một chữ. Repo này gặp đúng tình huống
đó nên phải tách ba cột: *từ chối theo chính sách* (7 ảnh), *đọc ra chữ nhưng không neo
được trường* (7 ảnh), *lỗi hạ tầng* (0 ảnh).

**Kết luận tôi sẽ viết thay:** "B tốt hơn A ở 2/3 điều kiện, mỗi điều kiện 1 ảnh. Chính
B chạy Mẫu 01 mất 93,2 s — gấp 6,4 lần khi chạy CCCD — nên phải tính lại chi phí ở mức
vài nghìn hồ sơ. **Chưa đủ căn cứ để chọn.**"
