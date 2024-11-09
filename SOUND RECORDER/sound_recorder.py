import sys
import os
import time
import sounddevice as sd
import numpy as np
from pydub import AudioSegment
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel, 
    QListWidget, QListWidgetItem, QStyleFactory, QLineEdit, QHBoxLayout
)
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt
import subprocess

# Set the path to FFmpeg (adjust the path if necessary)
AudioSegment.ffmpeg = "ffmpeg"  # Ensure ffmpeg is in the system path

# Global Variables
recording = None
sampling_rate = 44100
duration = 0
is_recording = False
current_file = None
recordings = []

# File Handling
def save_audio(filename, audio_data, format='wav'):
    audio_data.export(filename, format=format)
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

# Audio Conversion
def convert_to_mp3(input_file):
    try:
        audio = AudioSegment.from_file(input_file)
        output_file = os.path.splitext(input_file)[0] + ".mp3"
        audio.export(output_file, format="mp3")
        print(f"File converted to MP3 and saved as {output_file}")
        return output_file
    except Exception as e:
        print(f"Error converting file: {e}")
        return None

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
    
    audio_data = np.concatenate(recording, axis=0)
    audio_segment = AudioSegment(
        audio_data.tobytes(),
        frame_rate=sampling_rate,
        sample_width=2,
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
        self.setGeometry(100, 100, 600, 500)
        self.setWindowIcon(QIcon('microphone.png'))



        self.setStyleSheet("""
            QWidget {
                background-color: #0E5200;
                color: #c4c4c4;
                font-family: 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
            }
            QPushButton {
                background-color: #2C701E;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size : 30px
            }
            QPushButton:hover {
                background-color: #4B4F5A;
            }
            QLabel {
                font-size: 30px;
            }
            QListWidget {
                background-color: #2C701E;
                border: none;
                font-size: 20px;
            }
            QListWidget::item {
                padding: 6px 12px;
            }
            QListWidget::item:selected {
                background-color: #4b4f5a;
            }
            QLineEdit {
                background-color: #2C701E;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 20px
            }
        """)
        
        layout = QVBoxLayout()
        
        self.status_label = QLabel("Welcome to the Sound Recorder!", self)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 40px; font-weight: bold;")
        layout.addWidget(self.status_label)

        control_layout = QHBoxLayout()
        
        self.record_button = QPushButton("Start Recording", self)
        self.record_button.clicked.connect(self.toggle_recording)
        control_layout.addWidget(self.record_button)
        
        self.play_button = QPushButton("Play Selected Recording", self)
        self.play_button.clicked.connect(self.play_selected_recording)
        control_layout.addWidget(self.play_button)
        
        self.delete_button = QPushButton("Delete Selected Recording", self)
        self.delete_button.clicked.connect(self.delete_selected_recording)
        control_layout.addWidget(self.delete_button)
        
        self.convert_button = QPushButton("Convert to MP3", self)
        self.convert_button.clicked.connect(self.convert_selected_to_mp3)
        control_layout.addWidget(self.convert_button)
        
        layout.addLayout(control_layout)

        self.select_file_button = QPushButton("Select File to Convert to MP3")
        self.select_file_button.clicked.connect(self.select_file_to_convert)
        layout.addWidget(self.select_file_button)

        self.rename_label = QLabel("Rename Recording:")
        self.rename_label.setAlignment(Qt.AlignCenter)
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
                    subprocess.Popen(["ffplay", "-nodisp", "-autoexit", file_path])
                    self.status_label.setText(f"Playing {filename}")
                except FileNotFoundError:
                    self.status_label.setText("Error: 'ffplay' not found.")
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

    def convert_selected_to_mp3(self):
        if self.recordings_list.currentItem():
            filename = self.recordings_list.currentItem().text()
            file_path = os.path.join("recordings", filename)
            mp3_file = convert_to_mp3(file_path)
            if mp3_file:
                self.status_label.setText(f"Converted {filename} to MP3.")
            else:
                self.status_label.setText("Error converting to MP3.")
        else:
            self.status_label.setText("No recording selected.")

    def select_file_to_convert(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Audio File to Convert", "", "Audio Files (*.wav *.ogg *.flac *.mp4 *.m4a *.aac)")
        if file_path:
            mp3_file = convert_to_mp3(file_path)
            if mp3_file:
                self.status_label.setText(f"Converted {os.path.basename(file_path)} to MP3.")
            else:
                self.status_label.setText("Error converting file to MP3.")

# Main function to run the app
if __name__ == '__main__':
    if not os.path.exists('recordings'):
        os.makedirs('recordings')

    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create('Fusion'))
    window = SoundRecorderApp()
    window.show()
    sys.exit(app.exec_())
