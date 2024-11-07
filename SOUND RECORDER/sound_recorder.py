import sys
import os
import time
import sounddevice as sd
import numpy as np
from pydub import AudioSegment
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel, QListWidget, QListWidgetItem, QMessageBox, QStyleFactory, QLineEdit
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
import subprocess

# Set the path to FFmpeg (adjust the path to where ffmpeg.exe is located on your system)
AudioSegment.ffmpeg = "ffmpeg"  # Ensure ffmpeg is in the system path

# Global Variables
recording = None
sampling_rate = 44100  # Standard sampling rate
duration = 0  # Recording duration
is_recording = False
current_file = None
recordings = []

# File Handling
def save_audio(filename, audio_data, format='wav'):
    if format == 'mp3':
        audio_data.export(filename, format='mp3')
    else:
        audio_data.export(filename, format='wav')
    print(f"File saved as {filename}")

def delete_audio(filename):
    if os.path.exists(filename):
        os.remove(filename)
        print(f"{filename} deleted.")
    else:
        print(f"{filename} does not exist.")

def rename_audio(old_filename, new_filename):
    if os.path.exists(old_filename):
        os.rename(old_filename, new_filename)
        print(f"Renamed {old_filename} to {new_filename}")
    else:
        print(f"{old_filename} does not exist.")

def list_recordings():
    return [f for f in os.listdir('recordings') if os.path.isfile(os.path.join('recordings', f))]

# Audio Recording and Playback Logic
def record_audio():
    global recording, is_recording, duration, current_file
    if is_recording:
        print("Recording in progress...")
        return
    is_recording = True
    duration = 0
    print("Recording started...")
    recording = []
    
    def callback(indata, frames, time, status):
        if status:
            print(status)
        recording.append(indata.copy())
    
    sd.InputStream(callback=callback, channels=1, samplerate=sampling_rate, dtype='int16').start()
    return recording

def stop_recording():
    global recording, is_recording, current_file, recordings
    if not is_recording:
        print("No active recording.")
        return
    is_recording = False
    print("Recording stopped.")
    
    # Convert numpy array to pydub audio segment
    audio_data = np.concatenate(recording, axis=0)
    audio_segment = AudioSegment(
        audio_data.tobytes(),
        frame_rate=sampling_rate,
        sample_width=2,  # Assuming 16-bit audio (2 bytes)
        channels=1
    )
    
    current_file = f"recordings/recording_{int(time.time())}.wav"
    save_audio(current_file, audio_segment, format='wav')
    recordings.append(current_file)

# GUI with PyQt5
class SoundRecorderApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_recordings()
        
    def init_ui(self):
        self.setWindowTitle("Sound Recorder")
        self.setGeometry(100, 100, 600, 400)
        self.setWindowIcon(QIcon('microphone.png'))
        self.setStyleSheet("""
            QWidget {
                background-color: #282c34;
                color: #c4c4c4;
                font-family: 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
            }
            QPushButton {
                background-color: #3c3f4a;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #4b4f5a;
            }
            QLabel {
                font-size: 16px;
            }
            QListWidget {
                background-color: #3c3f4a;
                border: none;
            }
            QListWidget::item {
                padding: 6px 12px;
            }
            QListWidget::item:selected {
                background-color: #4b4f5a;
            }
            QLineEdit {
                background-color: #3c3f4a;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
            }
        """)
        
        layout = QVBoxLayout()
        
        self.status_label = QLabel("Welcome to the Sound Recorder!", self)
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        self.record_button = QPushButton("Start Recording", self)
        self.record_button.clicked.connect(self.toggle_recording)
        layout.addWidget(self.record_button)
        
        self.play_button = QPushButton("Play Selected Recording", self)
        self.play_button.clicked.connect(self.play_selected_recording)
        layout.addWidget(self.play_button)
        
        self.delete_button = QPushButton("Delete Selected Recording", self)
        self.delete_button.clicked.connect(self.delete_selected_recording)
        layout.addWidget(self.delete_button)
        
        self.rename_label = QLabel("Rename Recording:")
        layout.addWidget(self.rename_label)
        
        self.rename_input = QLineEdit()
        self.rename_input.returnPressed.connect(self.rename_recording)
        layout.addWidget(self.rename_input)
        
        self.recordings_list = QListWidget(self)
        self.recordings_list.itemDoubleClicked.connect(self.play_selected_recording)
        layout.addWidget(self.recordings_list)
        
        self.setLayout(layout)
    
    def toggle_recording(self):
        if is_recording:
            stop_recording()
            self.record_button.setText("Start Recording")
            self.status_label.setText(f"Recording saved as {current_file}")
            self.load_recordings()
        else:
            record_audio()
            self.record_button.setText("Stop Recording")
            self.status_label.setText("Recording in progress...")
    
    def play_selected_recording(self):
        if self.recordings_list.currentItem():
            filename = self.recordings_list.currentItem().text()
            file_path = os.path.join("recordings", filename)
            if os.path.exists(file_path):
                try:
                    # Updated: Removed shell=True
                    subprocess.Popen(["ffplay", "-nodisp", "-autoexit", file_path])
                    self.status_label.setText(f"Playing {filename}")
                except FileNotFoundError:
                    self.status_label.setText("Error: 'ffplay' not found. Please ensure FFmpeg is installed and in the system path.")
                except Exception as e:
                    self.status_label.setText(f"Error playing {filename}: {str(e)}")
            else:
                self.status_label.setText("File not found.")
        else:
            self.status_label.setText("No recording selected.")
    
    def delete_selected_recording(self):
        if self.recordings_list.currentItem():
            filename = self.recordings_list.currentItem().text()
            file_path = os.path.join("recordings", filename)
            delete_audio(file_path)
            self.load_recordings()
            self.status_label.setText(f"{filename} deleted.")
        else:
            self.status_label.setText("No recording selected.")
    
    def rename_recording(self):
        if self.recordings_list.currentItem():
            old_filename = self.recordings_list.currentItem().text()
            new_filename = f"recordings/{self.rename_input.text()}.wav"
            rename_audio(f"recordings/{old_filename}", new_filename)
            self.load_recordings()
            self.status_label.setText(f"Renamed {old_filename} to {self.rename_input.text()}.wav")
            self.rename_input.clear()
        else:
            self.status_label.setText("No recording selected.")
    
    def load_recordings(self):
        self.recordings_list.clear()
        recordings = list_recordings()
        for recording in recordings:
            item = QListWidgetItem(recording)
            item.setIcon(QIcon('microphone.png'))
            self.recordings_list.addItem(item)

# Main function to run the app
if __name__ == '__main__':
    # Ensure the recordings folder exists
    if not os.path.exists('recordings'):
        os.makedirs('recordings')

    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create('Fusion'))
    window = SoundRecorderApp()
    window.show()
    sys.exit(app.exec_())
