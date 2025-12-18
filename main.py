import sys
import cv2
import mediapipe as mp
import speech_recognition as sr
import threading
import requests
import feedparser
import google.generativeai as genai
from PyQt5.QtWidgets import QApplication
from PyQt5.QtQml import QQmlApplicationEngine
from PyQt5.QtCore import QObject, pyqtSignal, QTimer, Qt, QTime, QDate
from PyQt5.QtGui import QImage
from PyQt5.QtQuick import QQuickImageProvider
import math
import os
import time
import subprocess 

# ---------------------------------------------------
# CONFIG
# ---------------------------------------------------

WEATHER_API_KEY = "abc" 
CITY = "Hanoi"
PHOTO_SAVE_PATH = r"photos" 
GEMINI_API_KEY = "abc" 

# FILE THỰC THI (SYSTEMC / C++ MOCK)
# Tự động phát hiện hệ điều hành để chọn tên file đúng
if os.name == 'nt': # Windows
    SYSTEMC_TIMER_EXEC = "camera_timer.exe"
    SYSTEMC_GESTURE_EXEC = "hand_decision.exe"
else: # Linux / Raspberry Pi
    SYSTEMC_TIMER_EXEC = "./camera_timer"
    SYSTEMC_GESTURE_EXEC = "./hand_decision"

# ---------------------------------------------------
# INIT GEMINI
# ---------------------------------------------------
ai_model = None
model_name_used = "Unknown"

try:
    genai.configure(api_key=GEMINI_API_KEY)
    print(">>> Đang khởi tạo AI...")
    all_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    
    priority_list = ["models/gemini-flash-latest", "models/gemini-1.5-flash", "models/gemini-pro"]
    selected_model = None
    
    for p in priority_list:
        if p in all_models:
            selected_model = p
            break
            
    if not selected_model and all_models:
        selected_model = all_models[0]

    if selected_model:
        ai_model = genai.GenerativeModel(selected_model)
        model_name_used = selected_model
        print(f">>> MODEL ĐÃ CHỌN: {selected_model}")
    else:
        print(">>> KHÔNG TÌM THẤY MODEL NÀO!")

except Exception as e:
    print(">>> LỖI INIT AI:", e)

# ---------------------------------------------------
# IMAGE PROVIDER
# ---------------------------------------------------
class LiveImageProvider(QQuickImageProvider):
    def __init__(self):
        super().__init__(QQuickImageProvider.Image)
        self.current_image = None

    def requestImage(self, id, size, requestedSize=None):
        if self.current_image is not None:
            return self.current_image, self.current_image.size()
        img = QImage(320, 240, QImage.Format_RGB888)
        img.fill(Qt.black)
        return img, img.size()

    def update_image(self, img):
        self.current_image = img

# ---------------------------------------------------
# VOICE WORKER
# ---------------------------------------------------
class VoiceWorker(threading.Thread):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback
        self.recognizer = sr.Recognizer()
        self.daemon = True
        self.mics = sr.Microphone.list_microphone_names()
        self.device_index = 0
        
        for i, m in enumerate(self.mics):
            if "USB" in m or "Usb" in m:
                self.device_index = i
                break
        print(f"Voice Thread started on MIC index: {self.device_index}")

    def run(self):
        while True:
            try:
                with sr.Microphone(device_index=self.device_index) as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    audio = self.recognizer.listen(source, timeout=None, phrase_time_limit=5)
                    try:
                        text = self.recognizer.recognize_google(audio, language="vi-VN")
                        print("User said:", text)
                        self.callback(text.lower())
                    except sr.UnknownValueError:
                        pass
                    except Exception as e:
                        print("Speech error:", e)
            except Exception as e:
                print("Voice thread fatal error:", e)

