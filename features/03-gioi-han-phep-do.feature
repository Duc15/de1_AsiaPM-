# language: vi
#
# ĐÂY LÀ FILE TRẢ LỜI MỤC "ĐIỀU CHÚNG TÔI QUAN TÂM NHẤT" CỦA ĐỀ.
#
#   "Không phải con số accuracy bạn đo được — con số đó phụ thuộc vào model bạn
#    tình cờ chọn, và model sẽ đổi. Chúng tôi quan tâm: bạn có biết phép đo của
#    chính mình không chứng minh được điều gì không?"
#
# Nếu để phần giới hạn nằm dưới dạng một đoạn văn cuối báo cáo thì nó là thứ dễ
# viết cho có, dễ quên cập nhật, và không ai phát hiện khi nó lạc hậu. Nên ở đây
# giới hạn là DỮ LIỆU (gioi_han/so_gioi_han.json) và các kịch bản dưới đây canh
# nó như canh bất kỳ hành vi nào khác:
#
#   - công bố một chỉ số mới mà quên khai giới hạn  -> ĐỎ
#   - khai giới hạn mà không nói cần bằng chứng gì để gỡ -> ĐỎ
#   - tuyên bố đã gỡ một giới hạn mà không dẫn được bằng chứng -> ĐỎ
#
# Nói cách khác: bộ test không cho phép báo cáo có con số mà không có giới hạn đi kèm.

@gioi-han @dieu-quan-tam-nhat
Tính năng: Phép đo này không chứng minh được điều gì

  Một báo cáo nói rõ giới hạn của nó có giá trị hơn một báo cáo toàn số đẹp.
  Muốn điều đó đúng lâu dài thì giới hạn phải được máy canh, không phải được nhớ.

  Bối cảnh:
    Cho sổ giới hạn đã được nạp
    Và kết quả đo mới nhất đã có

  Kịch bản: Mọi chỉ số công bố trong báo cáo đều phải có ít nhất một giới hạn
    Khi tôi đối chiếu các chỉ số công bố với sổ giới hạn
    Thì không được có chỉ số nào không được giới hạn nào phủ

  Khung kịch bản: Mỗi giới hạn phải nói rõ nó CHẶN điều gì
    Cho giới hạn "<ma>"
    Thì nó phải nêu được điều phép đo không chứng minh được
    Và nó phải nêu được bằng chứng cần thu thập để gỡ
    Và nó phải nêu được hậu quả nếu bỏ qua
    Và mức độ của nó phải thuộc tập cho phép

    Dữ liệu:
      | ma    |
      | GH-01 |
      | GH-02 |
      | GH-03 |
      | GH-04 |
      | GH-05 |
      | GH-06 |
      | GH-07 |
      | GH-08 |
      | GH-09 |
      | GH-10 |
      | GH-11 |

  Kịch bản: Giới hạn đã gỡ phải dẫn được bằng chứng đã gỡ nó
    Khi tôi lọc các giới hạn có trạng thái "da_go"
    Thì mỗi giới hạn đó phải dẫn được bằng chứng cụ thể
    Và bằng chứng đó phải trỏ tới một tệp có thật trong repo

  Kịch bản: Giới hạn chặn kết luận phải xuất hiện trong báo cáo 2 trang
    Khi tôi lọc các giới hạn mức "chan_ket_luan"
    Thì mỗi giới hạn đó phải được nhắc tới trong BAO-CAO.md

  Kịch bản: Con số càng nổi bật thì càng phải có giới hạn nặng đi kèm
    Cho chỉ số nổi bật nhất của báo cáo là "accuracy_truong_doc_duoc"
    Thì nó phải bị ít nhất một giới hạn mức "chan_ket_luan" phủ

  @tu-soi
  Kịch bản: Sổ giới hạn không được rỗng và không được toàn "đã gỡ"
    Thì phải còn ít nhất 5 giới hạn đang mở
    Và điều đó được ghi thẳng vào báo cáo chứ không giấu trong phụ lục
