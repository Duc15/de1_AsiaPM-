# language: vi
#
# Góc nhìn NGHIỆP VỤ của kết quả đo — viết để Ban QLDA đọc được mà không cần mở code.
# Các kịch bản dưới đây đọc `ket_qua/tesseract/cham_diem.json` của lượt đo gần nhất,
# nên chúng chạy trong ~1 giây và không gọi lại OCR.
#
# Ngưỡng ở đây là ngưỡng NGHIỆP VỤ trong cau_hinh.json, không phải ngưỡng kỹ thuật.
# Kịch bản không nêu tên model: đổi model không phải sửa file này.
# Kịch bản đầu tiên đang ĐỎ có chủ ý: đó chính là kết luận của bài.

@do-luong @nghiep-vu
Tính năng: Cụm trích xuất có đủ tin cậy để đưa vào hệ thống NƠXH không

  Model nằm giữa ảnh người dân chụp và người duyệt. Câu hỏi duy nhất: đoạn giữa
  có đáng tin không, và biết bằng cách nào.

  Bối cảnh:
    Cho kết quả đo mới nhất của model đang kiểm thử

  @cong_nghiep_vu
  Kịch bản: Cổng chất lượng nghiệp vụ
    Thì điểm tin cậy phải đạt ít nhất ngưỡng nghiệp vụ
    Và accuracy trường nghiêm trọng phải đạt ít nhất ngưỡng nghiệp vụ
    Và số trường nghiêm trọng lọt cổng HITL không được vượt mức cho phép

  @rang-buoc-phap-ly
  Kịch bản: Ràng buộc pháp lý — không bao giờ được bịa
    Thì tỉ lệ bịa dữ liệu trên ảnh không đọc được phải bằng 0
    Và tỉ lệ từ chối đúng phải bằng 100 phần trăm
    Và không được có lỗi hạ tầng nào trong lượt đo

  Khung kịch bản: Chất lượng ảnh tụt tới đâu thì model gãy
    Thì ở bậc ảnh "<bac>" điểm tin cậy phải nằm quanh <ky_vong> phần trăm

    Dữ liệu:
      | bac            | ky_vong |
      | sach           | 66.7    |
      | nhe            | 66.7    |
      | trung_binh     | 10.3    |
      | nang           | 0.0     |
      | khong_doc_duoc | 100.0   |

  Kịch bản: Người dân cảm nhận ở mức hồ sơ, không phải mức trường
    Thì tỉ lệ hồ sơ người đọc được mà vẫn bị trả về phải được báo cáo
    Và con số đó phải tệ hơn con số accuracy mức trường

  Khung kịch bản: Đánh đổi khi đặt ngưỡng cổng HITL
    Thì ở ngưỡng <nguong> phải còn <ro_ri> trường nghiêm trọng lọt cổng

    Dữ liệu:
      | nguong | ro_ri |
      | 0.80   | 6     |
      | 0.90   | 4     |
      | 0.95   | 0     |

  @tu-soi
  Kịch bản: Model đối chứng phải bị bộ đo cho điểm thấp
    Cho kết quả đo của model đối chứng luôn từ chối
    Thì điểm tin cậy của nó phải thấp hơn model đang đo
    Và accuracy trên trường người đọc được của nó phải bằng 0
