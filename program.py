import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
from config import *

class Program:
    def __init__(self):
        self.root = tk.Tk()
        self.window_width = 1280
        self.window_height = 720
        paned_window = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)
        self.side_frame = ttk.Frame(paned_window, width=self.window_width // 4)
        paned_window.add(self.side_frame)
        self.plot_frame = ttk.Frame(paned_window, width=self.window_width * 3 // 4)
        paned_window.add(self.plot_frame)
        self.configure()

    def start(self):
        self.root.mainloop()

    def configure(self):
        self.root.title("Dataverse")
        self.root.resizable(0, 0)
        self.root.option_add("*Foreground", TEXT)
        self.root.option_add("*Background", BACKGROUND)
        self.root.option_add("*Button.Foreground", TEXT)
        self.root.option_add("*Button.Background", BACKGROUND)
        self.root.option_add("*Label.Foreground", TEXT)
        self.root.option_add("*Label.Background", BACKGROUND)
        self.root.option_add("*Entry.Foreground", TEXT)
        self.root.option_add("*Entry.Background", BACKGROUND)
        self.center_window()
        self.load_window()
        points = np.array([
            [1, 2, 3],
            [4, 5, 6],
            [7, 8, 9],
            [10, 11, 12],
            [13, 14, 15],
            [16, 17, 18],
            [19, 20, 21],
            [22, 23, 24],
            [25, 26, 27],
            [28, 29, 30]
        ])
        self.create_plot(points)

    def center_window(self):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (self.window_width // 2)
        y = (screen_height // 2) - (self.window_height // 2)
        self.root.geometry(f"{self.window_width}x{self.window_height}+{x}+{y}")

    def load_window(self):
        menu = tk.Menu(self.root)
        self.root.config(menu=menu)
    
        file = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="Archivo", menu=file)
        file.add_command(label="Cargar imágenes", command=self.load)
        file.add_command(label="Guardar resultados", command=self.save)

        config = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="Configuración", menu=config)
        config.add_command(label="Seleccionar método", command=self.select_method)
        config.add_command(label="Modificar parámetros", command=self.modify_params)

        about = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="Acerca de", menu=about)
        about.add_command(label="Acerca de", command=self.about)

        exit = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="Salir", menu=exit)
        exit.add_command(label="Salir", command=self.root.destroy)

    def load(self):
        folder_selected = filedialog.askdirectory()
        print(folder_selected)
        # Procesar imagenes

    def save(self):
        pass

    def select_method(self):
        pass

    def modify_params(self):
        pass

    def about(self):
        about_window = tk.Toplevel(self.root)
        about_window.title("Acerca de")
        about_window.geometry("300x200")
        about_label = tk.Label(about_window, text=ABOUT_TXT, justify="center")
        about_label.pack(expand=True, fill='both', padx=10, pady=10)

    def create_plot(self, points):
        fig = Figure(figsize=(self.window_width * 3 // 4 / 100, self.window_height / 100), dpi=100)
        ax = fig.add_subplot(111, projection='3d')
        ax.scatter(points[:, 0], points[:, 1], points[:, 2], c = COLOR)
        ax.set_xlabel('X Label')
        ax.set_ylabel('Y Label')
        ax.set_zlabel('Z Label')
        ax.axis('equal')
        ax.axis('off')
        canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)