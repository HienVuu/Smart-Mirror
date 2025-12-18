# Smart Mirror: Hardware-Software Co-design Implementation
## Project Overview
This project implements a Smart Mirror system utilizing a Hardware-Software Co-design architecture. The system integrates high-level software processing for computer vision and natural language understanding with low-level hardware simulation for critical control logic. The project demonstrates the interoperability between Python (Host Application) and C++/SystemC (Hardware Logic Simulation).

## System Architecture
The system operates on a co-simulation model comprising two main layers:

Host Application (Python): Handles data acquisition from sensors (camera, microphone), executes heavy-duty algorithms (MediaPipe for hand tracking, Google Gemini for NLP), manages external API communications (OpenWeatherMap, RSS), and renders the graphical user interface (QtQuick/QML).

Logic Accelerator (C++/SystemC):

Gesture Decision Module: Accepts raw tracking data from the host and executes threshold comparison logic to determine control states (ON/OFF).

Hardware Timer Module: Simulates a hardware clock counter to manage timing sequences for the image capture functionality.

## Features
Multimodal Interaction: Supports both voice commands (Vietnamese) and hand gesture recognition.

AI Integration: Incorporates Google Gemini LLM for context-aware conversational assistance.

Real-time Information: Displays synchronized clock, weather conditions (temperature, humidity, AQI), and news updates.

Hardware-in-the-loop Simulation: Utilizing external C++ executables to validate logic control independent of the main software loop.

## Prerequisites
To ensure system stability, the following environment configurations are strictly required:

Python Version: Python 3.10 (Required for MediaPipe compatibility).

Compiler: GCC/G++ (MinGW for Windows or build-essential for Linux).

Hardware: Raspberry Pi 4 Model B or Standard Laptop (x86_64).

Peripherals: USB Webcam and Microphone.

## Installation Guide for Win/Linux
1. Environment Setup
It is recommended to use Conda to manage the specific Python version required.

conda create -n mirror python=3.10 -y
conda activate mirror

2. Dependency Installation
Install the required Python packages. Note that specific versions of mediapipe and protobuf are enforced to prevent compatibility issues.

pip install -r requirements.txt

3. Hardware Module Compilation
The logic modules must be compiled before running the main application.
For Windows (Simulation Mode):
g++ hand_decision.cpp -o hand_decision
g++ camera_timer.cpp -o camera_timer

For Linux / Raspberry Pi (SystemC Mode): Ensure the SystemC library is installed in the standard path or update the include paths accordingly.
g++ -I. -I/usr/local/systemc-2.3.3/include -L. -L/usr/local/systemc-2.3.3/lib-linux64 -o hand_decision hand_decision.cpp -lsystemc -lm

4. Configuration
Open main.py and update the following constants with your valid API keys:
WEATHER_API_KEY = "YOUR_OPENWEATHERMAP_API_KEY"
GEMINI_API_KEY = "YOUR_GOOGLE_GEMINI_API_KEY"
CITY = "Hanoi"

## Installation Guide for Raspberry Pi 4
This section outlines specific configurations required when deploying the system on a Raspberry Pi 4 Model B (ARM64 architecture).

1. Operating System Requirement
The Raspberry Pi OS (64-bit) is strictly required. The MediaPipe library does not support the legacy 32-bit architecture.

Recommended Image: Raspberry Pi OS with desktop (64-bit).
2. System Dependencies
Before installing Python packages, essential system-level libraries for audio and image processing must be installed via APT.

 sudo apt update
sudo apt install -y python3-pyaudio portaudio19-dev libgl1-mesa-glx libhdf5-dev libatlas-base-dev

3. Re-compilation of Logic Modules
Executables compiled on Windows (x86) are not compatible with Raspberry Pi (ARM). The C++ logic modules must be re-compiled natively on the device.

Navigate to the project directory and run:

# Remove old Windows executables if present
rm *.exe

# Compile the gesture decision module
g++ hand_decision.cpp -o hand_decision

# Compile the timer module (if available)
g++ camera_timer.cpp -o camera_timer

## Usage Instructions
Run the main application entry point:

python main.py

Operational Logic
Gesture Control:

Open Hand (5 fingers): Triggers the Logic Accelerator to return a high signal (1), activating the AI interface.

Closed Fist (0-1 finger): Triggers the Logic Accelerator to return a low signal (0), deactivating the AI interface.

Voice Control:

Activate the system using commands such as "Thoi tiet" (Weather), "Tin tuc" (News), or natural language questions.

Command "Chup anh" (Take photo) initiates the hardware timer sequence.

## Project Structure
main.py: Main entry point and Host Application logic.

interface.qml: User Interface definition using QtQuick.

hand_decision.cpp: Source code for the gesture logic comparator.

camera_timer.cpp: Source code for the hardware timer simulation.

requirements.txt: List of Python dependencies.

photos/: Output directory for captured images.

## Troubleshooting
Issue: AttributeError: module 'mediapipe' has no attribute 'solutions'

Cause: Incompatibility between the installed Python version and MediaPipe/Protobuf libraries.

Resolution: Verify that the Python environment is version 3.10. Reinstall dependencies using the exact versions specified in requirements.txt.

Issue: SystemC Executable Not Found

Cause: The C++ modules have not been compiled, or the operating system is not detecting the output file.

Resolution: Revisit the Hardware Module Compilation step and ensure the output files (hand_decision.exe on Windows or hand_decision on Linux) exist in the root directory.