# ---------------------------------------------------
# BACKEND
# ---------------------------------------------------
class Backend(QObject):
    imageUpdated = pyqtSignal(str)
    updateClock = pyqtSignal(str, str)
    updateWeather = pyqtSignal(str, str)
    updateNews = pyqtSignal(str)
    updateAI = pyqtSignal(str)
    changePage = pyqtSignal(int)
    updateVoiceStatus = pyqtSignal(str)

    def __init__(self, img_provider):
        super().__init__()
        self.img_provider = img_provider
        self.cap = cv2.VideoCapture(0)

        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(max_num_hands=1, min_detection_confidence=0.7)
        self.mpDraw = mp.solutions.drawing_utils

        # Gesture state
        self.last_open_time = 0
        self.last_fist_time = 0
        
        # Context Data
        self.context_weather = "Đang cập nhật..."
        self.context_news = "Đang cập nhật..."

        # Timers
        self.timer = QTimer()
        self.timer.timeout.connect(self.game_loop)
        self.timer.start(30)

        self.weather_timer = QTimer()
        self.weather_timer.timeout.connect(self.fetch_weather)
        self.weather_timer.start(1800000)

        self.news_timer = QTimer()
        self.news_timer.timeout.connect(self.fetch_news)
        self.news_timer.start(600000)

        QTimer.singleShot(1000, self.fetch_weather)
        QTimer.singleShot(2000, self.fetch_news)

        self.voice_thread = VoiceWorker(self.process_voice)
        self.voice_thread.start()

    # --- WEATHER ---
    def fetch_weather(self):
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={WEATHER_API_KEY}&units=metric&lang=vi"
            data = requests.get(url, timeout=5).json()
            if data.get("cod") != 200: return

            lat, lon = data['coord']['lat'], data['coord']['lon']
            temp = int(data['main']['temp'])
            desc = data["weather"][0]["description"]
            icon = data["weather"][0]["icon"]

            try:
                url_air = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}"
                aqi = requests.get(url_air, timeout=5).json()['list'][0]['main']['aqi']
            except:
                aqi = "?"

            self.context_weather = f"Tại {CITY}: {temp}°C, {desc}. AQI {aqi}."
            self.updateWeather.emit(f"{temp}°C", desc.title() + "|" + icon)
        except Exception as e:
            print("Fetch Weather Error:", e)

    def get_fresh_weather_info(self):
        # Hàm rút gọn để lấy weather khi hỏi AI
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={WEATHER_API_KEY}&units=metric&lang=vi"
            data = requests.get(url, timeout=5).json()
            temp = int(data['main']['temp'])
            desc = data["weather"][0]["description"]
            return f"{temp}°C, {desc}"
        except:
            return "Không rõ"

    # --- NEWS ---
    def fetch_news(self):
        try:
            rss_urls = ["https://vnexpress.net/rss/tin-moi-nhat.rss"]
            display_titles = [e.title for e in feedparser.parse(rss_urls[0]).entries[:10]]
            self.context_news = "Tin tức: " + "; ".join(display_titles[:5])
            self.updateNews.emit("TIN MỚI: " + "   ✦   ".join(display_titles))
        except Exception as e:
            print("News Error:", e)

    # --- VOICE & SYSTEMC PHOTO ---
    def process_voice(self, text):
        corrections = {
            "tiêu cực tím": "tia cực tím",
            "chụp hình": "chụp ảnh",
            "lưu ảnh": "chụp ảnh"
        }
        for wrong, right in corrections.items():
            if wrong in text: text = text.replace(wrong, right)

        self.updateVoiceStatus.emit("🗣 " + text)

        if "chụp ảnh" in text:
            self.take_photo_with_systemc()
            return

        if ai_model:
            self.ask_gemini(text)
        else:
            self.updateAI.emit("Lỗi: Không tìm thấy AI.")

    def take_photo_with_systemc(self):
        # Chức năng chụp ảnh có sử dụng SystemC Timer (nếu có file)
        try:
            if not os.path.exists(PHOTO_SAVE_PATH):
                os.makedirs(PHOTO_SAVE_PATH)
            
            self.changePage.emit(1)
            self.updateAI.emit("Kích hoạt Timer phần cứng...")
            
            # Kiểm tra file thực thi timer
            if os.path.exists(SYSTEMC_TIMER_EXEC):
                process = subprocess.Popen(
                    [SYSTEMC_TIMER_EXEC], 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE,
                    text=True
                )
                while True:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        clean_out = output.strip()
                        if "T-minus" in clean_out:
                            self.updateAI.emit(f"Đếm ngược: {clean_out.split(' ')[-1]}")
            else:
                # Fallback nếu chưa build file C++ timer
                print("Không tìm thấy file timer C++, chạy fallback Python.")
                for i in range(3, 0, -1):
                    self.updateAI.emit(str(i))
                    time.sleep(1)

            ret, frame = self.cap.read()
            if ret:
                frame = cv2.flip(frame, 1)
                timestamp = int(time.time())
                filename = f"{PHOTO_SAVE_PATH}/anh_{timestamp}.jpg"
                cv2.imwrite(filename, frame)
                self.updateAI.emit("Đã chụp xong!")
        except Exception as e:
            print("Photo Error:", e)
            self.updateAI.emit("Lỗi chụp ảnh.")

    def ask_gemini(self, text):
        self.updateAI.emit("Đang suy nghĩ...")
        self.changePage.emit(1)
        
        def run_ai():
            try:
                info = self.get_fresh_weather_info() if "thời tiết" in text else self.context_weather
                sys_prompt = f"Trả lời ngắn gọn dưới 3 câu. Thời gian: {QTime.currentTime().toString()}. Dữ liệu: {info}. Câu hỏi: {text}"
                res = ai_model.generate_content(sys_prompt)
                if res and res.text:
                    self.updateAI.emit(res.text.strip())
            except Exception as e:
                self.updateAI.emit(f"Lỗi AI: {str(e)[:40]}...")

        threading.Thread(target=run_ai).start()

    # ---------------------------------------------------
    # GESTURE WITH SYSTEMC / C++ MOCK INTEGRATION
    # ---------------------------------------------------
    
    def run_systemc_decision(self, finger_count):
        """
        Gọi file thực thi C++ (hand_decision.exe) để ra quyết định
        Input: Số lượng ngón tay (int)
        Output: 1 (Open), 0 (Close), -1 (Hold)
        """
        try:
            if not os.path.exists(SYSTEMC_GESTURE_EXEC):
                print(f"LỖI: Không tìm thấy file {SYSTEMC_GESTURE_EXEC}")
                return -1 # Không làm gì nếu thiếu file

            # Gọi process
            cmd = [SYSTEMC_GESTURE_EXEC, str(finger_count)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Đọc kết quả in ra từ C++ (stdout)
            output = result.stdout.strip()
            if output:
                return int(output)
            return -1
        except Exception as e:
            print(f"SystemC Call Error: {e}")
            return -1

    def detect_gesture(self, handLms):
        lm = handLms.landmark
        tips = [4, 8, 12, 16, 20]
        pips = [3, 6, 10, 14, 18]

        finger_open = []
        # Logic đơn giản để đếm ngón tay
        # Lưu ý: Ngón cái check x hoặc y tùy hướng tay, ở đây dùng tạm logic y cho đơn giản
        for tip, pip in zip(tips[1:], pips[1:]):
            finger_open.append(lm[tip].y < lm[pip].y)

        # Xử lý riêng ngón cái (tương đối)
        if lm[tips[0]].x < lm[pips[0]].x: 
            finger_open.append(True)
        
        total_open = sum(finger_open)

        # --- GỌI HARDWARE SIMULATION ---
        decision = self.run_systemc_decision(total_open)
        
        now = QTime.currentTime().msecsSinceStartOfDay()

        if decision == 1: # C++ bảo MỞ AI
            if self.last_open_time == 0:
                self.last_open_time = now
            elif now - self.last_open_time > 800:
                print(f">>> HARDWARE DECISION: OPEN ({total_open} fingers)")
                self.changePage.emit(1)
                self.last_open_time = 0
            self.last_fist_time = 0

        elif decision == 0: # C++ bảo ĐÓNG AI
            if self.last_fist_time == 0:
                self.last_fist_time = now
            elif now - self.last_fist_time > 800:
                print(f">>> HARDWARE DECISION: CLOSE ({total_open} fingers)")
                self.changePage.emit(0)
                self.last_fist_time = 0
            self.last_open_time = 0
            
        else: # C++ bảo Giữ nguyên (-1)
            self.last_open_time = 0
            self.last_fist_time = 0

    def game_loop(self):
        t = QTime.currentTime().toString("hh:mm")
        d = QDate.currentDate()
        self.updateClock.emit(t, f"Ngày {d.day()}/{d.month()}/{d.year()}")

        ret, frame = self.cap.read()
        if not ret: return

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.hands.process(rgb)

        if result.multi_hand_landmarks:
            for handLms in result.multi_hand_landmarks:
                self.mpDraw.draw_landmarks(frame, handLms, self.mpHands.HAND_CONNECTIONS)
                self.detect_gesture(handLms)
        else:
            self.last_open_time = 0
            self.last_fist_time = 0

        h, w, ch = rgb.shape
        qt = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        self.img_provider.update_image(qt)
        self.imageUpdated.emit("refresh")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    provider = LiveImageProvider()
    engine = QQmlApplicationEngine()
    engine.addImageProvider("live", provider)
    backend = Backend(provider)
    engine.rootContext().setContextProperty("backend", backend)
    engine.load("interface.qml")
    sys.exit(app.exec_())