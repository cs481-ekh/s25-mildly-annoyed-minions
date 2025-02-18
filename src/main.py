from gui import GUI
from tkinterdnd2 import TkinterDnD

def main():

    root = TkinterDnD.Tk()
    app = GUI(root)
    root.update_idletasks()
    root.deiconify()
    root.mainloop()

if __name__ == '__main__':
    main()