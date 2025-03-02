import os
from tkinter import filedialog, scrolledtext, messagebox

try:
    from Tkinter import *
except ImportError:
    from tkinter import *

from tkinterdnd2 import TkinterDnD, DND_FILES
from states import AppState

file_pic_base_64 = ('iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAMAAABg3Am1AAAAk1BMVEVHcEzJz9j/Vi/'
                    'jMQbo6+7FytL/VS/ovrbq6+/e4Obs9fvhZUfbLwnYy835UizR1N3/VjDM0tn9XzzHzdb'
                    '/79Dr7PD/VjDu7/PCyND8clO/xc7/WTP/UCjs7vL/SiL/RBrFy9T29/v//v7/8/D/ppP'
                    '/va709Pn/moP/3NX/ZEH/Uyz/xLf/0Mb/6eT/hGj/eFpHcEwgl6rUAAAAMXRSTlMA9NT7'
                    'TULPA/77+e9KZ/glnOze4f////////////////////////////////////8A2zK2aQAAA'
                    'clJREFUSMfN1e1ugjAUBuBuTkCdClsoaEthFGwpftz/3e0UxLFRCvuz7E1MQzhPzkEKIAR'
                    'x0TZJvPBnVu9LOGWIi/ZhNKyPVllgFi56+RjWAzhmT0YxDkbEOIjNwgLMwgaMwjaSUdg7G'
                    'IQVmKaa6DAU9g7H4VRTIw16WO50FxDv+6kOevd9JV69PFqMgTDxeolmgH68058Cdx5wvzp'
                    'sTzPAtuvgotfNOpwE681rK6B+MQOE682iEbp+LmgF1ANIJqMBCISe1W63O8wIlClHA4IJp'
                    'k1YqkNVszJFaXOcsvYslJE7aEPotYQIWIuiEAdKsCh0bupR8h2wIuec52dWw5rngpJLriP'
                    'YOKgoLfJDyQmpyvzGLmdcVVVXYAQsFQ1QlPASQArDKwuQZ5lLWnO4PiYlk3pGbhtJSllW6'
                    'QNceFmX9ZWOdYBpUsowqzl+jMQYo3gc3CghBEDVXbQ+xpZrAABr+7cWFHPJeuV90PzUQVT'
                    '6dioB96/Qk4urGgJfN+22Rm+LNFvjvivuW4MQXz8PvuO8zdl8b47j6+fB/c1LoH3k5gP3/'
                    '77I0NKLksiaJPKWfZAFq4kEWR/s4+xoT5zF+/4naBvEEwnub8pP7R+maUCbATwAAAAASUVO'
                    'RK5CYII=')


