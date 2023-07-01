import sys
import os
from PyQt6.QtWidgets import QHBoxLayout,QRadioButton, QButtonGroup,QApplication, QMainWindow, QPushButton, QLabel, QFileDialog, QComboBox, QLineEdit, QVBoxLayout, QWidget, QGridLayout, QMessageBox, QProgressBar
from PyQt6.QtCore import QThread, pyqtSignal,Qt
from moviepy.editor import VideoFileClip
from faster_whisper import WhisperModel

class AudioExtractor(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)

    def __init__(self, file_paths, output_format, output_lang, model_size):
        super().__init__()
        self.file_paths = file_paths
        self.output_format = output_format
        self.output_lang = output_lang
        self.model_size = model_size

    def run(self):
        try:
            # 加载用户选择的模型大小
            model = WhisperModel(self.model_size, device="cpu",compute_type="int8",download_root='.')
            for index, file_path in enumerate(self.file_paths):
                dir_name = os.path.dirname(file_path)
                base_name = os.path.basename(file_path)
                # 如果是视频文件，先提取音频
                if file_path.lower().endswith(('.mp4', '.avi', '.mov', '.wmv', '.flv')):
                    audio_path = os.path.splitext(file_path)[0] + '.wav'
                    self.extract_audio_from_video(file_path, audio_path)
                else:
                    audio_path = file_path

                # 获取输出格式的 writer
                segments, info = model.transcribe(audio_path, beam_size=1,language=self.output_lang)

                
                output_file_name = dir_name+'/'+os.path.splitext(base_name)[0] + '.' + self.output_format
                # print(output_file_name)
                with open(output_file_name, 'w') as file:
                    for segment in segments:
                        print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))
                        line="%s/n" % (segment.text)
                        file.write(line)
                

                # 写入转录
                

                # 更新进度条
                progress_value = (index + 1) / len(self.file_paths) * 100
                self.progress.emit(progress_value)

            self.finished.emit("success")
        except Exception as e:
            self.finished.emit(str(e))

    @staticmethod
    def extract_audio_from_video(video_path, audio_path):
        video = VideoFileClip(video_path)
        audio = video.audio
        audio.write_audiofile(audio_path)


class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QGridLayout()

        # 文件路径输入和选择
        layout.addWidget(QLabel("音频文件路径:"), 0, 0)
        self.file_paths = QLineEdit(self)
        layout.addWidget(self.file_paths, 0, 1)
        self.btn_choose = QPushButton('选择文件', self)
        self.btn_choose.clicked.connect(self.choose_file)
        layout.addWidget(self.btn_choose, 0, 2)

        # 语言选择
        layout.addWidget(QLabel("语言:"), 1, 0)
        self.language_selector = QComboBox(self)
        self.language_selector.addItems([ "zh","en"])
        layout.addWidget(self.language_selector, 1, 1)

        # 输出格式选择
        layout.addWidget(QLabel("输出格式:"), 2, 0)
        self.format_selector = QComboBox(self)
        # self.format_selector.addItems(["txt", "vtt", "srt", "tsv", "json"])
        self.format_selector.addItems(["txt"])
        layout.addWidget(self.format_selector, 2, 1)

        # 模型大小选择
        # self.radio_tiny = QRadioButton("tiny")
        # self.radio_base = QRadioButton("base")
        # self.radio_small = QRadioButton("Small")
        self.radio_medium = QRadioButton("Medium")
        # self.radio_large_v1 = QRadioButton("Large-v1")
        self.radio_large_v2 = QRadioButton("Large-v2")
        
        self.radio_medium.setChecked(True)
        radio_layout = QHBoxLayout()
        # radio_layout.addWidget(self.radio_tiny)
        # radio_layout.addWidget(self.radio_base)
        # radio_layout.addWidget(self.radio_small)
        radio_layout.addWidget(self.radio_medium)
        # radio_layout.addWidget(self.radio_large_v1)
        radio_layout.addWidget(self.radio_large_v2)
        radio_layout.addStretch()
        
        layout.addWidget(QLabel("模型大小:"), 3, 0)
        layout.addLayout(radio_layout, 3, 1, 1, 3) 

        # 转录按钮
        self.btn_transcribe = QPushButton('转录', self)
        self.btn_transcribe.clicked.connect(self.transcribe_audio)
        layout.addWidget(self.btn_transcribe, 4, 0, 1, 4)

        # 进度条
        self.progress_bar = QProgressBar(self)
        # self.progress_bar.setMaximumWidth(500)  # 设置最大宽度
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)  # 设置居中对齐
        layout.addWidget(self.progress_bar, 5, 0, 1, 4)

        # 设置布局
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.setGeometry(100, 100, 500, 200)
        self.setWindowTitle('音频转录')

    def choose_file(self):
        file_dialog = QFileDialog()
        self.file_names = file_dialog.getOpenFileNames(filter="All files (*.*);;WAV files (*.wav);;MP3 files (*.mp3);;FLAC files (*.flac);;OGG files (*.ogg);;AIFF files (*.aiff);;AAC files (*.aac);;WMA files (*.wma);;MP4 files (*.mp4);;AVI files (*.avi);;MOV files (*.mov);;WMV files (*.wmv);;FLV files (*.flv)")[0]
        self.file_paths.setText(','.join(self.file_names))

    def transcribe_audio(self):
        self.progress_bar.setRange(0, 0)
        selected_model = "medium"
        # if self.radio_tiny.isChecked():
        #     selected_model = "tiny"
        # elif self.radio_base.isChecked():
        #     selected_model = "base"
        # elif self.radio_small.isChecked():
        #     selected_model = "small"
        if self.radio_medium.isChecked():
            selected_model = "medium"
        # elif self.radio_large_v1.isChecked():
        #     selected_model = "large-v1"
        elif self.radio_large_v2.isChecked():
            selected_model = "large-v2"

        self.extractor_thread = AudioExtractor(self.file_names, self.format_selector.currentText(), self.language_selector.currentText(), selected_model)
        self.extractor_thread.progress.connect(self.update_progress)
        self.extractor_thread.finished.connect(self.on_transcription_complete)
        self.extractor_thread.start()

    def update_progress(self, progress):
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(progress)

    def on_transcription_complete(self, status):
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(1)
        if status == "success":
            QMessageBox.information(self, "成功", "转录成功！")
        else:
            QMessageBox.critical(self, "错误", status)
            self.progress_bar.setValue(0)


app = QApplication(sys.argv)
window = App()
window.show()
sys.exit(app.exec())
