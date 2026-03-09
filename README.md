# 🏋️‍♂️ SmartCoach Production System

## 📖 Overview
SmartCoach is an AI-powered fitness tracking system that monitors user posture using Deep Learning (Mediapipe) and tracks physiological data (Heart Rate via Fitbit & Muscle Activity via EMG sensors).

## 🏗️ Architecture
- **Data Collection:** ESP32 (EMG Sensor), Fitbit Versa 4 (Web API), PC Camera (Mediapipe AI).
- **Backend API:** FastAPI, Python, Custom Idempotency Pipeline to prevent data duplication.
- **Database:** Serverless PostgreSQL hosted on **Neon.tech Cloud** (Features built-in Connection Pooling & SSL).
- **Infrastructure:** Docker, Docker Compose, & Bash Automation Scripts.
- **Frontend / UI:** Streamlit (Real-time Web Dashboard) & Flutter (Mobile App connected via Ngrok).

## 🚀 How to Run

### Option 1: The Automated Way (Recommended for Local Dev)
We created a master bash script that launches the entire ecosystem (API, Dashboard, AI Camera, Fitbit Tracker, and Ngrok Tunnel) in the background with a single command.

1. Clone the repository and open the workspace.
2. Make the script executable (first time only):
   chmod +x run_system.sh
3. Run the complete system:
   ./run_system.sh

### Option 2: The Production Way (Docker)
For cloud deployment or running isolated containers:
docker-compose up --build -d

## 📂 Project Structure
- `api.py`: The main FastAPI application.
- `db_manager.py`: Brain of the database (Cloud connection, Upsert logic).
- `run_system.sh`: The master execution script.
- `docker-compose.yml`: Infrastructure containerization setup.