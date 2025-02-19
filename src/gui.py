import os
from tkinter import filedialog, messagebox, Toplevel, Text, Scrollbar
import tkinter as tk

try:
    from Tkinter import *
except ImportError:
    from tkinter import *

import tkinterdnd2
from tkinterdnd2 import DND_FILES
from ocr import extract_text_from_pdf  # Import the OCR function
from config import set_tesseract_path

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


class GUI:
    def __init__(self, master):
        self.master = master
        self.master.withdraw()
        self.master.title("R&D Labs Directory Parser")
        Label(self.master, text='Drag and drop files here:').grid(row=0, column=0, padx=10, pady=5)
        self.master.geometry("550x400")

        self.frames = {}
        self.create_frames()
        self.update_screen("file_selection")

        self.added_files = set()

        global file_icon
        file_icon = PhotoImage(data=file_pic_base_64)

    def create_frames(self):
        self.frames["file_selection"] = self.create_file_selection_frame()
        self.frames["processing"] = self.create_processing_frame()
        self.frames["results"] = self.create_results_frame()
        self.frames["completion"] = self.create_completion_frame()

    def update_screen(self, state):
        pass

    def create_file_selection_frame(self):
        self.master.grid_rowconfigure(1, weight=1)
        self.master.grid_columnconfigure(0, weight=1)

        main_frame = Frame(self.master)
        main_frame.grid(row=1, column=0, padx=5, pady=5, sticky='news')

        self.master.grid_rowconfigure(1, weight=1)
        self.master.grid_columnconfigure(0, weight=1)

        self.canvas = Canvas(main_frame, bg='white', relief='sunken', bd=1)
        self.canvas.grid(row=0, column=0, padx=5, pady=5, sticky='news')

        self.scrollbar = Scrollbar(main_frame, orient='vertical', command=self.canvas.yview)
        self.scrollbar.grid(row=0, column=1, sticky='ns')

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.inner_frame = Frame(self.canvas, bg='lightgray')
        self.inner_window = self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")

        self.inner_frame.bind("<Configure>", self.update_scrollregion)

        self.canvas.bind_all("<MouseWheel>", self.on_mousewheel)
        self.canvas.bind_all("<Button-4>", self.on_mousewheel)
        self.canvas.bind_all("<Button-5>", self.on_mousewheel)

        self.canvas.drop_target_register(DND_FILES)
        self.canvas.dnd_bind("<<Drop>>", self.drop)

        self.canvas.filenames = {}
        self.canvas.nextcoords = [60, 20]
        self.canvas.dragging = False

        self.canvas.drag_source_register(1, DND_FILES)
        self.canvas.dnd_bind('<<DragInitCmd>>', self.drag_init)
        self.canvas.dnd_bind('<<DragEndCmd>>', self.drag_end)

        self.canvas.configure(borderwidth=0, relief="solid", highlightthickness=0)

        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        bottom_frame = Frame(self.master)
        bottom_frame.grid(row=2, column=0, columnspan=2, pady=10, sticky="ew")

        self.status_label = Label(bottom_frame, text="", fg="black", anchor="w", width=50)
        self.status_label.pack(side="left", padx=10)

        self.select_button = Button(bottom_frame, text="Select Files", command=self.select_files)
        self.select_button.pack(side="right", padx=10)

        # Add OCR button
        self.ocr_button = Button(bottom_frame, text="Run OCR", command=self.run_ocr)
        self.ocr_button.pack(side="right", padx=10)

        return self

    def create_processing_frame(self):
        pass

    def create_results_frame(self):
        pass

    def create_completion_frame(self):
        pass

    def update_status(self, valid, duplicate, invalid):
        status_parts = []
        if valid > 0:
            status_parts.append(f"Added {valid} VALID File{'s' if valid > 1 else ''}")
        if duplicate > 0:
            status_parts.append(f"Skipped {duplicate} DUPLICATE{'S' if duplicate > 1 else ''}")
        if invalid > 0:
            status_parts.append(f"Ignored {invalid} NON-VALID File{'s' if invalid > 1 else ''}")

        self.status_label.config(text=" | ".join(status_parts), fg="blue")

    def select_files(self):
        file_paths = filedialog.askopenfilenames(title="Select PDF Files", filetypes=[("PDF Files", "*.pdf")], multiple=True)

        valid_count, duplicate_count, invalid_count = 0, 0, 0

        if file_paths:
            for file_path in file_paths:
                if file_path in self.added_files:
                    print(f"Skipping Previously Added File: {file_path}")
                    duplicate_count += 1
                    continue
                self.add_file_to_canvas(file_path)
                valid_count += 1

        self.update_status(valid_count, duplicate_count, invalid_count)

    def add_file_to_canvas(self, file_path):
        id1 = self.canvas.create_image(self.canvas.nextcoords[0], self.canvas.nextcoords[1], image=file_icon, anchor='n',
                                       tags=('file',))
        id2 = self.canvas.create_text(self.canvas.nextcoords[0], self.canvas.nextcoords[1] + 50,
                                      text=os.path.basename(file_path), anchor='n', justify='center', width=90)

        self.canvas.filenames[id1] = file_path
        self.canvas.filenames[id2] = file_path

        if self.canvas.nextcoords[0] > 450:
            self.canvas.nextcoords = [60, self.canvas.nextcoords[1] + 130]
        else:
            self.canvas.nextcoords = [self.canvas.nextcoords[0] + 100, self.canvas.nextcoords[1]]

        self.added_files.add(file_path)
        print("Added file: ", file_path)

        self.update_scrollregion()

    def is_pdf(self, file_path):
        return file_path.lower().endswith('.pdf')

    def drop(self, event):
        if self.canvas.dragging:
            return tkinterdnd2.REFUSE_DROP
        if event.data:
            files = self.canvas.tk.splitlist(event.data)
            valid_count, duplicate_count, invalid_count = 0, 0, 0
            for file_path in files:
                if not self.is_pdf(file_path):
                    print(f"Rejected Non-PDF File: {file_path}")
                    invalid_count += 1
                    continue
                if file_path in self.added_files:
                    print(f"Skipping Previously Added File: {file_path}")
                    duplicate_count += 1
                    continue
                self.add_file_to_canvas(file_path)

            self.update_status(valid_count, duplicate_count, invalid_count)

        return event.action

    def drag_init(self, event):
        data = ()
        x, y = self.canvas.winfo_pointerxy()
        canvas_x = self.canvas.canvasx(x)
        canvas_y = self.canvas.canvasy(y)

        item = self.canvas.find_closest(canvas_x, canvas_y)
        if item:
            self.canvas.dragging = True
            data = (self.canvas.filenames.get(item[0]),)
            self.canvas.focus.set()
            return ((tkinterdnd2.ASK, tkinterdnd2.COPY), (tkinterdnd2.DND_FILES, tkinterdnd2.DND_TEXT), data)
        else:
            return 'break'

    def drag_end(self, event):
        self.canvas.dragging = False

    def update_scrollregion(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_mousewheel(self, event):
        if event.delta:
            self.canvas.yview_scroll(-1 * (event.delta // 120), "units")
        elif event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")

    def run_ocr(self):
        # Check if files are added
        if not self.added_files:
            messagebox.showwarning("No Files", "No PDF files have been added.")
            return

        # Set the Tesseract path
        try:
            set_tesseract_path()  # Call the function from config.py
        except FileNotFoundError as e:
            messagebox.showerror("Tesseract Error", str(e))
            return

        # Create a new window to display OCR results
        ocr_window = Toplevel(self.master)
        ocr_window.title("OCR Results")
        ocr_window.geometry("600x400")

        # Add a text widget to display the extracted text
        text_widget = Text(ocr_window, wrap="word")
        text_widget.pack(fill="both", expand=True, padx=10, pady=10)

        # Add a scrollbar
        scrollbar = Scrollbar(ocr_window, command=text_widget.yview)
        scrollbar.pack(side="right", fill="y")
        text_widget.config(yscrollcommand=scrollbar.set)

        # Perform OCR on each file and display the results
        for file_path in self.added_files:
            try:
                extracted_text = extract_text_from_pdf(file_path)  # Assuming this uses pytesseract
                text_widget.insert("end", f"=== {os.path.basename(file_path)} ===\n")
                text_widget.insert("end", extracted_text + "\n\n")
            except Exception as e:
                text_widget.insert("end", f"Error processing {file_path}: {str(e)}\n\n")

        # Disable editing in the text widget
        text_widget.config(state="disabled")