class GUI():
    def __init__(self, master):
        self.master = master  # Reference to the AppController
        self.root = TkinterDnD.Tk()
        self.root.title("R&D Labs Directory Parser")
        self.root.geometry("600x400")
        self.state = AppState.FILE_SELECTION
        self.master.current_state = AppState.FILE_SELECTION
        self.added_files = []
        self.inner_frame = None
        # self.csv_files = []  # Initialize csv_files list
        self.create_main_frame()
        self.generate_frame()
        global file_icon
        file_icon = PhotoImage(data=file_pic_base_64)

    def create_main_frame(self):
        self.main_frame = Frame(self.root)
        self.main_frame.pack(expand=True, fill="both")

    def generate_frame(self, data=None):
        if self.main_frame:
            self.main_frame.destroy()
        self.create_main_frame()
        if self.state == AppState.FILE_SELECTION:
            self.create_file_selection_frame()
        elif self.state == AppState.PROCESSING:
            self.create_processing_frame()
        elif self.state == AppState.RESULTS:
            self.create_results_frame(data)
        elif self.state == AppState.COMPLETE:
            self.create_complete_frame()
        else:
            print(f"ERROR: No frame found for state: {self.state}")
            return

    def set_state(self, new_state, data=None):
        self.state = new_state
        self.generate_frame(data)

    def create_file_selection_frame(self):
        frame = Frame(self.main_frame)
        frame.pack(expand=True, fill="both")
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        main_frame = Frame(frame)
        main_frame.grid(row=1, column=0, padx=5, pady=5, sticky="news")
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        self.canvas = Canvas(main_frame, bg="white", relief="sunken", bd=1)
        self.canvas.grid(row=0, column=0, padx=5, pady=5, sticky="news")
        self.scrollbar = Scrollbar(main_frame, orient="vertical", command=self.canvas.yview)
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.inner_frame = Frame(self.canvas, bg="lightgray")
        self.inner_window = self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")
        self.canvas.drop_target_register(DND_FILES)
        self.canvas.dnd_bind("<<Drop>>", self.drop_file)
        self.canvas.filenames = {}
        self.canvas.nextcoords = [60, 20]
        bottom_frame = Frame(frame)
        bottom_frame.grid(row=2, column=0, columnspan=2, pady=10, sticky="ew")
        self.status_label = Label(bottom_frame, text="", fg="black", anchor="w", width=50)
        self.status_label.pack(side="left", padx=10)
        self.select_button = Button(bottom_frame, text="Select Files", command=self.add_files)
        self.select_button.pack(side="right", padx=10)
        self.process_button = Button(bottom_frame, text="Parse Files", command=self.process_files)
        self.process_button.pack(side="right", padx=10)

    def create_processing_frame(self):
        pass

    def create_results_frame(self, results):
        frame = Frame(self.main_frame)
        frame.pack(expand=True, fill="both")
        main_frame = Frame(frame)
        main_frame.grid(row=1, column=0, padx=5, pady=5, sticky="news")
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)
        self.inner_frame = Frame(frame)
        self.inner_frame.grid(row=0, column=0, padx=10, pady=10, sticky="news")
        label = Label(self.inner_frame, text="OCR Results", font=("Arial", 14, "bold"))
        label.pack(pady=10)
        text_area = scrolledtext.ScrolledText(self.inner_frame, wrap=WORD, height=15)
        text_area.pack(expand=True, fill="both", padx=10, pady=5)
        text_area.insert(END, results)
        text_area.config(state=DISABLED)

    def create_complete_frame(self):
        pass

    def drop_file(self, event):
        files = self.root.splitlist(event.data)
        valid_count, duplicate_count, invalid_count = 0, 0, 0
        for file in files:
            if not self.is_pdf(file):
                invalid_count += 1
                continue
            if self.is_pdf(file) and file in self.added_files:
                print(f"Skipping Previously Added File: {file}")
                duplicate_count += 1
                continue
            if self.is_pdf(file) and file not in self.added_files:
                self.add_file_to_canvas(file)
                valid_count += 1
        self.update_status(valid_count, duplicate_count, invalid_count)

    def add_files(self):
        filenames = filedialog.askopenfilenames(filetypes=[("PDF files", "*.pdf")])
        valid_count, duplicate_count, invalid_count = 0, 0, 0
        for file in filenames:
            if file not in self.added_files:
                self.add_file_to_canvas(file)
                valid_count += 1
            else:
                print(f"Skipping Previously Added File: {file}")
                duplicate_count += 1
        self.update_status(valid_count, duplicate_count, invalid_count)

    def add_file_to_canvas(self, file_path):
        id1 = self.canvas.create_image(self.canvas.nextcoords[0], self.canvas.nextcoords[1], image=file_icon, anchor='n', tags=('file',))
        id2 = self.canvas.create_text(self.canvas.nextcoords[0], self.canvas.nextcoords[1] + 50, text=os.path.basename(file_path), anchor='n', justify='center', width=90)
        self.canvas.filenames[id1] = file_path
        self.canvas.filenames[id2] = file_path
        if self.canvas.nextcoords[0] > 450:
            self.canvas.nextcoords = [60, self.canvas.nextcoords[1] + 130]
        else:
            self.canvas.nextcoords = [self.canvas.nextcoords[0] + 100, self.canvas.nextcoords[1]]
        self.added_files.append(file_path)
        print("Added file: ", file_path)

    def update_status(self, valid, duplicate, invalid):
        status_parts = []
        if valid > 0:
            status_parts.append(f"Added {valid} VALID File{'s' if valid > 1 else ''}")
        if duplicate > 0:
            status_parts.append(f"Skipped {duplicate} DUPLICATE{'S' if duplicate > 1 else ''}")
        if invalid > 0:
            status_parts.append(f"Ignored {invalid} NON-VALID File{'s' if invalid > 1 else ''}")
        self.status_label.config(text=" | ".join(status_parts), fg="blue")

    def is_pdf(self, file_path):
        return file_path.lower().endswith('.pdf')

    def handle_error(self, title, message, msg_type="error"):
        msgbox_funcs = {
            "error": messagebox.showerror,
            "warning": messagebox.showwarning,
            "info": messagebox.showinfo
        }
        msgbox_funcs.get(msg_type, messagebox.showerror)(title, message)

    def process_files(self):
        if self.added_files:
            self.master.process_files(self.added_files)
        else:
            self.handle_error("Processing Error", "Parsing failed. No PDF files were selected.")