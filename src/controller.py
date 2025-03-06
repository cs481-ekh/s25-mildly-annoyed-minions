from src.ocr import OCRProcessor
from src.gui import GUI
from src.states import AppState


class AppController:
    """Controller class for the graphical application."""
    def __init__(self):
        self.gui = GUI(self)
        self.ocr_processor = OCRProcessor(self)
        self.current_state = None
        self.parsed_files = []
        self.current_file = None  # Track the current file being processed

    def set_state(self, new_state):
        """Sets the current state of the app.

        :param new_state: The new AppState of the app.
        """
        self.current_state = new_state
        self.gui.set_state(new_state)

    def process_files(self, file_paths):
        """Processes one or more files and updates the current state.

        :param file_paths: The list of files to process.
        """
        self.set_state(AppState.PROCESSING)
        failed_files = []
        self.parsed_files = []  # Clear previous results

        for file_path in file_paths:
            self.current_file = file_path  # Set current file to help with path resolution
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
        """Save the parsed files to disk.

        :return: None
        """
        if not self.parsed_files:
            self.gui.handle_error("Save Error", "No successfully parsed files to save.")
            return

        for csv_path, extracted_text in self.parsed_files:
            if csv_path and extracted_text:
                saved_path = self.ocr_processor.save_csv(csv_path, extracted_text)
                if not saved_path:
                    self.gui.handle_error("Save Error", f"Failed to save: {csv_path}")

    def run(self):
        """Start the GUI."""
        self.gui.root.mainloop()
