# **Web-Based Eye Tracking for Dynamic Attention Map Generation**

This project is an end-to-end integrated system that uses a standard webcam to collect participants' eye-tracking data in response to dynamic video stimuli and generates collective attention maps (saliency maps) from this data. The research aims to provide an accessible and scalable methodology that does not require special hardware.

This repository contains the source code for the software used in the scientific work titled: \[article title\].

### **✨ Key Features**

* **Web-Based Data Collection:** Participants can join the experiment through any modern web browser.  
* **Hardware-Independent:** It only requires a standard webcam.  
* **Interactive Calibration and Validation:** It includes click-based calibration and quantitative validation steps inspired by GazeRecorder for high data accuracy.  
* **Automatic Test Management:** It automatically organizes data for each participant and test session, preventing overwrites.  
* **Dynamic Heatmap Generation:** It creates time-varying attention maps, which are overlaid onto the video, from the collected collective data.  
* **Multiple Test Support:** It processes the results of different test groups (e.g., test1, test2) separately, allowing for comparison.

### **📂 Project Structure**

.  
├── static/  
│   ├── webgazer.js     \# Eye-tracking library  
│   └── video.mp4       \# Sample video to be used in the experiment  
├── templates/  
│   └── index.html      \# The web interface seen by the participant  
├── app.py              \# Data collection server (Flask)  
├── process\_gaze.py     \# Data processing and heatmap generation script  
├── requirements.txt    \# Required Python libraries  
└── README.md           \# This file

### **🚀 Setup and Usage**

Follow the steps below to run this project on your computer.

#### **1\. Prerequisites**

* [Python 3.9](https://www.python.org/downloads/) or higher  
* [Git](https://git-scm.com/downloads/)

#### **2\. Installation**

Bash  
\# 1\. Clone the project repository  
git clone https://github.com/your-username/Gaze-Heatmap-Generator.git  
cd Gaze-Heatmap-Generator

\# 2\. Create and activate a virtual environment (Recommended)  
python \-m venv venv  
\# For Windows:  
venv\\Scripts\\activate  
\# For macOS/Linux:  
source venv/bin/activate

\# 3\. Install the required Python libraries  
pip install \-r requirements.txt

#### **3\. Usage**

The project consists of two main stages: Data Collection and Data Processing.

**Stage 1: Data Collection**

1. Save the video you will use in the experiment as `static/video.mp4`.  
2. Start the data collection server with the following command: `python app.py`.  
3. Open a web browser and go to `http://127.0.0.1:5000`.  
4. You can add a parameter to the URL to specify a participant ID, for example: `http://127.0.0.1:5000/?pid=ali`.  
5. Follow the instructions on the interface to complete the experiment. The collected data will be saved to the `data/` folder, which is created automatically in the project's root directory.

**Stage 2: Data Processing and Heatmap Generation**

1. After the data collection is complete, run the following command to generate the attention map video: `python process_gaze.py`.  
2. The script will automatically find all test groups in the `data/` folder and generate a separate video for each.  
3. The resulting videos will be saved to the `results/` folder, which is created automatically in the project's root directory, with names like `heatmap_video_test1.mp4`, `heatmap_video_test2.mp4`, etc..

### **📄 Citation**

### **⚖️ License**

This project is licensed under the MIT License. See the `LICENSE` file for details.

