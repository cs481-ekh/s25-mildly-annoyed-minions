from ocr import OCRProcessor
from gui import GUI
from states import AppState

class AppController:
    def __init__(self):
        self.current_state = None
        self.selected_file = None
        self.extracted_text = ""
        self.csv_files = []  # List to store CSV file paths
        self.gui = GUI(self)
        self.ocr_processor = OCRProcessor(self)

    def set_state(self, new_state, data=None):
        self.current_state = new_state
        self.gui.set_state(new_state, data)

    def process_files(self, file_paths):
        if not file_paths:
            self.gui.show_error("No file selected.")
            return

        self.csv_files = []  # Reset CSV files list
        for file_path in file_paths:
            # Call the OCRProcessor to extract text and generate CSV
            extracted_text, csv_path = self.ocr_processor.extract_text_from_pdf(file_path)
            if extracted_text:
                self.extracted_text += extracted_text + "\n"  # Append extracted text
            if csv_path:
                self.csv_files.append(csv_path)  # Append CSV file path

        # Pass the extracted text and CSV files to the GUI
        if self.csv_files:
            self.set_state(AppState.RESULTS, self.extracted_text)
        else:
            self.gui.show_error("No CSV files were generated.")

    def run(self):
        self.gui.root.mainloop()