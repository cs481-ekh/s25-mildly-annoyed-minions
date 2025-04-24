# src/gui/app_window.py
import os
import textwrap
from tkinter import (filedialog, messagebox)

import PIL
from PIL import Image, ImageDraw, ImageTk

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
        self.selected_save_paths = set()
        self.result_file_widgets = {}
        self.last_window_width = None
        self.select_button = None
        self.save_button = None
        self.file_selection_inner_window = None
        self.results_canvas_window = None
        self.scrollbar = None
        self.remove_button_container = None
        self.remove_button = None
        self.file_selection_canvas = None
        self.results_canvas = None
        self.rect_select_start_x = None
        self.rect_select_start_y = None
        self.rect_select_current = None
        self.rect_selection_active = False
        self.file_selection_inner_frame = None
        self.results_inner_frame = None
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

        top_frame.columnconfigure(0, weight=0, minsize=150)
        top_frame.columnconfigure(1, weight=1)
        top_frame.columnconfigure(2, weight=0, minsize=205)

        self.logo_label = Label(top_frame, image=self.sdp_logo)
        self.logo_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        title_frame = Frame(top_frame)
        title_frame.grid(row=0, column=1, sticky="nsew")
        title_frame.columnconfigure(0, weight=1)
        title_frame.rowconfigure(0, weight=1)

        self.page_title_label = Label(title_frame, text="Page Title", font=("Arial", 14, "bold"))
        self.page_title_label.grid(row=0, column=0, sticky="nsew")

        self.remove_button_container = Frame(top_frame)
        self.remove_button_container.grid(row=0, column=2, padx=(0, 28), sticky="se")
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
        self.update_page_title("Select Files to Parse")

        content_frame = Frame(self.main_frame)
        content_frame.pack(expand=True, fill="both")
        content_frame.grid_rowconfigure(1, weight=1)
        content_frame.grid_columnconfigure(0, weight=1)

        file_display_window = Frame(content_frame)
        file_display_window.grid(row=1, column=0, padx=5, pady=5, sticky="news")
        file_display_window.grid_rowconfigure(0, weight=1)
        file_display_window.grid_columnconfigure(0, weight=1)

        canvas_bg = "#f7f7f7" if not self.added_files else "white"
        self.file_selection_canvas = Canvas(file_display_window, bg=canvas_bg, relief="sunken", bd=1)
        self.file_selection_canvas.grid(row=0, column=0, padx=5, pady=5, sticky="news")
        self.scrollbar = Scrollbar(file_display_window, orient="vertical", command=self.file_selection_canvas.yview)
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.file_selection_canvas.configure(yscrollcommand=self.scrollbar.set)

        self.file_selection_inner_frame = Frame(self.file_selection_canvas, bg="lightgray")
        self.file_selection_inner_window = self.file_selection_canvas.create_window((0, 0),
                                                                                    window=self.file_selection_inner_frame,
                                                                                    anchor="nw")

        self.file_selection_canvas.drop_target_register(DND_FILES)
        self.file_selection_canvas.dnd_bind("<<Drop>>", self.drop_file)
        self.file_selection_canvas.filenames = {}
        self.file_selection_canvas.file_icon_ids = {}
        self.file_selection_canvas.file_bg_ids = {}
        self.file_selection_canvas.nextcoords = [60, 20]
        self.setup_rectangle_selection()
        self.bind_mousewheel_to_canvas()

        if not self.added_files:
            self.drag_drop_label = Label(self.file_selection_canvas,
                                         text="Drag & Drop PDF Files Here",
                                         font=("Arial", 10),
                                         fg="#555555",
                                         bg=canvas_bg)
            self.drag_drop_label.pack(expand=True, fill="both")

        bottom_frame = Frame(content_frame, height=50)
        bottom_frame.grid(row=2, column=0, padx=(0, 10), pady=10, sticky="ew")
        bottom_frame.grid_columnconfigure(0, weight=1)
        bottom_frame.grid_propagate(False)

        self.status_label = Label(bottom_frame, text="", fg="black", anchor="w")
        self.status_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        button_frame = Frame(bottom_frame)
        button_frame.grid(row=0, column=1, padx=10, sticky="e")

        self.process_button = Button(
            button_frame,
            text="Parse All Files",
            command=self.process_files,
            font=("Arial", 10, "bold"),
            bg="#3a4cde",
            fg="white",
            padx=10,
            pady=5
        )
        self.process_button.pack(side="right", padx=10)
        self.update_process_button_text()

        self.select_button = Button(button_frame, text="Select Files", command=self.add_files)
        self.select_button = Button(
            button_frame,
            text="Select Files",
            command=self.add_files,
            font=("Arial", 10, "bold"),
            bg="#c3c3c7",
            padx=10,
            pady=5
        )
        self.select_button.pack(side="right", padx=10)

    def create_processing_frame(self):
        # Implementation for processing frame goes here.

        self.update_page_title("Processing...")

        pass

    def create_results_frame(self):
        self.update_page_title("OCR Results")

        content_frame = Frame(self.main_frame)
        content_frame.pack(expand=True, fill="both")
        content_frame.grid_rowconfigure(1, weight=1)
        content_frame.grid_columnconfigure(0, weight=1)

        results_display_window = Frame(content_frame)
        results_display_window.grid(row=1, column=0, sticky="news", padx=5, pady=5)
        results_display_window.grid_rowconfigure(0, weight=1)
        results_display_window.grid_columnconfigure(0, weight=1)

        self.results_canvas = Canvas(results_display_window, bg="white", relief="sunken", bd=1)
        self.results_canvas.grid(row=0, column=0, sticky="news", padx=5, pady=5)

        results_scrollbar = Scrollbar(results_display_window, orient="vertical", command=self.results_canvas.yview)
        results_scrollbar.grid(row=0, column=1, sticky="ns")
        self.results_canvas.configure(yscrollcommand=results_scrollbar.set)

        self.results_inner_frame = Frame(self.results_canvas, bg="white")
        self.results_canvas_window = self.results_canvas.create_window((0, 0), window=self.results_inner_frame, anchor="nw")

        def on_inner_frame_configure(event):
            self.results_canvas.configure(scrollregion=self.results_canvas.bbox("all"))

        def on_canvas_resize(event):
            self.results_canvas.itemconfig(self.results_canvas_window, width=event.width)

        self.results_inner_frame.bind("<Configure>", on_inner_frame_configure)
        self.results_canvas.bind("<Configure>", on_canvas_resize)
        self.results_canvas.bind("<Button-1>", self._on_results_canvas_click)

        # ----- Header Row -----
        header = Frame(self.results_inner_frame, bg="#e0e0e0", pady=4)
        header.pack(fill="x")

        def bind_selection(row_widget, labels, path, bg_color):
            def on_click(event):
                self.toggle_file_selection(
                    file_path=path,
                    row_widget=row_widget,
                    selection_set=self.selected_save_paths,
                    selected_color="#add8e6",
                    default_color=bg_color
                )

            row_widget.bind("<Button-1>", on_click)
            for label in labels:
                label.bind("<Button-1>", on_click)

        # ----- File Rows -----
        for index, (file_path, _) in enumerate(self.master.parsed_files):
            base_name = os.path.basename(file_path)
            name, ext = os.path.splitext(base_name)
            file_ext = ext[1:].upper() or "N/A"
            try:
                size_bytes = os.path.getsize(file_path)
                size_str = f"{size_bytes / 1024:.1f} KB" if size_bytes < 1_000_000 else f"{size_bytes / 1_048_576:.2f} MB"
            except FileNotFoundError:
                size_str = "N/A"

            truncated_path = textwrap.shorten(file_path, width=80, placeholder="...")

            bg_color = "#ffffff" if index % 2 == 0 else "#f5f5f5"

            row = Frame(
                self.results_inner_frame,
                bg=bg_color,
                highlightthickness=0,  # no border by default
                bd=0,
                pady=2
            )

            labels = [
                Label(row, text=name, width=25, anchor="w", bg=bg_color, font=("Arial", 10)),
                Label(row, text=file_ext, width=8, anchor="w", bg=bg_color, font=("Arial", 10)),
                Label(row, text=size_str, width=10, anchor="w", bg=bg_color, font=("Arial", 10)),
                Label(row, text=truncated_path, anchor="w", bg=bg_color, font=("Arial", 10))
            ]

            for lbl in labels:
                lbl.pack(side="left", fill="y" if lbl != labels[-1] else "x", expand=(lbl == labels[-1]))

            bind_selection(row, labels, file_path, bg_color)

            self.result_file_widgets[file_path] = row
            row.pack(fill="x", expand=True)

        # ----- Save Button -----
        bottom_frame = Frame(content_frame, height=50)
        bottom_frame.grid(row=2, column=0, sticky="ew", padx=(0, 20), pady=(10, 10))
        bottom_frame.grid_columnconfigure(0, weight=1)
        bottom_frame.grid_propagate(False)

        status_placeholder = Label(bottom_frame, text="")  # You could repurpose this for summary or status
        status_placeholder.grid(row=0, column=0, padx=10, sticky="w")

        self.save_button = Button(
            bottom_frame,
            text="Save Parsed Files",
            command=self.master.save_parsed_files,
            font=("Arial", 10, "bold"),
            bg="#4CAF50",
            fg="white",
            padx=10,
            pady=5
        )
        self.save_button.grid(row=0, column=1, padx=10, sticky="e")
        self.update_save_button_text()

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
                if current_width > 100 and hasattr(self, 'file_selection_canvas') and self.file_selection_canvas:
                    self.arrange_files()


    def bind_mousewheel_to_canvas(self):
        def _on_mousewheel(event):
            if event.num == 4 or event.delta > 0:
                self.file_selection_canvas.yview_scroll(-1, "units")
            elif event.num == 5 or event.delta < 0:
                self.file_selection_canvas.yview_scroll(1, "units")

        self.file_selection_canvas.bind("<MouseWheel>", _on_mousewheel)
        self.file_selection_canvas.bind("<Button-4>", _on_mousewheel)
        self.file_selection_canvas.bind("<Button-5>", _on_mousewheel)

    def calculate_grid_layout(self):
        if not hasattr(self, 'file_selection_canvas') or not self.file_selection_canvas:
            return 7

        canvas_width = self.file_selection_canvas.winfo_width()
        if canvas_width <= 1:
            canvas_width = self.root.winfo_width() - 40

        icon_width = 100
        icons_per_row = max(1, int((canvas_width - 40) / icon_width))
        return icons_per_row

    def arrange_files(self):
        if not hasattr(self, 'file_selection_canvas') or not self.file_selection_canvas:
            return

        self.file_selection_canvas.delete("all")
        self.file_selection_canvas.filenames = {}
        self.file_selection_canvas.file_icon_ids = {}
        self.file_selection_canvas.file_bg_ids = {}

        if not self.added_files:
            self.file_selection_canvas.config(bg="#f7f7f7")
            if hasattr(self, 'drag_drop_label') and self.drag_drop_label:
                self.drag_drop_label.destroy()
            self.drag_drop_label = Label(self.file_selection_canvas, text="Drag & Drop PDF Files Here",
                                         font=("Arial", 10), fg="#555555", bg="#f7f7f7")
            self.drag_drop_label.place(relx=0.5, rely=0.5, anchor=CENTER)
            return

        self.file_selection_canvas.config(bg="white")
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
            bg_rect = self.file_selection_canvas.create_rectangle(
                x - 40, y - 10,
                x + 40, y + 90,
                fill="", outline="", tags=('file_bg',)
            )
            icon_id = self.file_selection_canvas.create_image(
                x, y,
                image=self.file_icon,
                anchor='n',
                tags=('file',)
            )
            text_id = self.file_selection_canvas.create_text(
                x, y + 50,
                text=os.path.basename(file_path),
                anchor='n',
                justify='center',
                width=90
            )

            self.file_selection_canvas.filenames[icon_id] = file_path
            self.file_selection_canvas.filenames[text_id] = file_path
            self.file_selection_canvas.filenames[bg_rect] = file_path

            self.file_selection_canvas.file_icon_ids[file_path] = icon_id
            self.file_selection_canvas.file_bg_ids[file_path] = bg_rect

            if icon_id in self.selected_files or (
                    file_path in self.file_selection_canvas.file_icon_ids and
                    self.file_selection_canvas.file_icon_ids[file_path] in self.selected_files
            ):
                self.file_selection_canvas.itemconfig(bg_rect, fill="#add8e6", outline="#4682b4")
                if icon_id not in self.selected_files:
                    self.selected_files.append(icon_id)

            col += 1
            if col >= icons_per_row:
                col = 0
                row += 1


        total_rows = (len(self.added_files) + icons_per_row - 1) // icons_per_row
        canvas_height = margin_y + (total_rows * icon_height) + margin_y
        canvas_width = margin_x + (min(len(self.added_files), icons_per_row) * icon_width)
        self.file_selection_canvas.config(scrollregion=(0, 0, canvas_width, canvas_height))

    def setup_rectangle_selection(self):
        """Set up variables and bindings for rectangle selection."""
        self.rect_select_start_x = None
        self.rect_select_start_y = None
        self.rect_select_current = None
        self.rect_selection_active = False

        # Bind events for rectangle selection
        self.file_selection_canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.file_selection_canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.file_selection_canvas.bind("<ButtonRelease-1>", self.on_mouse_up)

    def on_mouse_down(self, event):
        """Handle mouse button press event."""
        if not self.added_files:
            return

        canvas_x = self.file_selection_canvas.canvasx(event.x)
        canvas_y = self.file_selection_canvas.canvasy(event.y)

        clicked_items = self.file_selection_canvas.find_overlapping(canvas_x - 1, canvas_y - 1, canvas_x + 1, canvas_y + 1)

        if clicked_items:
            clicked_id = clicked_items[0]
            if clicked_id in self.file_selection_canvas.filenames:
                file_path = self.file_selection_canvas.filenames[clicked_id]
                icon_id = self.file_selection_canvas.file_icon_ids.get(file_path)
                bg_id = self.file_selection_canvas.file_bg_ids.get(file_path)
                if icon_id in self.selected_files:
                    self.deselect_file(file_path, bg_id)
                else:
                    self.select_file(file_path, bg_id)

                self.update_process_button_text()
                self.update_remove_button_visibility()
                return

        self.deselect_all_files()
        self.rect_select_start_x = canvas_x
        self.rect_select_start_y = canvas_y
        self.rect_selection_active = True

    def on_mouse_drag(self, event):
        """Handle mouse drag event for rectangle selection."""
        if not self.rect_selection_active:
            return

        canvas_x = self.file_selection_canvas.canvasx(event.x)
        canvas_y = self.file_selection_canvas.canvasy(event.y)

        if self.rect_select_current:
            self.file_selection_canvas.coords(
                self.rect_select_current,
                self.rect_select_start_x, self.rect_select_start_y,
                canvas_x, canvas_y
            )

        x0 = int(min(self.rect_select_start_x, canvas_x))
        y0 = int(min(self.rect_select_start_y, canvas_y))
        x1 = int(max(self.rect_select_start_x, canvas_x))
        y1 = int(max(self.rect_select_start_y, canvas_y))
        width = x1 - x0
        height = y1 - y0

        image = PIL.Image.new("RGBA", (width, height), (12, 18, 69, 40))
        draw = ImageDraw.Draw(image)

        dash_length = 4
        spacing = 2
        line_width = 2
        outline = (16, 22, 69, 150)

        # Top edge
        for i in range(0, width, dash_length + spacing):
            draw.line([(i, 0), (min(i + dash_length, width - line_width), 0)], fill=outline, width=line_width)
        # Bottom edge
        for i in range(0, width, dash_length + spacing):
            draw.line([(i, height - line_width), (min(i + dash_length, width - line_width), height - 1)], fill=outline, width=line_width)
        # Left edge
        for i in range(0, height, dash_length + spacing):
            draw.line([(0, i), (0, min(i + dash_length, height - line_width))], fill=outline, width=line_width)
        # Right edge
        for i in range(0, height, dash_length + spacing):
            draw.line([(width - line_width, i), (width - line_width, min(i + dash_length, height - line_width))], fill=outline, width=line_width)

        self.rect_select_current = PIL.ImageTk.PhotoImage(image)

        if hasattr(self, 'rect_image_id') and self.rect_image_id:
            self.file_selection_canvas.delete(self.rect_image_id)

        self.rect_image_id = self.file_selection_canvas.create_image(x0, y0, image=self.rect_select_current, anchor='nw')

    def on_mouse_up(self, event):
        """Handle mouse button release event."""
        if not self.rect_selection_active:
            return

        if self.rect_image_id:
            self.file_selection_canvas.delete(self.rect_image_id)

        canvas_x = self.file_selection_canvas.canvasx(event.x)
        canvas_y = self.file_selection_canvas.canvasy(event.y)

        x1 = min(self.rect_select_start_x, canvas_x)
        y1 = min(self.rect_select_start_y, canvas_y)
        x2 = max(self.rect_select_start_x, canvas_x)
        y2 = max(self.rect_select_start_y, canvas_y)

        selected_items = self.file_selection_canvas.find_overlapping(x1, y1, x2, y2)

        selected_items = [item for item in selected_items if item != self.rect_select_current]

        file_paths_selected = set()
        for item in selected_items:
            if item in self.file_selection_canvas.filenames:
                file_path = self.file_selection_canvas.filenames[item]
                if file_path not in file_paths_selected:
                    icon_id = self.file_selection_canvas.file_icon_ids.get(file_path)
                    bg_id = self.file_selection_canvas.file_bg_ids.get(file_path)
                    self.select_file(file_path, bg_id)
                    file_paths_selected.add(file_path)

        if self.rect_select_current:
            self.file_selection_canvas.delete(self.rect_select_current)

        self.rect_select_start_x = None
        self.rect_select_start_y = None
        self.rect_select_current = None
        self.rect_selection_active = False

        self.update_process_button_text()
        self.update_remove_button_visibility()

    def _on_results_canvas_click(self, event):
        y = self.results_canvas.canvasy(event.y)

        clicked_inside_a_row = False
        for row in self.result_file_widgets.values():
            row_y = row.winfo_y()
            row_height = row.winfo_height()
            if row_y <= y <= row_y + row_height:
                clicked_inside_a_row = True
                break

        if not clicked_inside_a_row:
            self.clear_result_selections()

    def remove_drag_drop_label(self):
        if hasattr(self, 'drag_drop_label') and self.drag_drop_label:
            self.drag_drop_label.destroy()
            self.drag_drop_label = None
            self.file_selection_canvas.config(bg="white")

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

    def update_save_button_text(self):
        if not self.save_button:
            return
        count = len(self.selected_save_paths)
        if count == 0:
            self.save_button.config(text="Save All Files")
        else:
            self.save_button.config(text=f"Save {count} File{'s' if count > 1 else ''}")

    def update_remove_button_visibility(self):
        if self.selected_files:
            self.remove_button.pack(side="right", padx=2, pady=2)
        else:
            self.remove_button.pack_forget()

    def select_file(self, file_path, bg_id):
        self.file_selection_canvas.itemconfig(bg_id, fill="#add8e6", outline="#4682b4")
        self.selected_files.append(self.file_selection_canvas.file_icon_ids[file_path])
        self.log_message(f"Selected file: {os.path.basename(file_path)}")

    def toggle_file_selection(self, file_path, row_widget, selection_set, selected_color="#add8e6",
                              default_color="#ffffff"):
        """Generic toggler for selecting/deselecting a file row with dynamic border."""
        if file_path in selection_set:
            selection_set.remove(file_path)
            row_widget.config(
                bg=default_color,
                highlightthickness=0,
            )
            for widget in row_widget.winfo_children():
                widget.config(bg=default_color)
        else:
            selection_set.add(file_path)
            self.update_save_button_text()
            row_widget.config(
                bg=selected_color,
                highlightbackground="#1E3A8A",  # deep blue
                highlightcolor="#1E3A8A",
                highlightthickness=2  # visually distinct border
            )
            for widget in row_widget.winfo_children():
                widget.config(bg=selected_color)

        self.update_save_button_text()

    def deselect_file(self, file_path, bg_id):
        self.file_selection_canvas.itemconfig(bg_id, fill="", outline="")
        if self.file_selection_canvas.file_icon_ids[file_path] in self.selected_files:
            self.selected_files.remove(self.file_selection_canvas.file_icon_ids[file_path])
        self.log_message(f"Deselected file: {os.path.basename(file_path)}")

    def deselect_all_files(self):
        self.deselect_all(
            self.added_files,
            self.file_selection_canvas.file_bg_ids,
            self.selected_files,
            lambda i: ""  # canvas fills are already alternating by shape
        )
        self.log_message(f"Deselected {len(self.selected_files)} files")
        self.selected_files = []
        self.update_process_button_text()
        self.update_save_button_text()
        self.update_remove_button_visibility()

    def clear_result_selections(self):
        self.deselect_all(
            # list(self.selected_save_paths),
            self.result_file_widgets,
            self.selected_save_paths,
            lambda i: "#ffffff" if i % 2 == 0 else "#f5f5f5"
        )
        self.update_save_button_text()

    def deselect_all(self, file_paths, widget_map, selection_set, background_func):
        for index, file_path in enumerate(file_paths):
            if file_path not in widget_map:
                continue

            widget = widget_map[file_path]
            bg_color = background_func(index)

            # Canvas-based widgets (file selection view)
            if isinstance(widget, int):
                self.file_selection_canvas.itemconfig(widget, fill="", outline="")
                if widget in selection_set:
                    selection_set.remove(widget)

            # Frame-based widgets (results view)
            elif isinstance(widget, Frame):
                widget.config(bg=bg_color, highlightthickness=0)
                for child in widget.winfo_children():
                    child.config(bg=bg_color)

                if file_path in selection_set:
                    selection_set.remove(file_path)
        self.update_save_button_text()

    def get_selected_files(self):
        selected_paths = []
        for icon_id in self.selected_files:
            if icon_id in self.file_selection_canvas.filenames:
                selected_paths.append(self.file_selection_canvas.filenames[icon_id])
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

    def get_selected_result_paths(self):
        return list(self.selected_save_paths)

    def show_info(self, title, message):
        messagebox.showinfo(title, message, parent=self.root)

    def handle_results(self):
        # Implementation to handle and display OCR results

        pass
