# Lựa chọn công nghệ — Tại sao Python thay vì Go

## Giới thiệu

Một trong những câu hỏi thường gặp khi nhìn vào Data Service là:

> Tại sao lựa chọn Python thay vì Go?

Ở nhiều hệ thống backend hiện đại, Go thường được xem là lựa chọn phù hợp cho các dịch vụ hạ tầng nhờ hiệu năng cao, khả năng xử lý đồng thời tốt và chi phí tài nguyên thấp.

Tuy nhiên, đối với Data Service của Xime Platform, việc lựa chọn công nghệ được đánh giá dựa trên mục tiêu của từng giai đoạn phát triển thay vì chỉ dựa trên benchmark CPU.

---

## Hai giai đoạn phát triển khác nhau

Data Service được phát triển theo hai giai đoạn riêng biệt.

### Giai đoạn 1 — Xây dựng nền tảng và tài liệu tham khảo

Mục tiêu của giai đoạn đầu là:

* Hoàn thiện kiến trúc Data Service
* Chứng minh tính khả thi của Xime Framework
* Làm tài liệu tham khảo cho cộng đồng
* Tạo ví dụ thực tế cho cách xây dựng Microservice bằng Xime
* Tăng tốc độ phát triển sản phẩm

Trong giai đoạn này:

* Data Service được viết hoàn toàn bằng Python
* Không triển khai mã hóa file
* Không tối ưu hóa CPU ở mức thấp
* Tập trung vào kiến trúc, khả năng mở rộng và trải nghiệm phát triển

Các thành phần chính bao gồm:

* Data Object
* Ownership
* Permission
* Versioning
* Lifecycle
* Audit
* Routing
* Storage

Phần lớn workload của hệ thống là:

* Database I/O
* Disk I/O
* Network I/O
* Permission Evaluation

Đây đều là các tác vụ không bị giới hạn bởi hiệu năng CPU của Python.

Trong bối cảnh đó, lợi ích lớn nhất của Python là:

* Tốc độ phát triển nhanh
* Code ngắn gọn
* Dễ đọc
* Dễ thay đổi kiến trúc
* Dễ xây dựng framework
* Dễ tạo tài liệu tham khảo cho cộng đồng

Việc chuyển sang Go ở giai đoạn này sẽ làm tăng chi phí phát triển trong khi giá trị nhận lại không đáng kể.

---

## Giai đoạn 2 — Sản phẩm thương mại

Khi Data Service bước vào giai đoạn kinh doanh thực tế, yêu cầu của hệ thống sẽ thay đổi.

Lúc này các vấn đề cần giải quyết bao gồm:

* Bảo vệ dữ liệu khách hàng
* Mã hóa file
* Tối ưu CPU
* Tăng khả năng xử lý đồng thời
* Giảm chi phí tài nguyên

Trong giai đoạn này, hệ thống sẽ bổ sung một thành phần mới:

```text
Data Service (Python)

        │

        │ Unix Domain Socket

        ▼

xime-cryptod (C/C++)

        │

        ├── Worker 1
        ├── Worker 2
        ├── Worker 3
        ├── Worker N
        │

        ▼

OpenSSL
```

Data Service vẫn chịu trách nhiệm:

* Routing
* Permission
* Ownership
* Metadata
* Versioning
* Lifecycle

Trong khi đó:

```text
xime-cryptod
```

là tiến trình nền chuyên trách:

* Encrypt File
* Decrypt File
* Key Management
* Streaming File
* CPU Intensive Workloads

---

## Tại sao không mã hóa trực tiếp trong Python

Việc mã hóa file hoàn toàn có thể thực hiện bằng Python thông qua các thư viện như:

* cryptography
* PyNaCl

Tuy nhiên khi hệ thống phát triển lớn hơn, việc tách riêng thành tiến trình C/C++ mang lại nhiều lợi ích:

### Tận dụng OpenSSL trực tiếp

OpenSSL được viết bằng C và tối ưu rất sâu cho:

* AES-NI
* AVX2
* AVX512
* Hardware Acceleration

Các worker có thể gọi trực tiếp API của OpenSSL mà không cần đi qua lớp wrapper Python.

---

### Xử lý song song tốt hơn

Tiến trình crypto có thể duy trì:

```text
Worker Pool
```

với số lượng worker tùy theo cấu hình máy chủ.

Ví dụ:

```text
8 Core CPU

↓

8 Crypto Workers
```

Các worker hoạt động độc lập và xử lý đồng thời nhiều file.

---

### Tách biệt trách nhiệm

Data Service tập trung vào nghiệp vụ:

* Permission
* Metadata
* Routing

Crypto Service tập trung vào:

* Encryption
* Decryption

Điều này giúp hệ thống dễ bảo trì hơn.

---

### Tăng độ ổn định

Nếu có lỗi trong thành phần mã hóa:

```text
xime-cryptod crash
```

thì Data Service vẫn tiếp tục hoạt động.

Ngược lại, nếu mã hóa nằm trong cùng process Python, lỗi ở tầng native có thể ảnh hưởng trực tiếp đến toàn bộ service.

---

## Tại sao không chuyển toàn bộ sang Go

Khi phần nặng nhất của hệ thống đã được chuyển sang:

```text
C/C++
+
OpenSSL
```

thì lợi thế hiệu năng của Go giảm đi đáng kể.

Luồng xử lý thực tế lúc đó là:

```text
Python

↓

Unix Domain Socket

↓

C/C++

↓

OpenSSL
```

CPU chủ yếu dành thời gian thực thi:

```text
OpenSSL
```

chứ không phải:

```text
Python
```

Do đó việc thay thế toàn bộ Data Service bằng Go không còn mang lại nhiều giá trị tương xứng với chi phí chuyển đổi.

---

## Triết lý lựa chọn công nghệ

Data Service không cố gắng tối ưu mọi thứ ngay từ đầu.

Triết lý của dự án là:

```text
Ưu tiên tốc độ phát triển trong giai đoạn đầu.

Chỉ tối ưu những phần thực sự trở thành nút thắt cổ chai.
```

Vì vậy:

Giai đoạn 1:

```text
Python
+
Xime Framework
```

Giai đoạn 2:

```text
Python
+
Xime Framework
+
xime-cryptod (C/C++)
+
OpenSSL
```

Kiến trúc này cho phép giữ được tốc độ phát triển cao của Python trong khi vẫn tận dụng được hiệu năng tối đa của C/C++ ở những nơi thực sự cần thiết.
