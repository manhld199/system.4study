# HỆ THỐNG ĐỀ XUẤT KHÓA HỌC TRỰC TUYẾN TỰ ĐỘNG HÓA THEO THỜI GIAN THỰC 4STUDY

* Khoa Khoa học và Kỹ thuật thông tin, Trường Đại học Công nghệ Thông tin, Đại học Quốc gia Thành phố Hồ Chí Minh.
* GVHD: ThS. Nguyễn Thị Anh Thư.
* Nhóm sinh viên thực hiện: Nhóm 1.

## Kiến trúc hệ thống
Nhóm chia kiến trúc hệ thống thành 2 thành phần chính.
* Thành phần ngoại tuyến (Offline): Được nhóm xây dựng và phát triển để huấn luyện và kiểm tra các mô hình, nhằm tìm ra mô hình tối ưu nhất áp dụng trong pipeline đề xuất khóa học trực tuyến theo thời gian thực. Nhóm sử dụng các phương pháp truyền thống bao gồm: Collaborative Filtering, Content-based Filtering, Matrix Factorization; và các phương pháp hiện đại bao gồm: Graph Neural Networks, Neural Collaborative Filtering, Convolutional Neural Networks, Graph Convolutional Networks.
* Thành phần trực tuyến (Online): Là một pipeline đề xuất khóa học trực tuyến trong thời gian thực. Ba công việc chính trong phần này là thu thập dữ liệu trực tuyến từ cơ sở dữ liệu của website, truyền và xử lý dữ liệu theo thời gian thực, và đưa ra kết quả dự đoán, đề xuất khóa học.
![Hệ thống (2000 x 1000 px)](https://github.com/user-attachments/assets/07cce28d-ea94-4618-ab3d-77b1268f6515)

## Công nghệ
* Apache Kafka
* Apache Airflow
* MongoDB
* Azure Storage

## Hướng dẫn cài đặt và thực thi
## Bước 1. Clone repo này về máy
```
$ git clone https://github.com/manhld199/system.4study.git
```

## Bước 2. Tải và cài đặt Docker Desktop
* Tìm kiếm hoặc truy cập vào: https://docs.docker.com/desktop/setup/install/windows-install/ và chọn phiên bản phù hợp để cài đặt.
![image](https://github.com/user-attachments/assets/f3bad5c8-7afa-4b5f-a4ca-effdb99dd063)

## Bước 3. Cài đặt Docker container
* Sử dụng lệnh dưới đây để cài đặt docker container:
```
$ docker compose up --build
```
![image](https://github.com/user-attachments/assets/9f012bb8-b24a-42c5-a535-b9939405b395)

* Đợi một lúc để cài đặt, kết quả sau khi cài đặt:
![image](https://github.com/user-attachments/assets/f49a6822-98d6-4c4b-aa9a-bb4915b4acf5)

## Bước 4. Truy cập vào Airflow
* Truy cập vào đường dẫn: http://127.0.0.1:8080 hoặc http://localhost:8080 để xem giao diện quản lý.
* Đăng nhập vào Airflow với tài khoản - mật khẩu: airflow - airflow, một số giao diện quản lý sau khi đăng nhập:
![image](https://github.com/user-attachments/assets/cfbeb02d-ebb3-4e5d-8dc9-2cf3b6cc2b25)
![image](https://github.com/user-attachments/assets/b6921e84-830d-437b-b9b7-900644ba118c)
![image](https://github.com/user-attachments/assets/429c8a72-a143-40ce-8eee-80d0f252b914)
![image](https://github.com/user-attachments/assets/9071bdf3-1512-4c12-9992-6661062c05f7)
