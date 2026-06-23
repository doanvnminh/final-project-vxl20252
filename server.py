import socket
import face_recognition
import os

# --- CẤU HÌNH ---
SERVER_IP = '0.0.0.0'    # Lắng nghe mọi thiết bị kết nối qua Wi-Fi
SERVER_PORT = 5000       # Cổng kết nối với STM32
SAVED_FACE_PATH = "chu_nhan_o_tu.jpg" # File ảnh lưu khuôn mặt người gửi đồ
TEMP_IMAGE_PATH = "temp_incoming.jpg" # File ảnh tạm khi người đến lấy đồ

def start_server():
    # Tạo socket TCP/IP
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((SERVER_IP, SERVER_PORT))
    server_socket.listen(1)
    
    print("\n=======================================================")
    print("[MÔ HÌNH THỬ NGHIỆM] SERVER Ô TỦ THÔNG MINH ĐÃ SẴN SÀNG")
    print(f"[STATUS] Lắng nghe STM32 tại cổng {SERVER_PORT}...")
    print("=======================================================")

    while True:
        print("\n-------------------------------------------------------")
        # Kiểm tra trạng thái ô tủ dựa trên việc file ảnh gốc có tồn tại hay không
        if not os.path.exists(SAVED_FACE_PATH):
            print("[TRẠNG THÁI TỦ]: TRỐNG (Sẵn sàng nhận ĐĂNG KÝ GỬI ĐỒ)")
        else:
            print("[TRẠNG THÁI TỦ]: ĐANG KHÓA CÓ ĐỒ (Sẵn sàng quét mặt LẤY ĐỒ)")
            
        print("[CHỜ KẾT NỐI] Đang đợi STM32 chụp ảnh gửi lên...")
        client_socket, client_address = server_socket.accept()
        print(f"[KẾT NỐI] Nhận tín hiệu từ STM32 tại: {client_address}")

        try:
            # 1. Nhận luồng dữ liệu ảnh từ STM32 và ghi ra file tạm trước
            with open(TEMP_IMAGE_PATH, "wb") as f:
                while True:
                    data = client_socket.recv(4096)
                    if not data:
                        break # STM32 ngắt kết nối = gửi xong ảnh
                    f.write(data)
            
            print("[NHẬN ẢNH] Đã nhận xong ảnh từ STM32 Cam.")

            # Trích xuất và kiểm tra xem ảnh gửi lên có khuôn mặt không
            try:
                incoming_image = face_recognition.load_image_file(TEMP_IMAGE_PATH)
                incoming_encodings = face_recognition.face_encodings(incoming_image)
            except Exception as e:
                print(f"[LỖI] Không thể đọc file ảnh: {e}")
                client_socket.sendall(b"DENY\n")
                continue

            if len(incoming_encodings) == 0:
                print("[XỬ LÝ THẤT BẠI] Ảnh chụp không rõ nét hoặc không có khuôn mặt!")
                client_socket.sendall(b"DENY\n")
                continue
                
            incoming_encoding = incoming_encodings[0]

            # 2. BIỆN PHÁP LOGIC: XỬ LÝ GỬI ĐỒ / LẤY ĐỒ
            # TRƯỜNG HỢP 1: TỦ TRỐNG -> THỰC HIỆN GỬI ĐỒ
            if not os.path.exists(SAVED_FACE_PATH):
                # Đổi tên file tạm thành file chính thức để khóa tủ lại
                os.rename(TEMP_IMAGE_PATH, SAVED_FACE_PATH)
                print("[XỬ LÝ SUCCESS] Đã lưu khuôn mặt người GỬI ĐỒ thành công!")
                print("[GỬI TÍN HIỆU] Phát lệnh 'OPEN' để mở tủ cất đồ...")
                client_socket.sendall(b"OPEN\n")

            # TRƯỜNG HỢP 2: TỦ ĐANG CÓ ĐỒ -> THỰC HIỆN LẤY ĐỒ (ĐỐI CHIẾU FACENET)
            else:
                print("[XỬ LÝ] Đang đối chiếu khuôn mặt người lấy đồ...")
                # Nạp ảnh gốc của người gửi đồ trước đó
                saved_image = face_recognition.load_image_file(SAVED_FACE_PATH)
                saved_encoding = face_recognition.face_encodings(saved_image)[0]

                # So sánh khoảng cách vector FaceNet (Sai số tolerance = 0.45)
                results = face_recognition.compare_faces([saved_encoding], incoming_encoding, tolerance=0.45)

                if results[0] == True:
                    print("[XÁC THỰC THÀNH CÔNG] ĐÚNG CHỦ NHÂN ĐÃ GỬI ĐỒ!")
                    # Giải phóng ô tủ: Xóa ảnh gốc đi để người tiếp theo có thể dùng
                    os.remove(SAVED_FACE_PATH)
                    print("[XỬ LÝ] Đã giải phóng tủ về trạng thái TRỐNG.")
                    print("[GỬI TÍN HIỆU] Phát lệnh 'OPEN' trả hàng.")
                    client_socket.sendall(b"OPEN\n")
                else:
                    print("[XÁC THỰC THẤT BẠI] SAI KHUÔN MẶT! CẢNH BÁO KẺ GIAN!")
                    client_socket.sendall(b"DENY\n")

        except Exception as e:
            print(f"[LỖI HỆ THỐNG] Gặp sự cố khi xử lý dữ liệu: {e}")
        finally:
            client_socket.close()
            # Dọn dẹp file tạm nếu còn sót lại
            if os.path.exists(TEMP_IMAGE_PATH):
                os.remove(TEMP_IMAGE_PATH)