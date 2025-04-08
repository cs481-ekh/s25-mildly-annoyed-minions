import multiprocessing
import threading
from src.core.ocr_processor import OCRProcessor
from src.gui.gui import GUI
from src.utils.states import AppState
from src.core.image_processor import ImageProcessor


def process_pdf_worker(file_path, test_images_no_split, result_queue):
    """
    Worker function for multiprocessing.
    It calls ImageProcessor.extract_text_from_pdf with gui set to None to avoid pickling issues.
    """
    # Call the static method from ImageProcessor with gui=None.
    parsed_result = ImageProcessor.extract_text_from_pdf(file_path, test_images_no_split, None)
    result = (file_path, parsed_result) if parsed_result and all(parsed_result) else None
    result_queue.put(result)


class AppController:
    """Controller class for the graphical application."""
    def __init__(self):
        self.gui = GUI(self)
        # self.ocr_processor = OCRProcessor(self)
        self.ocr_processor = OCRProcessor()
        self.current_state = None
        self.parsed_files = []
        self.current_file = None  # Track the current file being processed
        self.manager = multiprocessing.Manager()
        self.result_queue = self.manager.Queue()

    def set_state(self, new_state):
        """Sets the current state of the app.

        :param new_state: The new AppState of the app.
        """
        self.current_state = new_state
        self.gui.set_state(new_state)

    @staticmethod
    def process_pdf(file_path, ocr_processor, result_queue):
        """Extract text from a PDF.

        :param file_path: The path to the PDF.
        :param ocr_processor: The OCRProcessor to use.
        :param result_queue: The result queue to use.
        :return: A tuple containing the file path and the OCR results.
        """
        parsed_result = ocr_processor.extract_text_from_pdf(file_path)
        result = (file_path, parsed_result) if parsed_result and all(parsed_result) else None
        result_queue.put(result)

    def process_files(self, file_paths):
        """Processes one or more files and updates the current state."""
        self.set_state(AppState.PROCESSING)
        self.parsed_files = []  # Clear previous results
        process_list = []

        # Here we use our new process_pdf_worker to avoid passing the full OCRProcessor.
        for file_path in file_paths:
            process = multiprocessing.Process(
                target=process_pdf_worker,
                args=(file_path, self.ocr_processor.test_images_no_split, self.result_queue)
            )
            process_list.append(process)
            process.start()

        threading.Thread(
            target=self.collect_results,
            args=(process_list,),
            daemon=True
        ).start()

    def collect_results(self, process_list):
        """Collect results from worker processes and update the GUI in the main thread.

        :param process_list: The list of processes to collect.
        """
        for process in process_list:
            process.join()

        failed_files = []

        while not self.result_queue.empty():
            file_path, parsed_result = self.result_queue.get()
            if parsed_result:
                self.parsed_files.append(parsed_result)
            else:
                failed_files.append(file_path)

        self.gui.root.after(0, self.update_gui_after_processing, failed_files)

    def update_gui_after_processing(self, failed_files):
        """Safely update the GUI after processing completes.

        :param failed_files: The list of failed files.
        """
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
