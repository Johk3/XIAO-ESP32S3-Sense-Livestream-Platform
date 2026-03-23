# ESP32S3 Sense Automated Dashcam & Web Streamer

This project turns your ESP32S3 Sense module into a fully reliable automated web streamer and local SD card recording camera. It uses a standalone hardware approach coupled with an automated Python helper script to convert all of your SD card footage from images to video.

This project derives majority of its code from [Limengdu](https://github.com/limengdu/SeeedStudio-XIAO-ESP32S3-Sense-camera/tree/main).

## Features

1. **Simple High-Res Web Stream:** Browse directly to the ESP32's IP address to watch its active 1600x1200 feed without any chunky UI.
2. **Robust Multi-Tasking 24/7:** A dedicated background script runs autonomously on the MCU, constantly capturing 1600x1200 frames and pushing them onto the SD card securely. 
3. **Structured Storage System:** Automatically writes images natively categorized by year/month/day/hour using NTP Time synchronization to keep accurate internal clocks automatically. Loss of battery gracefully drops it back right into sync.
4. **Auto-Video USB Extraction:** The companion script `auto_video_converter.py` is actively watching for USB drive insertions constantly. Simply plug your ESP32's SD card back into the computer, and the software compiles any new `.jpg` streams into distinct MP4 videos.

## Setup Instructions

### 1. Arduino Configuration (Hardware Setup)

1. Open `CameraWebServer_for_esp-arduino_3.0.x.ino` in your Arduino IDE.
2. Edit the `secrets.h` file located in the same directory (`CameraWebServer_for_esp-arduino_3.0.x`) and enter your Wi-Fi credentials to allow for network streaming and NTP time-syncing operations:
    ```cpp
    const char* WIFI_SSID = "your_wifi_here";
    const char* WIFI_PASSWORD = "your_password_here";
    ```
3. Make sure you select "XIAO_ESP32S3" settings, plug your module in via USB, compile, and upload to the board! 
   - **Important:** Ensure you have OPI PSRAM completely enabled in the Arduino IDE tools menu.

### 2. Python Configuration (Software Data Processing Setup)

The python companion automation script `auto_video_converter.py` enables automatic, lossless compilation of USB image trails into actual watchable MP4 videos instantly anytime you inject an SD card reader.

To run it:
1. Make sure Python 3.x is installed on your Linux / PC OS.
2. Ensure you have FFmpeg installed on your OS:
   ```bash
   sudo apt update
   sudo apt install ffmpeg
   ```
3. Install the specific python dependencies inside this folder matching the `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```
4. Adjust your output settings natively by editing the `.env` file created in this directory:
   ```env
   # Set this to where you want the videos to permanently live
   OUTPUT_DIR=~/Documents/Camera_Videos
   # The framerate you want the reconstruct videos to be at
   FPS=10
   ```
5. Simply leave the application actively watching via your terminal:
   ```bash
   python3 auto_video_converter.py
   ```
   > You can keep this fully running in the background all the time. Whenever it detects your exact ESP32 file architecture signature on an inserted USB block, it will kick into action
