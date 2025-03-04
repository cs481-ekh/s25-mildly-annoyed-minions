from src.ocr import OCRProcessor
from src.gui import GUI
from src.states import AppState


class AppController:
    def __init__(self):
        self.gui = GUI(self)
        self.ocr_processor = OCRProcessor(self)
        self.current_state = None
        self.parsed_files = []
        self.current_file = None  # Track the current file being processed

    def set_state(self, new_state):
        self.current_state = new_state
        self.gui.set_state(new_state)

    def process_files(self, file_paths):
        self.set_state(AppState.PROCESSING)
        failed_files = []
        self.parsed_files = []  # Clear previous results

        for file_path in file_paths:
            self.current_file = file_path  # Set current file to help with path resolution
            print(f"Processing file: {file_path}")  # Debug statement
            parsed_result = self.ocr_processor.extract_text_from_pdf(file_path)

            if parsed_result is None or not all(parsed_result):
                print(f"Failed to process file: {file_path}")  # Debug statement
                failed_files.append(file_path)
                continue  # Skip to next file

            csv_path, parsed_data = parsed_result
            self.parsed_files.append((csv_path, parsed_data))
            print(f"Successfully processed file: {file_path}, parsed data: {parsed_data}")  # Debug statement

        if failed_files:
            failed_message = "\n".join(failed_files)
            self.gui.handle_error("Processing Error", f"Some files failed:\n{failed_message}")

        if not self.parsed_files:
            self.gui.handle_error("Processing Error", "No files were successfully processed.")
            return

        self.set_state(AppState.RESULTS)

    def save_parsed_files(self):
        if not self.parsed_files:
            self.gui.handle_error("Save Error", "No successfully parsed files to save.")
            return

        for csv_path, parsed_data in self.parsed_files:
            if csv_path and parsed_data:
                saved_path = self.ocr_processor.save_csv(csv_path, parsed_data)
                if not saved_path:
                    self.gui.handle_error("Save Error", f"Failed to save: {csv_path}")

    def run(self):
        self.gui.root.mainloop()