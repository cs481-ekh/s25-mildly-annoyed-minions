# src/gui/app_window.py
import os
from tkinter import filedialog, scrolledtext, messagebox

try:
    from Tkinter import *
except ImportError:
    from tkinter import *

from tkinterdnd2 import TkinterDnD, DND_FILES
from src.utils.globals import AppState, FILE_PIC_BASE_64, SDP_LOGO


class GUI:
    """Class to represent the GUI application window."""
    def __init__(self, master):
        self.master = master
        self.root = TkinterDnD.Tk()
        self.root.minsize(810, 648)
        self.root.geometry("810x648")
        self.root.title("R&D Labs Directory Parser")
        self.state = AppState.FILE_SELECTION
        self.master.current_state = AppState.FILE_SELECTION
        self.added_files = []
        self.selected_files = []
        self.last_window_width = self.root.winfo_width()
        self.select_button = None
        self.inner_window = None
        self.scrollbar = None
        self.remove_button_container = None
        self.remove_button = None
        self.canvas = None
        self.inner_frame = None
        self.page_title_label = None
        self.logo_label = None
        self.drag_drop_label = None
        self.status_label = None
        self.process_button = None
        self.main_frame = None
        self.sdp_logo = PhotoImage(data=SDP_LOGO)
        self.file_icon = PhotoImage(data=FILE_PIC_BASE_64)
        self.create_main_frame()
        self.generate_frame()
        self.bind_window_resize()

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

    def set_state(self, new_state):
        old_state = self.state
        self.state = new_state
        self.log_message(f"State changed from {old_state} to {new_state}", "info")
        self.generate_frame()

    def create_main_frame(self):
        self.main_frame = Frame(self.root)
        self.main_frame.pack(expand=True, fill="both")

        top_frame = Frame(self.main_frame, height=60)
        top_frame.pack(side="top", fill="x", anchor="n", pady=(5, 0))
        top_frame.pack_propagate(False)

        top_frame.columnconfigure(0, weight=0, minsize=160)
        top_frame.columnconfigure(1, weight=1)
        top_frame.columnconfigure(2, weight=0, minsize=160)

        self.logo_label = Label(top_frame, image=self.sdp_logo)
        self.logo_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        title_frame = Frame(top_frame)
        title_frame.grid(row=0, column=1, sticky="nsew")
        title_frame.columnconfigure(0, weight=1)
        title_frame.rowconfigure(0, weight=1)

        self.page_title_label = Label(title_frame, text="Page Title", font=("Arial", 14, "bold"))
        self.page_title_label.grid(row=0, column=0, sticky="nsew")

        self.remove_button_container = Frame(top_frame)
        self.remove_button_container.grid(row=0, column=2, sticky="se")
        # self.remove_button_container.pack(side="bottom", padx=5)
        self.remove_button = Button(
            self.remove_button_container,
            text="X",
            command=self.remove_selected_files,
            fg="white",
            bg="red",
            width=3,
            padx=4,
            pady=5
        )

    def create_file_selection_frame(self):
        content_frame = Frame(self.main_frame)
        content_frame.pack(expand=True, fill="both")
        content_frame.grid_rowconfigure(1, weight=1)
        content_frame.grid_columnconfigure(0, weight=1)

        main_frame = Frame(content_frame)
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
        self.bind_mousewheel_to_canvas()

        if not self.added_files:
            self.drag_drop_label = Label(self.canvas, text="Drag & Drop PDF Files Here",
                                         font=("Arial", 10), fg="#555555", bg=canvas_bg)
            self.drag_drop_label.pack(expand=True, fill="both")

        bottom_frame = Frame(content_frame, height=40)
        bottom_frame.grid(row=2, column=0, padx=5, pady=10, sticky="ew")
        bottom_frame.grid_columnconfigure(0, weight=1)
        bottom_frame.grid_propagate(False)

        self.status_label = Label(bottom_frame, text="", fg="black", anchor="w")
        self.status_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        button_frame = Frame(bottom_frame)
        button_frame.grid(row=0, column=1, padx=10, pady=5, sticky="e")

        self.process_button = Button(
            button_frame,
            text="Parse All Files",
            command=self.process_files
        )
        self.process_button.pack(side="right", padx=10)
        self.update_process_button_text()

        self.select_button = Button(button_frame, text="Select Files", command=self.add_files)
        self.select_button.pack(side="right", padx=10)

        self.update_page_title("Select Files to Parse")

    def create_processing_frame(self):
        # Implementation for processing frame goes here.

        self.update_page_title("Processing")

        pass

    def create_results_frame(self):
        content_frame = Frame(self.main_frame)
        content_frame.pack(expand=True, fill="both")

        main_frame = Frame(content_frame)
        main_frame.grid(row=1, column=0, padx=5, pady=5, sticky="news")
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)

        self.inner_frame = Frame(content_frame)
        self.inner_frame.grid(row=0, column=0, padx=10, pady=10, sticky="news")

        text_area = scrolledtext.ScrolledText(self.inner_frame, wrap=WORD, height=15)
        text_area.pack(expand=True, fill="both", padx=10, pady=5)

        # REPLACE WITH ACTUAL RESULTS DISPLAY AND HANDLING
        if self.master.parsed_files:
            # Display the extracted text from the first parsed file
            text_area.insert(END, self.master.parsed_files[0][1])
        text_area.config(state="disabled")

        download_button = Button(
            self.inner_frame,
            text="Save Parsed Files",
            command=self.master.save_parsed_files
        )
        download_button.pack(pady=10)

        self.update_page_title("OCR Results")

    def create_complete_frame(self):
        # Implementation for complete frame goes here.
        pass

    def create_error_frame(self):
        # Implementation for error frame goes here.
        pass

    def update_page_title(self, new_title):
        self.page_title_label.config(text=new_title)

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
                self.added_files.append(file)
                valid_count += 1

        if valid_count > 0:
            self.arrange_files()

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
                self.added_files.append(file)
                valid_count += 1
            else:
                self.log_message(f"Skipping previously added file: {file}", "info")
                duplicate_count += 1
        if valid_count > 0:
            self.arrange_files()

        self.update_file_status(valid_count, duplicate_count)

    def remove_selected_files(self):
        if not self.selected_files:
            return

        selected_paths = self.get_selected_files()
        removed_count = len(selected_paths)

        for file_path in selected_paths:
            if file_path in self.added_files:
                self.added_files.remove(file_path)

        self.selected_files = []

        self.update_process_button_text()
        self.update_remove_button_visibility()
        self.arrange_files()
        self.update_file_status(remove=removed_count)

    def bind_window_resize(self):
        self.root.bind("<Configure>", self.on_window_resize)
        self.last_window_width = self.root.winfo_width()

    def on_window_resize(self, event):
        if event.widget == self.root:
            current_width = self.root.winfo_width()
            if abs(current_width - self.last_window_width) > 10:
                self.last_window_width = current_width
                if current_width > 100:
                    self.arrange_files()

    def bind_mousewheel_to_canvas(self):
        def _on_mousewheel(event):
            if event.num == 4 or event.delta > 0:
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5 or event.delta < 0:
                self.canvas.yview_scroll(1, "units")

        self.canvas.bind("<MouseWheel>", _on_mousewheel)
        self.canvas.bind("<Button-4>", _on_mousewheel)
        self.canvas.bind("<Button-5>", _on_mousewheel)

    def calculate_grid_layout(self):
        if not hasattr(self, 'canvas') or not self.canvas.winfo_exists():
            return 5

        canvas_width = self.canvas.winfo_width()
        if canvas_width <= 1:
            canvas_width = self.root.winfo_width() - 40

        icon_width = 100
        icons_per_row = max(1, int((canvas_width - 40) / icon_width))
        return icons_per_row

    def arrange_files(self):
        self.canvas.delete("all")
        self.canvas.filenames = {}
        self.canvas.file_icon_ids = {}
        self.canvas.file_bg_ids = {}

        if not self.added_files:
            self.canvas.config(bg="#f7f7f7")
            if hasattr(self, 'drag_drop_label') and self.drag_drop_label:
                self.drag_drop_label.destroy()
            self.drag_drop_label = Label(self.canvas, text="Drag & Drop PDF Files Here",
                                         font=("Arial", 10), fg="#555555", bg="#f7f7f7")
            self.drag_drop_label.place(relx=0.5, rely=0.5, anchor=CENTER)
            return

        self.canvas.config(bg="white")
        if hasattr(self, 'drag_drop_label') and self.drag_drop_label:
            self.drag_drop_label.destroy()
            self.drag_drop_label = None

        icons_per_row = self.calculate_grid_layout()
        margin_x, margin_y = 30, 30
        icon_width, icon_height = 100, 120
        row, col = 0, 0
        for file_path in self.added_files:
            x = margin_x + (col * icon_width) + (icon_width / 2)
            y = margin_y + (row * icon_height)
            bg_rect = self.canvas.create_rectangle(
                x - 40, y - 10,
                x + 40, y + 90,
                fill="", outline="", tags=('file_bg',)
            )
            icon_id = self.canvas.create_image(
                x, y,
                image=self.file_icon,
                anchor='n',
                tags=('file',)
            )
            text_id = self.canvas.create_text(
                x, y + 50,
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

            if icon_id in self.selected_files or (
                    file_path in self.canvas.file_icon_ids and
                    self.canvas.file_icon_ids[file_path] in self.selected_files
            ):
                self.canvas.itemconfig(bg_rect, fill="#add8e6", outline="#4682b4")
                if icon_id not in self.selected_files:
                    self.selected_files.append(icon_id)

            col += 1
            if col >= icons_per_row:
                col = 0
                row += 1

        total_rows = (len(self.added_files) + icons_per_row - 1) // icons_per_row
        canvas_height = margin_y + (total_rows * icon_height) + margin_y
        canvas_width = margin_x + (min(len(self.added_files), icons_per_row) * icon_width)
        self.canvas.config(scrollregion=(0, 0, canvas_width, canvas_height))

    def handle_canvas_click(self, event):
        if self.status_label:
            self.status_label.config(text="")

        clicked_items = self.canvas.find_withtag("current")
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

        self.update_process_button_text()
        self.update_remove_button_visibility()

    def remove_drag_drop_label(self):
        if hasattr(self, 'drag_drop_label') and self.drag_drop_label:
            self.drag_drop_label.destroy()
            self.drag_drop_label = None
            self.canvas.config(bg="white")

    def update_process_button_text(self):
        if not hasattr(self, 'process_button'):
            return

        if not self.added_files:
            self.process_button.config(text="Parse All Files")
        elif self.selected_files:
            file_count = len(self.selected_files)
            self.process_button.config(
                text=f"Parse {file_count} File{'s' if file_count > 1 else ''}"
            )
        else:
            self.process_button.config(text="Parse All Files")

    def update_remove_button_visibility(self):
        if self.selected_files:
            self.remove_button.pack(side="right", padx=2, pady=2)
        else:
            self.remove_button.pack_forget()

    def select_file(self, file_path, bg_id):
        self.canvas.itemconfig(bg_id, fill="#add8e6", outline="#4682b4")
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
        self.update_process_button_text()
        self.update_remove_button_visibility()

    def get_selected_files(self):
        selected_paths = []
        for icon_id in self.selected_files:
            if icon_id in self.canvas.filenames:
                selected_paths.append(self.canvas.filenames[icon_id])
        return selected_paths

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

        status_message = "No files selected" if not status_parts else " | ".join(status_parts)
        self.update_status(status_message, status_type, True)

    def update_status(self, message, status_type="info", update_label=False):
        prefix = {"info": "INFO", "success": "SUCCESS", "warning": "WARNING", "error": "ERROR"}.get(status_type, "INFO")
        print(f"[{prefix}] {message}")
        colors = {"info": "blue", "success": "green", "warning": "orange", "error": "red"}
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
        }
        self.log_message(f"{title}: {message}", msg_type)
        msgbox_funcs.get(msg_type, messagebox.showerror)(title, message, parent=self.main_frame)

    def process_files(self):
        if self.status_label:
            self.status_label.config(text="")
        files_to_process = self.get_selected_files() if self.selected_files else self.added_files
        if files_to_process:
            self.master.process_files(files_to_process)
        else:
            self.handle_error("Processing Error", "Parsing failed. No PDF files were selected.")

    def show_info(self, title, message):
        messagebox.showinfo(title, message, parent=self.root)

    def handle_results(self):
        # Implementation to handle and display OCR results
        pass
