import cv2
import face_recognition
import os
import time

# --- CẤU HÌNH ---
SAVED_FACE_PATH = "chu_nhan_o_tu.jpg"
TEMP_IMAGE_PATH = "temp_incoming.jpg"

def main():
    # Khởi chạy webcam của Mac M1
    # Nếu Mac hỏi quyền truy cập Camera, hãy chọn 'Allow'
    video_capture = cv2.VideoCapture(0)
    
    if not video_capture.isOpened():
        print("[LỖI] Không thể mở Webcam của Mac M1!")
        return

    print("\n=======================================================")
    print("[GIẢ LẬP] HỆ THỐNG TỦ THÔNG MINH BẰNG WEBCAM")
    print("=======================================================")
    print("HƯỚNG DẪN BẤM PHÍM TRÊN BÀN PHÍM:")
    print(" - Bấm phím 'S' (Space/Chụp): Để kích hoạt gửi đồ hoặc lấy đồ")
    print(" - Bấm phím 'Q' (Quit): Để thoát chương trình giả lập")
    print("-------------------------------------------------------")

    while True:
        # Đọc khung hình từ webcam để hiển thị lên màn hình
        ret, frame = video_capture.read()
        if not ret:
            break

        # Kiểm tra trạng thái tủ hiện tại để hiển thị văn bản lên luồng video
        if not os.path.exists(SAVED_FACE_PATH):
            status_text = "TRANG THAI: TU TRONG - Bam 'S' de GUI DO"
            color = (0, 255, 0) # Màu xanh lá
        else:
            status_text = "TRANG THAI: CO DO - Bam 'S' de LAY DO"
            color = (0, 0, 255) # Màu đỏ

        # Vẽ chữ trạng thái lên màn hình camera để dễ quan sát
        cv2.putText(frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        cv2.imshow('Gia Lap Locker - STM32 Cam', frame)

        # Chờ người dùng bấm nút trên bàn phím
        key = cv2.waitKey(1) & 0xFF

        # --- KỊCH BẢN KHI BẤM PHÍM 'S' (GIẢ LẬP BẤM NÚT TRÊN STM32) ---
        if key == ord('s') or key == ord('S'):
            print("\n[TÍN HIỆU] Đã bấm nút chụp ảnh!")
            
            # Lưu khung hình hiện tại của webcam thành file ảnh tạm
            cv2.imwrite(TEMP_IMAGE_PATH, frame)
            print("[XỬ LÝ] Đã chụp ảnh thành công. Đang phân tích khuôn mặt...")

            # Trích xuất dữ liệu khuôn mặt bằng AI
            try:
                incoming_image = face_recognition.load_image_file(TEMP_IMAGE_PATH)
                incoming_encodings = face_recognition.face_encodings(incoming_image)
            except Exception as e:
                print(f"[LỖI AI] Không xử lý được ảnh: {e}")
                continue

            if len(incoming_encodings) == 0:
                print("[XÁC THỰC THẤT BẠI] Không tìm thấy khuôn mặt nào trước camera. Thử lại!")
                if os.path.exists(TEMP_IMAGE_PATH): os.remove(TEMP_IMAGE_PATH)
                continue

            incoming_encoding = incoming_encodings[0]

            # LOGIC TRƯỜNG HỢP 1: TỦ TRỐNG -> GỬI ĐỒ
            if not os.path.exists(SAVED_FACE_PATH):
                os.rename(TEMP_IMAGE_PATH, SAVED_FACE_PATH)
                print("=========================================")
                print("[KẾT QUẢ SERVER]: LỆNH 'OPEN' ĐƯỢC PHÁT!")
                print("[MÔ PHỎNG]: Khóa từ bật mở -> Hãy cất đồ.")
                print("[HỆ THỐNG]: Đã lưu mặt bạn làm gốc. Tủ chuyển sang KHÓA.")
                print("=========================================")
                time.sleep(2) # Tạm dừng 2 giây để người dùng đọc thông báo

            # LOGIC TRƯỜNG HỢP 2: TỦ ĐANG KHÓA -> LẤY ĐỒ
            else:
                print("[XỬ LÝ] Đang so sánh khuôn mặt bạn với chủ tủ gốc (FaceNet)...")
                saved_image = face_recognition.load_image_file(SAVED_FACE_PATH)
                saved_encoding = face_recognition.face_encodings(saved_image)[0]

                # So sánh 2 khuôn mặt
                results = face_recognition.compare_faces([saved_encoding], incoming_encoding, tolerance=0.45)

                if results[0] == True:
                    print("=========================================")
                    print("[KẾT QUẢ SERVER]: LỆNH 'OPEN' ĐƯỢC PHÁT!")
                    print("[MÔ PHỎNG]: ĐÚNG CHỦ NHÂN -> Khóa từ bật mở thành công.")
                    print("[HỆ THỐNG]: Tủ đã được giải phóng về trạng thái TRỐNG.")
                    print("=========================================")
                    os.remove(SAVED_FACE_PATH) # Xóa ảnh gốc, giải phóng tủ
                else:
                    print("=========================================")
                    print("[KẾT QUẢ SERVER]: LỆNH 'DENY'!!!")
                    print("[MÔ PHỎNG]: SAI KHUÔN MẶT -> Khóa đóng chặt, báo còi!")
                    print("=========================================")
                
                if os.path.exists(TEMP_IMAGE_PATH): os.remove(TEMP_IMAGE_PATH)
                time.sleep(2)

        # --- BẤM 'Q' ĐỂ THOÁT ---
        elif key == ord('q') or key == ord('Q'):
            break

    # Dọn dẹp luồng camera khi tắt ứng dụng
    video_capture.release()
    cv2.destroyAllWindows()
    if os.path.exists(TEMP_IMAGE_PATH): os.remove(TEMP_IMAGE_PATH)
    print("\n[HỆ THỐNG] Đã đóng chương trình giả lập.")

if __name__ == "__main__":
    main()