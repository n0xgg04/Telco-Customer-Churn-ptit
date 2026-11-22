# Telco Churn · Web trình chiếu

Web Vue 3 dùng Tailwind CSS và Iconify Vue, gồm 12 slide từ [kịch bản Markdown](kich-ban-thuyet-trinh-telco-churn.md).

## Chạy trên máy

Mở terminal trong thư mục `slide`. Dùng Node.js 20.19+ hoặc 22.12+.

```powershell
npm.cmd install
npm.cmd run dev
```

Mở địa chỉ Vite in trong terminal, mặc định là [http://127.0.0.1:5173](http://127.0.0.1:5173).

- **← / →** hoặc **Page Up / Page Down** để đổi slide. **Home / End** để về slide đầu hoặc cuối.
- **F** để bật hoặc tắt chế độ trình chiếu. **Esc** để đóng ảnh, đóng bảng bên hoặc thoát toàn màn hình.
- **Mục lục** để nhảy tới slide. **Lời thoại** hiển thị phần tương ứng trong kịch bản Markdown.
- Slide demo có ba cảnh chụp từ dashboard. Bấm vào ảnh để phóng to. Nút mở dashboard trực tiếp cần Streamlit chạy trên cổng `8501`.

Ảnh chụp lưu trong [images](images/). Để tạo bản build tĩnh, chạy `npm.cmd run build`. Có thể xem bản build bằng `npm.cmd run preview`.
