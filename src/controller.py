import multiprocessing
import threading

from src.ocr import OCRProcessor
from src.gui import GUI
from src.states import AppState


class AppController:
    """Controller class for the graphical application."""
    def __init__(self):
        self.gui = GUI(self)
        self.ocr_processor = OCRProcessor(self)  # For CSV saving in main process, OK
        self.current_state = None
        self.parsed_files = []
        self.current_file = None  # Track the current file being processed

        # Shared multiprocessing Manager/Queue for collecting results
        self.manager = multiprocessing.Manager()
        self.result_queue = self.manager.Queue()

    def set_state(self, new_state):
        """Sets the current state of the app."""
        self.current_state = new_state
        self.gui.set_state(new_state)

    @staticmethod
    def process_pdf_worker(file_path, result_queue):
        """
        Worker function that runs in a child process.

        1) Creates a local OCRProcessor with `master=None` to avoid any Tkinter references.
        2) Calls its extract_text_from_pdf(file_path).
        3) Puts (file_path, (csv_path, parsed_data)) into result_queue on success;
           puts (file_path, None) if something fails or returns empty data.
        """
        # Create a local OCRProcessor that does NOT reference Tk objects
        ocr_processor_local = OCRProcessor(None)
        csv_path, extracted_data = (None, None)

        try:
            csv_path, extracted_data = ocr_processor_local.extract_text_from_pdf(file_path)
        except Exception as e:
            # We cannot directly show a Tkinter error dialog in child process,
            # so either log or store the error in the queue if desired.
            print(f"Error processing {file_path}: {e}")

        # If both are valid, assume success; otherwise mark as fail.
        if csv_path and extracted_data:
            result_queue.put((file_path, (csv_path, extracted_data)))
        else:
            result_queue.put((file_path, None))

    def process_files(self, file_paths):
        """Processes one or more files and updates the current state."""
        self.set_state(AppState.PROCESSING)
        self.parsed_files = []  # Clear previous results

        process_list = []

        # Spawn a child process for each PDF, passing only file_path + queue
        for file_path in file_paths:
            process = multiprocessing.Process(
                target=self.process_pdf_worker,
                args=(file_path, self.result_queue)
            )
            process_list.append(process)
            process.start()

        # In a separate thread, wait for each process to finish and gather results
        threading.Thread(
            target=self.collect_results,
            args=(process_list,),
            daemon=True
        ).start()

    def collect_results(self, process_list):
        """
        Waits for all worker processes to finish, then collects their results
        from self.result_queue. Finally, updates the GUI in the main thread.
        """
        for process in process_list:
            process.join()

        failed_files = []

        # Collect results from the queue
        while not self.result_queue.empty():
            file_path, parsed_result = self.result_queue.get()
            if parsed_result:
                # parsed_result is presumably (csv_path, extracted_text) from OCR
                self.parsed_files.append(parsed_result)
            else:
                failed_files.append(file_path)

        # Schedule a GUI update in the main thread
        self.gui.root.after(0, self.update_gui_after_processing, failed_files)

    def update_gui_after_processing(self, failed_files):
        """Safely update the GUI after processing completes."""
        if failed_files:
            failed_message = "\n".join(failed_files)
            self.gui.handle_error("Processing Error", f"Some files failed:\n{failed_message}")

        self.set_state(AppState.RESULTS)

    def save_parsed_files(self):
        """
        Save the parsed files to disk in the main process
        (safe to call self.ocr_processor here).
        """
        if not self.parsed_files:
            self.gui.handle_error("Save Error", "No successfully parsed files to save.")
            return

        # Each item in self.parsed_files is (csv_path, extracted_text)
        for csv_path, extracted_text in self.parsed_files:
            if csv_path and extracted_text:
                saved_path = self.ocr_processor.save_csv(csv_path, extracted_text)
                if not saved_path:
                    self.gui.handle_error("Save Error", f"Failed to save: {csv_path}")

    def run(self):
        """Start the GUI."""
        self.gui.root.mainloop()
