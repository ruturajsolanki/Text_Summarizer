import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit, 
    QFileDialog, QProgressBar, QHBoxLayout, QSizePolicy, QMessageBox, QInputDialog
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QIcon
from bs4 import BeautifulSoup
import requests
import pdfplumber
from transformers import BartForConditionalGeneration, BartTokenizer
from googletrans import Translator

class WorkerThread(QThread):
    finished = pyqtSignal(str)

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        result = self.func(*self.args, **self.kwargs)
        self.finished.emit(result)

class WebScraper(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.init_home_screen()

    def init_ui(self):
        self.setWindowTitle('Summarizer')
        self.setWindowIcon(QIcon('icon.png'))
        self.setGeometry(100, 100, 800, 600)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Title label
        self.title_label = QLabel('Welcome to the Summarizer it helps you Summarize \n                               URL, TEXT & PDF')
        self.title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(self.title_label, alignment=Qt.AlignHCenter)

        # Select option label
        self.select_label = QLabel('Select a summarizer:')
        layout.addWidget(self.select_label, alignment=Qt.AlignHCenter)

        # Option buttons layout
        options_layout = QHBoxLayout()

        # Option buttons
        self.url_summarizer_button = QPushButton('URL')
        self.url_summarizer_button.setFixedHeight(40)
        self.url_summarizer_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.url_summarizer_button.clicked.connect(self.show_url_summarizer_options)
        options_layout.addWidget(self.url_summarizer_button)

        self.text_summarizer_button = QPushButton('Text')
        self.text_summarizer_button.setFixedHeight(40)
        self.text_summarizer_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.text_summarizer_button.clicked.connect(self.show_text_summarizer_options)
        options_layout.addWidget(self.text_summarizer_button)

        self.pdf_summarizer_button = QPushButton('PDF')
        self.pdf_summarizer_button.setFixedHeight(40)
        self.pdf_summarizer_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.pdf_summarizer_button.clicked.connect(self.show_pdf_summarizer_options)
        options_layout.addWidget(self.pdf_summarizer_button)

        self.home_button = QPushButton('Home')  # New "Home" button
        self.home_button.setFixedHeight(40)
        self.home_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.home_button.clicked.connect(self.show_home_screen)
        options_layout.addWidget(self.home_button)

        layout.addLayout(options_layout)

        # Initialize sub-layouts
        self.layout_url_options = QWidget()
        self.layout_url_options.setVisible(False)
        self.layout_text_options = QWidget()
        self.layout_text_options.setVisible(False)
        self.layout_pdf_options = QWidget()
        self.layout_pdf_options.setVisible(False)

        # Add sub-layouts to main layout
        layout.addWidget(self.layout_url_options)
        layout.addWidget(self.layout_text_options)
        layout.addWidget(self.layout_pdf_options)

        self.setLayout(layout)

        # Add some style
        self.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                border: none;
                color: white;
                padding: 10px 20px;
                font-size: 13px;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #6d04b8;
            }
            QPushButton:pressed {
                background-color: #6d04b8;
            }
            QTextEdit {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 5px;
            }
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 5px;
            }
        """)

    def init_home_screen(self):
        self.home_screen = QWidget()
        self.home_screen.setWindowTitle('Home')
        self.home_screen_layout = QVBoxLayout()
        self.home_screen_label = QLabel("Let's Summarize")
        self.home_screen_label.setAlignment(Qt.AlignCenter)
        self.home_screen_layout.addWidget(self.home_screen_label)
        self.home_screen.setLayout(self.home_screen_layout)

    def show_home_screen(self):
        self.hide_option_layouts()
        QMessageBox.information(self, 'Home', "You are already on the home screen.")

    def show_url_summarizer_options(self):
        self.hide_option_layouts()
        self.layout_url_options.setVisible(True)
        self.setup_url_options()

    def show_text_summarizer_options(self):
        self.hide_option_layouts()
        self.layout_text_options.setVisible(True)
        self.setup_text_options()

    def show_pdf_summarizer_options(self):
        self.hide_option_layouts()
        self.layout_pdf_options.setVisible(True)
        self.setup_pdf_options()

    def hide_option_layouts(self):
        self.layout_url_options.setVisible(False)
        self.layout_text_options.setVisible(False)
        self.layout_pdf_options.setVisible(False)

    def setup_url_options(self):
        # Clear any existing layout content
        layout = QVBoxLayout()
        self.layout_url_options.setLayout(layout)

        # URL input
        url_layout = QHBoxLayout()
        self.url_label = QLabel('Enter URL:')
        url_layout.addWidget(self.url_label)
        self.url_input = QLineEdit()
        url_layout.addWidget(self.url_input)
        layout.addLayout(url_layout)

        # Scrape button
        self.scrape_button = QPushButton('Scrape and Summarize')
        self.scrape_button.clicked.connect(self.scrape_and_summarize)
        layout.addWidget(self.scrape_button)

        # Download button
        self.download_button = QPushButton('Download Summary')
        self.download_button.clicked.connect(self.download_summary)
        layout.addWidget(self.download_button)

        # Translate button
        self.translate_button = QPushButton('Translate Summary')
        self.translate_button.clicked.connect(self.translate_summary)
        layout.addWidget(self.translate_button)

        # Summary output
        self.summary_label = QLabel('Summary:')
        layout.addWidget(self.summary_label)

        self.summary_output = QTextEdit()
        layout.addWidget(self.summary_output)

        # Progress bar
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

    def setup_text_options(self):
        # Clear any existing layout content
        layout = QVBoxLayout()
        self.layout_text_options.setLayout(layout)

        # Text input
        text_layout = QHBoxLayout()
        self.text_label = QLabel('Enter Text:')
        text_layout.addWidget(self.text_label)
        self.text_input = QTextEdit()
        text_layout.addWidget(self.text_input)
        layout.addLayout(text_layout)

        # Scrape from text button
        self.scrape_text_button = QPushButton('Summarize Text')
        self.scrape_text_button.clicked.connect(self.summarize_text)
        layout.addWidget(self.scrape_text_button)

        # Download button
        self.download_button = QPushButton('Download Summary')
        self.download_button.clicked.connect(self.download_summary)
        layout.addWidget(self.download_button)

        # Translate button
        self.translate_button = QPushButton('Translate Summary')
        self.translate_button.clicked.connect(self.translate_summary)
        layout.addWidget(self.translate_button)

        # Summary output
        self.summary_label = QLabel('Summary:')
        layout.addWidget(self.summary_label)

        self.summary_output = QTextEdit()
        layout.addWidget(self.summary_output)

        # Progress bar
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

    def setup_pdf_options(self):
        # Clear any existing layout content
        layout = QVBoxLayout()
        self.layout_pdf_options.setLayout(layout)

        # Upload PDF button
        self.upload_pdf_button = QPushButton('Upload PDF')
        self.upload_pdf_button.clicked.connect(self.upload_pdf_and_summarize)
        layout.addWidget(self.upload_pdf_button)

        # Download button
        self.download_button = QPushButton('Download Summary')
        self.download_button.clicked.connect(self.download_summary)
        layout.addWidget(self.download_button)

        # Translate button
        self.translate_button = QPushButton('Translate Summary')
        self.translate_button.clicked.connect(self.translate_summary)
        layout.addWidget(self.translate_button)

        # Summary output
        self.summary_label = QLabel('Summary:')
        layout.addWidget(self.summary_label)

        self.summary_output = QTextEdit()
        layout.addWidget(self.summary_output)

        # Progress bar
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

    def scrape_and_summarize(self):
        url = self.url_input.text()
        if url:
            self.progress_bar.setValue(0)  # Reset progress bar
            self.progress_bar.setRange(0, 0)  # Set progress bar to indeterminate
            self.worker_thread = WorkerThread(self.scrape_and_summarize_thread, url)
            self.worker_thread.finished.connect(self.on_thread_finished)
            self.worker_thread.start()
        else:
            self.summary_output.setPlainText("Please enter a URL.")

    def scrape_and_summarize_thread(self, url):
        try:
            # Send a GET request to the URL
            response = requests.get(url)
            
            # Check if the request was successful
            if response.status_code == 200:
                # Parse the HTML content of the page using BeautifulSoup
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract text from all paragraphs on the page
                paragraphs = soup.find_all('p')
                text = ' '.join([p.get_text() for p in paragraphs])
                
                # Generate a summary of the extracted text
                summary = self.generate_summary(text)
                return summary
            else:
                return "Failed to fetch the webpage."
        except Exception as e:
            return "An error occurred: " + str(e)

    def summarize_text(self):
        text = self.text_input.toPlainText()
        if text:
            self.progress_bar.setValue(0)  # Reset progress bar
            self.progress_bar.setRange(0, 0)  # Set progress bar to indeterminate
            self.worker_thread = WorkerThread(self.generate_summary, text)
            self.worker_thread.finished.connect(self.on_thread_finished)
            self.worker_thread.start()
        else:
            self.summary_output.setPlainText("Please enter text.")

    def upload_pdf_and_summarize(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select PDF File", "", "PDF Files (*.pdf)")
        if file_path:
            self.progress_bar.setValue(0)  # Reset progress bar
            self.progress_bar.setRange(0, 0)  # Set progress bar to indeterminate
            self.worker_thread = WorkerThread(self.upload_pdf_and_summarize_thread, file_path)
            self.worker_thread.finished.connect(self.on_thread_finished)
            self.worker_thread.start()
        else:
            self.summary_output.setPlainText("Please select a PDF file.")

    def upload_pdf_and_summarize_thread(self, file_path):
        try:
            # Read the PDF file and extract text
            with pdfplumber.open(file_path) as pdf:
                text = ''
                for page in pdf.pages:
                    text += page.extract_text()

            # Generate a summary of the extracted text
            summary = self.generate_summary(text)
            return summary
        except Exception as e:
            return "An error occurred: " + str(e)

    def generate_summary(self, text):
        # Initialize BART tokenizer and model
        tokenizer = BartTokenizer.from_pretrained('facebook/bart-large-cnn')
        model = BartForConditionalGeneration.from_pretrained('facebook/bart-large-cnn')

        # Tokenize input text
        inputs = tokenizer([text], max_length=1024, return_tensors='pt', truncation=True)

        # Generate summary
        summary_ids = model.generate(inputs['input_ids'], num_beams=4, max_length=150, early_stopping=True)
        
        # Decode summary tokens back to text
        summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        
        return summary

    def on_thread_finished(self, result):
        self.progress_bar.setRange(0, 1)  # Reset progress bar range
        self.summary_output.setPlainText(result)

    def download_summary(self):
        summary = self.summary_output.toPlainText()
        if summary:
            items = ['PDF', 'Text']
            item, ok = QInputDialog.getItem(self, "Select Format", "Select a format:", items, 0, False)
            if ok and item:
                if item == 'PDF':
                    file_path, _ = QFileDialog.getSaveFileName(self, "Save PDF", "", "PDF Files (*.pdf)")
                    if file_path:
                        self.save_as_pdf(summary, file_path)
                elif item == 'Text':
                    file_path, _ = QFileDialog.getSaveFileName(self, "Save Text", "", "Text Files (*.txt)")
                    if file_path:
                        self.save_as_text(summary, file_path)
        else:
            self.summary_output.setPlainText("Please generate a summary first.")

    def save_as_pdf(self, text, file_path):
        # TODO: Implement PDF saving functionality
        pass

    def save_as_text(self, text, file_path):
        # TODO: Implement text saving functionality
        pass

    def translate_summary(self):
        summary_text = self.summary_output.toPlainText()
        if summary_text:
            # Get the destination language from the user
            language, ok_pressed = QInputDialog.getItem(self, "Select Language", "Select destination language:",
                                                    ['Hindi', 'French', 'Gujarati', 'Japanese'], 0, False)
            if ok_pressed:
                # Translate the summary into the selected language
                translator = Translator()
                translated_summary = translator.translate(summary_text, dest=language.lower())
                self.summary_output.setPlainText(translated_summary.text)
        else:
            self.summary_output.setPlainText("No summary to translate.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    scraper = WebScraper()
    scraper.show()
    sys.exit(app.exec_())
