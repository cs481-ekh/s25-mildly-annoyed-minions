import tkinter as tk
from tkinter import filedialog


class GUI:
    def __init__(self, master):
        self.master = master
        self.master.title("R&D Labs Directory Parser")
        self.master.geometry("500x500")

        self.file_frame = tk.LabelFrame(master, text="Select Files to Parse", padx=20, pady=20)
        self.file_frame.pack(padx=10, pady=10, fill="x")

        self.select_button = tk.Button(self.file_frame, text="Select Files", command=self.manual_file_select)
        self.select_button.pack()

    def manual_file_select(self):
        file_paths = filedialog.askopenfilenames(title="Select Files", filetypes=[("PDF files", "*.pdf")])
        if file_paths:
            print("Selected files:", file_paths)
