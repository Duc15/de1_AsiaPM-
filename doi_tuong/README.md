# Lớp đối tượng — cách thêm web và mobile

## Vì sao không gọi là "Page Object"

Page Object sinh ra để giấu **locator** của một trang web. Bài 1 không có trang,
không có locator, không có trình duyệt — đối tượng dưới quyền là một cụm model OCR
chạy headless. Gọi nó là `Page` thì cái tên nói dối về thứ nó bọc, và người sau sẽ
đi tìm `driver` không có ở đâu cả.

Nhưng **nguyên lý** của POM giữ nguyên, và chính nó là thứ cần cho việc scale:

> giấu **cách** tương tác → phơi ra **hành vi nghiệp vụ** → bước Gherkin viết một
> lần, dùng cho mọi nền tảng.

## Ba tầng

```
features/*.feature          Gherkin — nguồn sự thật nghiệp vụ. KHÔNG đổi khi thêm nền tảng.
    ↓
tests/test_bdd_*.py         Bước Cho/Khi/Thì. Chỉ gọi qua lớp đối tượng.
    ↓
doi_tuong/                  Lớp đối tượng. ĐÂY là chỗ duy nhất đổi khi thêm nền tảng.
    co_so.py                DoiTuongKiemThu + KetQuaTruong + KetQuaXuLy
    ho_so_giay_to.py        bài 1  — model trích xuất
    trang_tiep_nhan.py      bài 2  — web (chưa có)
    man_hinh_tiep_nhan.py   mobile — Appium (chưa có)
```

## Hợp đồng chung

Mọi nền tảng cài `DoiTuongKiemThu` và trả về cùng `KetQuaXuLy`:

| Phương thức | web | mobile | model (bài 1) |
|---|---|---|---|
| `mo(dinh_danh)` | `page.goto(url)` | mở màn hình | nạp ảnh giấy tờ |
| `xu_ly()` | bấm nộp | chạm nút | chạy worker trích xuất |
| `tu_kiem_tra()` | trang load được không | app khởi động được không | canary OCR |

`KetQuaTruong` cố ý có cả `tin_cay` lẫn `loi`: model điền `tin_cay` và bỏ trống
`loi`; web thì ngược lại. Bước Gherkin nào cần gì thì kiểm cái đó — không nền tảng
nào phải giả vờ có thứ nó không có.

## Thêm nền tảng web (bài 2)

```python
# doi_tuong/trang_tiep_nhan.py
class TrangTiepNhanHoSo(DoiTuongKiemThu):
    ten_nen_tang = "web"

    def __init__(self, page): self._page = page

    def mo(self, dinh_danh):
        self._page.goto(f"/tiep-nhan/{dinh_danh}")
        return self

    def xu_ly(self):
        self._page.get_by_role("button", name="Nộp hồ sơ").click()
        truong = {}
        for ten in ("so_dinh_danh", "ho_ten", "hinh_thuc"):
            o = self._page.get_by_test_id(ten)
            truong[ten] = KetQuaTruong(
                ten=ten,
                gia_tri=o.input_value(),
                loi=o.get_attribute("aria-errormessage"),
                can_nguoi_xac_nhan=o.get_attribute("data-can-xac-nhan") == "true")
        return KetQuaXuLy(trang_thai=self._page.get_by_test_id("trang-thai").inner_text(),
                          truong=truong)

    def tu_kiem_tra(self):
        return self._page.title() != "", "trang load được"
```

Rồi trong file bước, đổi đúng một fixture:

```python
@pytest.fixture(scope="module")
def doi_tuong(page):
    return TrangTiepNhanHoSo(page)     # thay cho HoSoGiayTo()
```

Các bước `Thì trường "X" phải bị đánh dấu cần người xác nhận`,
`Thì hồ sơ phải mang trạng thái "can_bo_sung"` dùng lại nguyên vẹn.

## Ranh giới phải giữ

1. **Feature file không được nhắc tới kỹ thuật.** Không có "click", "locator",
   "pytesseract", "psm 6" trong `.feature`. Thấy chúng ở đó là lớp đối tượng đang
   rò rỉ ra ngoài.
2. **Bước Gherkin không import driver.** `tests/test_bdd_*.py` chỉ import từ
   `doi_tuong/`. Kiểm bằng mắt: file bước của bài 1 không có chữ "tesseract" nào.
3. **Lớp đối tượng không chứa assertion.** Nó trả dữ liệu; phán quyết đúng/sai là
   việc của bước `Thì`. Trộn hai thứ thì không tái dùng được cho nền tảng khác.

## Một lưu ý đã trả giá

`HoSoGiayTo` từng cache cả kết quả đã áp cổng HITL, khoá theo (ảnh, loại giấy tờ).
Kịch bản *"ngưỡng phải cấu hình được"* đổi ngưỡng xong vẫn nhận cờ cũ và đỏ — đúng
cái nó sinh ra để bắt, chỉ có điều lỗi nằm ở **lớp đối tượng** chứ không ở model.
Nay chỉ phần OCR (đắt, không phụ thuộc ngưỡng) được cache; cờ tính lại mỗi lần.

Bài học chung cho POM: **chỉ cache thứ tốn kém và bất biến, đừng cache thứ phụ
thuộc tham số của ca kiểm thử.**
