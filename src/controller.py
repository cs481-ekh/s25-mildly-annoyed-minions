from ocr import OCRProcessor
from gui import GUI
from states import AppState

class AppController:
    def __init__(self):
        self.current_state = None
        self.selected_file = None
        self.extracted_text = ""
        self.gui = GUI(self)
        self.ocr_processor = OCRProcessor(self)

    def set_state(self, new_state, data=None):
        self.current_state = new_state
        self.gui.set_state(new_state, data)

    # def open_file(self, file_path):
    #     print(f"Opening file: {file_path}")
    #     self.set_state(AppState.PROCESSING)
    #     self.process_ocr(file_path)

    def process_files(self, file_paths):
        if not file_paths:
            self.gui.show_error("No file selected.")
            return

        for file_path in file_paths:
            extracted_text = self.ocr_processor.extract_text_from_pdf(file_path)
            self.extracted_text = extracted_text

        self.set_state(AppState.RESULTS, self.extracted_text)

    def run(self):
        self.gui.root.mainloop()
        self.gui.root.update_idletasks()
        self.gui.root.update()
        self.gui.root.quit()