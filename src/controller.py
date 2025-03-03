from src.ocr import OCRProcessor
from src.gui import GUI
from src.states import AppState

class AppController:
    def __init__(self):
        self.gui = GUI(self)
        self.ocr_processor = OCRProcessor(self)
        self.current_state = None
        self.parsed_files = []

    def set_state(self, new_state):
        self.current_state = new_state
        self.gui.set_state(new_state)

    def process_files(self, file_paths):
        self.set_state(AppState.PROCESSING)
        failed_files = []

        for file_path in file_paths:
            parsed_result = self.ocr_processor.extract_text_from_pdf(file_path)

            if parsed_result is None or not all(parsed_result):
                failed_files.append(file_path)
                continue  # Skip to next file

            csv_path, extracted_text = parsed_result
            self.parsed_files.append((csv_path, extracted_text))

        if failed_files:
            failed_message = "\n".join(failed_files)
            self.gui.handle_error("Processing Error", f"Some files failed:\n{failed_message}")

        self.set_state(AppState.RESULTS)

    def save_parsed_files(self):
        if not self.parsed_files:
            self.gui.handle_error("Save Error", "No successfully parsed files to save.")
            return

        for csv_path, extracted_text in self.parsed_files:
            if csv_path and extracted_text:
                saved_path = self.ocr_processor.save_csv(extracted_text, csv_path)
                if not saved_path:
                    self.gui.handle_error("Save Error", f"Failed to save: {csv_path}")

    def run(self):
        self.gui.root.mainloop()