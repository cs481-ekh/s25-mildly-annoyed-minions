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
        self.master = master
        self.root = TkinterDnD.Tk()
        self.root.title("R&D Labs Directory Parser")
        self.root.geometry("600x500")
        self.state = AppState.FILE_SELECTION
        self.master.current_state = AppState.FILE_SELECTION
        self.added_files = []
        self.selected_files = []
        self.inner_frame = None
        self.status_label = None
        self.drag_drop_label = None
        self.create_main_frame()
        self.generate_frame()
        global file_icon
        file_icon = PhotoImage(data=file_pic_base_64)

    def create_main_frame(self):
        self.main_frame = Frame(self.root)
        self.main_frame.pack(expand=True, fill="both")

    def generate_frame(self):
        if self.main_frame:
            self.main_frame.destroy()
        self.create_main_frame()
        if self.state == AppState.FILE_SELECTION:
            self.create_file_selection_frame()
        elif self.state == AppState.PROCESSING:
            self.create_processing_frame()
        elif self.state == AppState.RESULTS:
            self.create_results_frame()
        elif self.state == AppState.COMPLETE:
            self.create_complete_frame()
        elif self.state == AppState.ERROR:
            self.create_error_frame()
        else:
            self.log_message(f"ERROR: No frame found for state: {self.state}", "error")
            return

    def set_state(self, new_state):
        old_state = self.state
        self.state = new_state
        self.log_message(f"State changed from {old_state} to {new_state}", "info")
        self.generate_frame()

    def create_file_selection_frame(self):
        frame = Frame(self.main_frame)
        frame.pack(expand=True, fill="both")
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        top_frame = Frame(frame, height=30)
        top_frame.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        top_frame.grid_columnconfigure(0, weight=1)
        top_frame.pack_propagate(False)
        self.remove_button_container = Frame(top_frame)
        self.remove_button_container.pack(side="right", padx=5)
        self.remove_button = Button(self.remove_button_container, text="X", command=self.remove_selected_files,
                                    fg="white", bg="red", width=3, padx=4, pady=2)
        main_frame = Frame(frame)
        main_frame.grid(row=1, column=0, padx=5, pady=5, sticky="news")
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        canvas_bg = "#f7f7f7" if not self.added_files else "white"
        self.canvas = Canvas(main_frame, bg=canvas_bg, relief="sunken", bd=1)
        self.canvas.grid(row=0, column=0, padx=5, pady=5, sticky="news")
        self.scrollbar = Scrollbar(main_frame, orient="vertical", command=self.canvas.yview)
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.inner_frame = Frame(self.canvas, bg="lightgray")
        self.inner_window = self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")
        self.canvas.drop_target_register(DND_FILES)
        self.canvas.dnd_bind("<<Drop>>", self.drop_file)
        self.canvas.filenames = {}
        self.canvas.file_icon_ids = {}
        self.canvas.file_bg_ids = {}
        self.canvas.nextcoords = [60, 20]
        self.canvas.bind("<Button-1>", self.handle_canvas_click)
        if not self.added_files:
            self.drag_drop_label = Label(self.canvas, text="Drag & Drop PDF Files Here",
                                         font=("Arial", 10), fg="#555555", bg=canvas_bg)
            self.drag_drop_label.pack(expand=True, fill="both")
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

    def create_results_frame(self):
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
        text_area.insert(END, self.master.parsed_files[0][1])  # REPLACE WITH ACTUAL RESULTS DISPLAY AND HANDLING
        text_area.config(state=DISABLED)
        download_button = Button(self.inner_frame, text="Save Parsed Files", command=self.master.save_parsed_files)
        download_button.pack(pady=10)

    def create_complete_frame(self):
        pass

    def create_error_frame(self):
        pass

    def drop_file(self, event):
        files = self.root.splitlist(event.data)
        valid_count, duplicate_count, invalid_count = 0, 0, 0
        for file in files:
            if not self.is_pdf(file):
                invalid_count += 1
                self.log_message(f"Invalid file type: {file}", "warning")
                continue
            if self.is_pdf(file) and file in self.added_files:
                self.log_message(f"Skipping previously added file: {file}", "info")
                duplicate_count += 1
                continue
            if self.is_pdf(file) and file not in self.added_files:
                if not self.added_files:
                    self.remove_drag_drop_label()
                self.add_file_to_canvas(file)
                valid_count += 1

        self.update_file_status(valid=valid_count, duplicate=duplicate_count, invalid=invalid_count)

    def add_files(self):
        if self.status_label:
            self.status_label.config(text="")

        filenames = filedialog.askopenfilenames(filetypes=[("PDF files", "*.pdf")])
        valid_count, duplicate_count = 0, 0
        for file in filenames:
            if file not in self.added_files:
                if not self.added_files:
                    self.remove_drag_drop_label()
                self.add_file_to_canvas(file)
                valid_count += 1

            else:
                self.log_message(f"Skipping previously added file: {file}", "info")
                duplicate_count += 1

        self.update_file_status(valid_count, duplicate_count)

    def add_file_to_canvas(self, file_path):
        bg_rect = self.canvas.create_rectangle(
            self.canvas.nextcoords[0] - 40,
            self.canvas.nextcoords[1] - 10,
            self.canvas.nextcoords[0] + 40,
            self.canvas.nextcoords[1] + 90,
            fill="", outline="", tags=('file_bg',)
        )

        icon_id = self.canvas.create_image(
            self.canvas.nextcoords[0],
            self.canvas.nextcoords[1],
            image=file_icon,
            anchor='n',
            tags=('file',)
        )

        text_id = self.canvas.create_text(
            self.canvas.nextcoords[0],
            self.canvas.nextcoords[1] + 50,
            text=os.path.basename(file_path),
            anchor='n',
            justify='center',
            width=90
        )

        self.canvas.filenames[icon_id] = file_path
        self.canvas.filenames[text_id] = file_path
        self.canvas.filenames[bg_rect] = file_path

        self.canvas.file_icon_ids[file_path] = icon_id
        self.canvas.file_bg_ids[file_path] = bg_rect

        if self.canvas.nextcoords[0] > 450:
            self.canvas.nextcoords = [60, self.canvas.nextcoords[1] + 130]
        else:
            self.canvas.nextcoords = [self.canvas.nextcoords[0] + 100, self.canvas.nextcoords[1]]

        self.added_files.append(file_path)
        self.log_message(f"Added file: {os.path.basename(file_path)}", "success")

    def handle_canvas_click(self, event):
        if self.status_label:
            self.status_label.config(text="")

        clicked_items = self.canvas.find_withtag(CURRENT)

        if not clicked_items:
            self.deselect_all_files()
            return

        clicked_id = clicked_items[0]

        if clicked_id in self.canvas.filenames:
            file_path = self.canvas.filenames[clicked_id]
            icon_id = self.canvas.file_icon_ids.get(file_path)
            bg_id = self.canvas.file_bg_ids.get(file_path)

            if icon_id in self.selected_files:
                self.deselect_file(file_path, bg_id)
            else:
                self.select_file(file_path, bg_id)
        else:
            self.deselect_all_files()

        self.update_remove_button_visibility()

    def remove_drag_drop_label(self):
        if hasattr(self, 'drag_drop_label') and self.drag_drop_label:
            self.drag_drop_label.destroy()
            self.drag_drop_label = None
            self.canvas.config(bg="white")

    def update_remove_button_visibility(self):
        if self.selected_files:
            self.remove_button.pack(side="right", padx=2, pady=2)
        else:
            self.remove_button.pack_forget()

    def select_file(self, file_path, bg_id):
        self.canvas.itemconfig(bg_id, fill="#add8e6", outline="#4682b4")  # Light blue background
        self.selected_files.append(self.canvas.file_icon_ids[file_path])
        self.log_message(f"Selected file: {os.path.basename(file_path)}")

    def deselect_file(self, file_path, bg_id):
        self.canvas.itemconfig(bg_id, fill="", outline="")
        if self.canvas.file_icon_ids[file_path] in self.selected_files:
            self.selected_files.remove(self.canvas.file_icon_ids[file_path])
        self.log_message(f"Deselected file: {os.path.basename(file_path)}")

    def deselect_all_files(self):
        for file_path in self.added_files:
            if file_path in self.canvas.file_bg_ids:
                bg_id = self.canvas.file_bg_ids[file_path]
                self.canvas.itemconfig(bg_id, fill="", outline="")

        self.log_message(f"Deselected {len(self.selected_files)} files")
        self.selected_files = []

        self.update_remove_button_visibility()

    def get_selected_files(self):
        selected_paths = []
        for icon_id in self.selected_files:
            if icon_id in self.canvas.filenames:
                selected_paths.append(self.canvas.filenames[icon_id])
        return selected_paths

    def remove_selected_files(self):
        if not self.selected_files:
            return

        selected_paths = self.get_selected_files()
        removed_count = len(selected_paths)

        for file_path in selected_paths:
            icon_id = self.canvas.file_icon_ids.get(file_path)
            bg_id = self.canvas.file_bg_ids.get(file_path)

            for item_id in self.canvas.find_all():
                if self.canvas.filenames.get(item_id) == file_path:
                    self.canvas.delete(item_id)

            if icon_id in self.canvas.filenames:
                del self.canvas.filenames[icon_id]
            if bg_id in self.canvas.filenames:
                del self.canvas.filenames[bg_id]

            if file_path in self.canvas.file_icon_ids:
                del self.canvas.file_icon_ids[file_path]
            if file_path in self.canvas.file_bg_ids:
                del self.canvas.file_bg_ids[file_path]

            if file_path in self.added_files:
                self.added_files.remove(file_path)

        self.selected_files = []

        self.update_remove_button_visibility()

        if not self.added_files:
            self.canvas.nextcoords = [60, 20]
            self.drag_drop_label = Label(self.canvas, text="Drag & Drop PDF Files Here",
                                        font=("Arial", 10), fg="#555555", bg="#f7f7f7")
            self.drag_drop_label.pack(expand=True, fill="both")
        self.update_file_status(remove=removed_count)

    def is_pdf(self, file_path):
        return file_path.lower().endswith('.pdf')

    def update_file_status(self, valid=0, duplicate=0, invalid=0, remove=0):

        status_parts = []
        status_type = "info"

        if valid > 0:
            status_parts.append(f"Added {valid} valid file{'s' if valid > 1 else ''}")
            status_type = "success"
        if duplicate > 0:
            status_parts.append(f"Skipped {duplicate} duplicate{'s' if duplicate > 1 else ''}")
            status_type = "warning" if valid == 0 else status_type
        if invalid > 0:
            status_parts.append(f"Ignored {invalid} non-valid file{'s' if invalid > 1 else ''}")
            status_type = "warning" if valid == 0 else status_type
        if remove > 0:
            status_parts.append(f"Removed {remove} file{'s' if remove > 1 else ''}")
            status_type = "info"

        if not status_parts:
            status_message = "No files selected"
            status_type = "info"
        else:
            status_message = " | ".join(status_parts)

        self.update_status(status_message, status_type, True)

    def update_status(self, message, status_type="info", update_label=False):
        prefix = {
            "info": "INFO",
            "success": "SUCCESS",
            "warning": "WARNING",
            "error": "ERROR"
        }.get(status_type, "INFO")

        print(f"[{prefix}] {message}")

        colors = {
            "info": "blue",
            "success": "green",
            "warning": "orange",
            "error": "red"
        }

        if update_label and self.status_label:
            self.status_label.config(text=message, fg=colors.get(status_type, "black"))

    def log_message(self, message, msg_type="info"):
        self.update_status(message, msg_type)

    def handle_error(self, title, message, msg_type="error"):
        msgbox_funcs = {
            "error": messagebox.showerror,
            "warning": messagebox.showwarning,
            "info": messagebox.showinfo,
            "confirm": messagebox.askyesnocancel
            # OTHER TYPES OF ERROR / NOTIFICATION MESSAGING SUPPORTED
        }

        self.log_message(f"{title}: {message}", msg_type)

        msgbox_funcs.get(msg_type, messagebox.showerror)(title, message, parent=self.main_frame)

    def process_files(self):
        if self.status_label:
            self.status_label.config(text="")

        if self.added_files:
            self.master.process_files(self.added_files)
        else:
            self.handle_error("Processing Error", "Parsing failed. No PDF files were selected.")

    def handle_results(self):
        pass