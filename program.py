import tkinter as tk
from tkinter import ttk, filedialog, font
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mpl_toolkits.mplot3d import Axes3D
from umap import UMAP
import bson
import socket
import numpy as np
import threading
from config import *


class Program:
    def __init__(self):
        self.root = tk.Tk()
        self.window_width = 1280
        self.window_height = 720
        paned_window = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)
        self.side_frame = ttk.Frame(paned_window, width=self.window_width // 4)
        self.side_frame.pack_propagate(False)
        paned_window.add(self.side_frame, weight=0)
        self.plot_frame = ttk.Frame(paned_window, width=self.window_width * 3 // 4)
        self.plot_frame.pack_propagate(False)
        paned_window.add(self.plot_frame, weight=0)
        self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listener.bind((IP, PORT))
        self.conn = None
        self.data = np.random.rand(100, 3)
        client_thread = threading.Thread(target=self.handle_connection)
        client_thread.daemon = True
        client_thread.start()
        self.params = {
            "metric": tk.StringVar(value="euclidean"),
            "n_neighbors": tk.StringVar(value="15"),
            "min_dist": tk.StringVar(value="0.01"),
        }
        self.configure()
    def start(self):
        self.root.mainloop()

    def configure(self):
        self.root.title("Dataverse - Controlador")
        self.root.resizable(0, 0)
        self.root.option_add("*Foreground", TEXT)
        self.root.option_add("*Background", BACKGROUND)
        self.center_window()
        self.load_window()

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

        about = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="Acerca de", menu=about)
        about.add_command(label="Acerca de", command=self.about)

        exit = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="Salir", menu=exit)
        exit.add_command(label="Salir", command=self.root.destroy)
        self.create_plot(self.data)
        self.load_side_frame()

    def load(self):
        folder_selected = filedialog.askdirectory()
        print(folder_selected)
        # Procesar imagenes

    def save(self):
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
        ax.scatter(points[:, 0], points[:, 1], points[:, 2], c = [COLOR[idx % len(COLOR)] for idx in range(len(points))])
        ax.set_xlabel('X Label')
        ax.set_ylabel('Y Label')
        ax.set_zlabel('Z Label')
        ax.axis('equal')
        ax.axis('off')
        canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    def handle_connection(self):
        self.listener.listen()
        print("Esperando conexion...")
        self.conn, addr = self.listener.accept()
        print("Navegador conectado")
        while True:
            msg = self.conn.recv(1024)
            print(msg)
            if not msg:
                break
            msg = bson.loads(msg)

    def load_side_frame(self):
        tk.Label(self.side_frame, text="Opciones", font=font.Font(size=15, weight="bold")).pack(pady=10)
        tk.Label(self.side_frame, text="Métrica").pack()
        tk.OptionMenu(self.side_frame, self.params["metric"], *["euclidean", "manhattan", "cosine"]).pack()
        tk.Label(self.side_frame, text="Nro. de vecinos").pack()
        tk.Entry(self.side_frame, textvariable=self.params["n_neighbors"]).pack()
        tk.Label(self.side_frame, text="Distancia mínima").pack()
        tk.Entry(self.side_frame, textvariable=self.params["min_dist"]).pack()
        tk.Button(self.side_frame, text="Actualizar", command=self.update_visualization).pack()

    def update_visualization(self):
        # Obtener valores de los parámetros
        metric = self.params["metric"].get()
        n_neighbors = int(self.params["n_neighbors"].get())
        min_dist = float(self.params["min_dist"].get())

        # Aplicar uMAP con los parámetros seleccionados
        umap = UMAP(metric=metric, n_neighbors=n_neighbors, min_dist=min_dist, n_components=3, random_state=42)
        msg = {"points": umap.fit_transform(self.data).tolist()}
        msg = bson.dumps(msg)
        print("Tamaño", len(msg))
        print("Enviando puntos al navegador...")
        self.conn.sendall(msg)
        print("Puntos enviados")