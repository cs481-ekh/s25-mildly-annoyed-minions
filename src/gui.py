import os
from tkinter import filedialog

try:
    from Tkinter import *
except ImportError:
    from tkinter import *

import tkinterdnd2
from tkinterdnd2 import DND_FILES

file_data = ('iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAMAAABg3Am1AAAAk1BMVEVHcEzJz9j/Vi/'
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

folder_data = ('iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAMAAACdt4HsAAAAP1BMVEVHcEz9zVz9yFn9'
               'ylv4tFL/zlv+zFv/z1zeoz34uVP9ylr+zlv/zlv+y1r/z1z5tVH/1V7/0V39wFf/wlj/'
               '3GFiE2TlAAAADnRSTlMAGqs8/PzC1AV4ZPKV35MoEK4AAAD+SURBVFjD7ZfLDoMgEEV5'
               'yFOlYPn/by20TVwIzMRZtAvOnuOFIYbLGGPWGRUurNpbhsFyneN1fYgxa44R8D03vl9Q'
               'KhuMQXTWV0Xe4PUypNAlKTjC1g9QIzjb5hSYOBQIMME62EEZxe6ayFMQAJ5thEUK1NLm'
               '8MziEjyaLIfAbqEn0JYqwCY4Ouxe4gQhNagDzknLepDhLirk6BlBUBRxlSRBuemaJigK'
               'SRPUH4YiCaKmCgzxDKiC3yeYgimYgimYgimYgn8UjAsH4o00rDzwK02MSxecwJfaR3rr'
               '8mHxhHfgvtX3lqJU409t6ZRveIRRvHttqaHN+g+x6toW2AtsZ8yuXHerXAAAAABJRU5E'
               'rkJggg==')


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

        global file_icon
        global folder_icon
        file_icon = PhotoImage(data=file_data)
        folder_icon = PhotoImage(data=folder_data)

        self.canvas = Canvas(self.master, bg='white', relief='sunken', bd=1)
        self.canvas.grid(row=1, column=0, padx=5, pady=5, sticky='news')

        self.scrollbar = Scrollbar(self.master, orient='vertical', command=self.canvas.yview)
        self.scrollbar.grid(row=1, column=1, sticky='ns')

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.inner_frame = Frame(self.canvas, bg='lightgray')
        self.inner_window = self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")

        self.inner_frame.bind("<Configure>", self.update_scrollregion)

        buttonbox = Frame(self.master)
        buttonbox.grid(row=2, column=0, columnspan=2, pady=5)
        Button(buttonbox, text='Select Files', command=self.select_files).pack(side=LEFT, padx=5)

        self.canvas.drop_target_register(DND_FILES)
        self.canvas.dnd_bind("<<Drop>>", self.drop)

        self.canvas.filenames = {}
        self.canvas.nextcoords = [60, 20]
        self.canvas.dragging = False

        self.canvas.drag_source_register(1, DND_FILES)
        self.canvas.dnd_bind('<<DragInitCmd>>', self.drag_init)
        self.canvas.dnd_bind('<<DragEndCmd>>', self.drag_end)

        return self

    def create_processing_frame(self):
        pass

    def create_results_frame(self):
        pass

    def create_completion_frame(self):
        pass

    def select_files(self):
        file_paths = filedialog.askopenfilenames(filetypes=[("PDF Files", "*.pdf")])
        if file_paths:
            for file_path in file_paths:
                self.add_file_to_canvas(file_path)

    def add_file_to_canvas(self, filename):
        if filename in self.added_files:
            print(f"Skipping already added file: {filename}")
            return

        icon = file_icon
        if os.path.isdir(filename):
            icon = folder_icon

        id1 = self.canvas.create_image(self.canvas.nextcoords[0], self.canvas.nextcoords[1], image=icon, anchor='n',
                                       tags=('file',))
        id2 = self.canvas.create_text(self.canvas.nextcoords[0], self.canvas.nextcoords[1] + 50,
                                      text=os.path.basename(filename), anchor='n', justify='center', width=90)

        self.canvas.filenames[id1] = filename
        self.canvas.filenames[id2] = filename

        if self.canvas.nextcoords[0] > 450:
            self.canvas.nextcoords = [60, self.canvas.nextcoords[1] + 130]
        else:
            self.canvas.nextcoords = [self.canvas.nextcoords[0] + 100, self.canvas.nextcoords[1]]

        self.added_files.add(filename)

        self.update_scrollregion()

    def drop_enter(event):
        event.widget.focus_force()
        print('Entering %s' % event.widget)
        return event.action

    def drop_position(event):
        return event.action

    def drop_leave(event):
        print('Leaving %s' % event.widget)
        return event.action

    def drop(self, event):
        if self.canvas.dragging:
            return tkinterdnd2.REFUSE_DROP
        if event.data:
            files = self.canvas.tk.splitlist(event.data)
            for f in files:
                self.add_file_to_canvas(f)
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