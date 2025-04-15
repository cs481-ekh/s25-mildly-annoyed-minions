import multiprocessing
import threading
from multiprocessing import Queue
from src.utils.states import AppState
from src.ocr import OCRProcessor, process_pdf_worker
from src.gui.gui import GUI


class AppController:
    """Controller class for the graphical application."""

    def __init__(self):
        self.gui = GUI(self)
        self.current_state = None
        self.parsed_files = []
        self.current_file = None  # Track the current file being processed
        self.manager = multiprocessing.Manager()
        self.result_queue: Queue = self.manager.Queue()

    def set_state(self, new_state):
        """Sets the current state of the app."""
        self.current_state = new_state
        self.gui.set_state(new_state)

    def process_files(self, file_paths):
        """Processes one or more files using multiprocessing."""
        self.set_state(AppState.PROCESSING)
        self.parsed_files = []  # Clear previous results

        process_list = []

        for file_path in file_paths:
            process = multiprocessing.Process(
                target=process_pdf_worker,
                args=(file_path, self.result_queue)
            )
            process_list.append(process)
            process.start()

        threading.Thread(
            target=self.collect_results,
            args=(process_list,),
            daemon=True
        ).start()

    def collect_results(self, process_list):
        """Collect results from worker processes and update the GUI."""
        for process in process_list:
            process.join()

        failed_files = []

        while not self.result_queue.empty():
            result = self.result_queue.get()
            if result:
                file_path, parsed_result = result
                if parsed_result:
                    self.parsed_files.append((file_path, parsed_result))
                else:
                    failed_files.append(file_path)

        self.gui.root.after(0, self.update_gui_after_processing, failed_files)

    def update_gui_after_processing(self, failed_files):
        if failed_files:
            failed_message = "\n".join(failed_files)
            self.gui.handle_error("Processing Error", f"Some files failed:\n{failed_message}")
        self.set_state(AppState.RESULTS)

    def save_parsed_files(self):
        if not self.parsed_files:
            self.gui.handle_error("Save Error", "No successfully parsed files to save.")
            return

        ocr_processor = OCRProcessor(master=self)

        for csv_path, extracted_text in self.parsed_files:
            if csv_path and extracted_text:
                saved_path = ocr_processor.save_csv(csv_path, extracted_text)
                if not saved_path:
                    self.gui.handle_error("Save Error", f"Failed to save: {csv_path}")

    def run(self):
        self.gui.root.mainloop()
