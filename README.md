# Gaze Tracking Experiment

This project is designed for **web-based eye tracking data collection**.  
Participants are tracked in the browser using **WebGazer.js**, and gaze data is sent to a Python **Flask** backend for secure storage.  

## 🚀 Installation

```bash
git clone https://github.com/username/Gaze-Tracking-Experiment.git
cd Gaze-Tracking-Experiment
pip install -r requirements.txt
```

## ▶️ Running the Application

```bash
python app.py
```

Then open your browser at: `http://127.0.0.1:5000`  

## 📂 Data Structure

- A separate CSV file is created for each participant under the `data/` directory.  
- CSV format:  
  ```
  t, x, y
  12345, 250, 320
  12346, 252, 318
  ...
  ```
- Data is stored in **CSV format** for easy offline analysis (Python, R, MATLAB, etc.).  

## 📌 Features

- Webcam-based eye tracking using **WebGazer.js**  
- Calibration protocol to improve accuracy  
- Flask backend for secure data management  
- Separate CSV storage for each participant  

## 📖 References

- [WebGazer.js](https://webgazer.cs.brown.edu/)  
- [Flask](https://flask.palletsprojects.com/)  
