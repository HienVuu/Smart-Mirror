import QtQuick 2.12
import QtQuick.Controls 2.12
import QtQuick.Window 2.12
import QtGraphicalEffects 1.12

ApplicationWindow {
    visible: true
    width: 1024
    height: 600
    color: "black"
    title: "Smart Mirror - SystemC Intergrated"

    // -------------------------------
    // 1. Nền Camera
    // -------------------------------
    Image {
        id: cameraFeed
        anchors.fill: parent
        fillMode: Image.PreserveAspectCrop
        cache: false
        opacity: 0.30
    }

    // -------------------------------
    // 2. Đồng hồ
    // -------------------------------
    Item {
        anchors.top: parent.top
        anchors.right: parent.right
        anchors.margins: 30
        width: 300
        height: 150

        Column {
            anchors.right: parent.right

            Text {
                id: timeText
                text: "00:00"
                color: "white"
                font.pixelSize: 90
                font.bold: true
                style: Text.Outline
                styleColor: "black"
            }

            Text {
                id: dateText
                text: "--/--/----"
                color: "#CCCCCC"
                font.pixelSize: 24
            }
        }
    }

    // -------------------------------
    // 3. Thời tiết
    // -------------------------------
    Item {
        id: weatherBox
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.margins: 30
        width: 350
        height: 150

        Row {
            spacing: 20
            anchors.verticalCenter: parent.verticalCenter

            // ICON thời tiết
            Image {
                id: weatherIcon
                width: 90
                height: 90
                fillMode: Image.PreserveAspectFit
                source: "weather/01d.png"   // ảnh mặc định hoặc placeholder
            }

            Column {
                anchors.verticalCenter: parent.verticalCenter

                Text {
                    id: tempText
                    text: "--°C"
                    color: "white"
                    font.pixelSize: 60
                    font.bold: true
                }

                Text {
                    id: weatherDesc
                    text: "Đang tải dữ liệu..."
                    color: "#DDDDDD"
                    font.pixelSize: 22
                    width: 200
                    wrapMode: Text.WordWrap
                }
            }
        }
    }

    // -------------------------------
    // 4. KHUNG TRỢ LÝ AI (SWIPE VIEW)
    // -------------------------------
    SwipeView {
        id: swipeView
        anchors.centerIn: parent
        width: 700
        height: 300
        interactive: false // Không cho quẹt tay, chỉ đổi bằng code
        currentIndex: 0
        clip: true

        // Trang 0: Trống (để nhìn gương)
        Item { } 

        // Trang 1: Hiển thị AI / Thông báo hệ thống
        Item {
            Rectangle {
                anchors.fill: parent
                color: "#CC000000"
                radius: 20
                border.color: "cyan"
                border.width: 2

                Column {
                    anchors.centerIn: parent
                    width: parent.width - 40

                    Text {
                        text: "HỆ THỐNG THÔNG MINH"
                        color: "cyan"
                        font.pixelSize: 28
                        font.bold: true
                        anchors.horizontalCenter: parent.horizontalCenter
                    }

                    ScrollView {
                        width: parent.width
                        height: 200

                        TextArea {
                            id: aiResponseText
                            text: "Xin chào! Bạn cần giúp gì?"
                            color: "white"
                            font.pixelSize: 24
                            wrapMode: Text.WordWrap
                            background: null
                            readOnly: true
                        }
                    }
                }
            }
        }
    }

    // -------------------------------
    // 5. Thanh tin tức chạy
    // -------------------------------
    Rectangle {
        id: newsBar
        width: parent.width
        height: 40
        anchors.bottom: parent.bottom
        color: "#AA000000"

        Text {
            id: newsText
            text: "Đang tải tin tức..."
            color: "#00FF00"
            font.pixelSize: 20
            anchors.verticalCenter: parent.verticalCenter

            x: newsBar.width
            NumberAnimation on x {
                from: newsBar.width
                to: -newsText.width
                duration: 20000
                loops: Animation.Infinite
                running: true
            }
        }
    }

    // -------------------------------
    // 6. Trạng thái giọng nói
    // -------------------------------
    Text {
        id: voiceStatusText
        text: "🎤 Sẵn sàng"
        color: "yellow"
        font.pixelSize: 18
        anchors.bottom: newsBar.top
        anchors.bottomMargin: 10
        anchors.horizontalCenter: parent.horizontalCenter
        style: Text.Outline
        styleColor: "black"
    }

    // -------------------------------
    // 7. BẮT TÍN HIỆU TỪ PYTHON (BACKEND)
    // -------------------------------
    Connections {
        target: backend

        // Cập nhật ảnh camera
        function onImageUpdated(msg) {
            cameraFeed.source = "image://live/frame" + Math.random()
        }

        // Cập nhật đồng hồ
        function onUpdateClock(t, d) {
            timeText.text = t
            dateText.text = d
        }

        // Cập nhật thời tiết
        function onUpdateWeather(tempIconStr, descIconStr) {
            var parts = descIconStr.split("|")
            var desc = parts[0]
            var icon = parts[1]

            tempText.text = tempIconStr
            weatherDesc.text = desc
            weatherIcon.source = "weather/" + icon + ".png"
        }

        // Cập nhật tin tức
        function onUpdateNews(news) { 
            newsText.text = news 
        }

        // Cập nhật nội dung AI / Thông báo SystemC
        function onUpdateAI(response) {
            aiResponseText.text = response
            swipeView.currentIndex = 1
        }

        // Đổi trang (0: Ẩn, 1: Hiện)
        function onChangePage(idx) {
            swipeView.currentIndex = idx
        }

        // Trạng thái giọng nói
        function onUpdateVoiceStatus(s) {
            voiceStatusText.text = s
        }
    }
}