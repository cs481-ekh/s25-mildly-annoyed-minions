import tkinter as tk

class GUI:
    def __init__(self, master):
        self.master = master
        self.master.title("R&D Labs Directory Parser")
        self.master.geometry("500x500")

        self.label = tk.Label(self.master, text="Test Content")
        self.label.pack(pady=20)