# language: vi
#
# Nguồn: US-M1-EXTRACT-001, mục 02 của đề. AC1/AC2/AC3 vốn đã viết bằng
# Given/When/Then, nên chúng được chép gần như nguyên văn xuống đây — truy vết
# từ đặc tả tới ca kiểm thử là nhìn thấy được, không phải tra bảng.
#
# Đối tượng dưới quyền là lớp `doi_tuong/ho_so_giay_to.py`. Các bước dưới đây
# KHÔNG nhắc tới Tesseract; đổi model không phải sửa file này.

@dac-ta @ac
Tính năng: Trích xuất OCR/KIE vào schema chuẩn kèm điểm tin cậy

  Là nhân viên xử lý hồ sơ của Ban QLDA, tôi muốn hệ thống tự đọc ảnh giấy tờ và
  điền vào biểu chuẩn kèm điểm tin cậy từng trường, để tôi chỉ phải kiểm chỗ máy
  không chắc thay vì gõ lại toàn bộ hồ sơ.

  Bối cảnh:
    Cho hạ tầng trích xuất đã qua canary

  @ac1 @happy-path
  Kịch bản: AC1 — ảnh hợp lệ thì trường vào schema chuẩn kèm điểm tin cậy
    Cho một ảnh giấy tờ hợp lệ, đọc được "cccd_sach_01"
    Khi worker trích xuất chạy
    Thì mọi trường trả về phải thuộc schema chuẩn của loại giấy tờ đó
    Và mỗi trường phải kèm một điểm tin cậy trong khoảng 0 đến 1
    Và nguồn của mỗi trường phải thuộc tập đặc tả cho phép
    Và ảnh gốc phải được liên kết trong sổ bằng chứng
    Và nhật ký worker phải được ghi

  @ac2 @edge
  Kịch bản: AC2 — trường dưới ngưỡng bị đánh dấu cần người xác nhận
    Cho một ảnh giấy tờ hợp lệ, đọc được "cccd_sach_02"
    Và ngưỡng tin cậy cấu hình là 0.90
    Khi worker trích xuất chạy
    Thì mọi trường có điểm tin cậy dưới ngưỡng phải bị đánh dấu cần người xác nhận
    Và không trường nào từ ngưỡng trở lên bị đánh dấu thừa

  @ac2 @bien
  Kịch bản: AC2 — ranh giới, điểm tin cậy đúng bằng ngưỡng thì KHÔNG gắn cờ
    Cho một ảnh giấy tờ hợp lệ, đọc được "cccd_sach_01"
    Khi worker trích xuất chạy
    Và ngưỡng được đặt đúng bằng điểm tin cậy của trường "so_dinh_danh"
    Thì trường "so_dinh_danh" không bị đánh dấu cần người xác nhận

  @ac2 @cau-hinh
  Khung kịch bản: AC2 — ngưỡng phải cấu hình được, không được hard-code
    Cho một ảnh giấy tờ hợp lệ, đọc được "cccd_sach_01"
    Và ngưỡng tin cậy cấu hình là <nguong>
    Khi worker trích xuất chạy
    Thì số trường bị đánh dấu cần người xác nhận phải là <so_truong>

    Dữ liệu:
      | nguong | so_truong |
      | 0.00   | 0         |
      | 1.01   | 4         |

  @ac3 @negative @rang-buoc-phap-ly
  Khung kịch bản: AC3 — ảnh không đọc được thì KHÔNG bịa dữ liệu
    Cho một ảnh mờ, lỗi, không đọc được "<anh>"
    Khi worker trích xuất chạy
    Thì hệ thống KHÔNG được trả về bất kỳ giá trị nào
    Và hồ sơ phải mang trạng thái "can_bo_sung"
    Và trạng thái đó phải kèm lý do bằng tiếng người

    Dữ liệu:
      | anh                      |
      | cccd_khong_doc_duoc_01   |
      | cccd_khong_doc_duoc_02   |
      | mau_01_khong_doc_duoc_01 |

  @ac3 @mat-trai
  Kịch bản: AC3 mặt trái — hồ sơ đã cho đi tiếp thì không được thiếu trường bắt buộc
    Cho một ảnh giấy tờ hợp lệ, đọc được "cccd_sach_01"
    Khi worker trích xuất chạy
    Thì nếu hồ sơ đủ điều kiện xử lý thì mọi trường nghiêm trọng phải có giá trị

  @ha-tang
  Kịch bản: Lỗi gọi model không được nhầm thành "model đọc không ra"
    Cho một ảnh không tồn tại "khong_he_ton_tai"
    Khi worker trích xuất chạy
    Thì kết quả phải mang lỗi hạ tầng
    Và không được coi đó là hành vi từ chối theo AC3
