import tkinter as tk
from tkinter import ttk, filedialog, font
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mpl_toolkits.mplot3d import Axes3D
from sklearn.datasets import load_digits
from umap import UMAP
import socket
import numpy as np
import threading
from config import *
import os
import msgpack

path = os.path.dirname(os.path.abspath(__file__))

class Program:
    def __init__(self):
        # Nota, el dataset esta hardcodeado por ahora
        with open(path + "/" + "dataset/dataset.mpack", "rb") as f:
            self.dataset = msgpack.load(f)
        self.root = tk.Tk()
        self.window_width = 1280
        self.window_height = 720
        paned_window = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)
        self.left_frame = ttk.Frame(paned_window, width=self.window_width // 5)
        self.left_frame.pack_propagate(False)
        paned_window.add(self.left_frame, weight=0)
        self.plot_frame = ttk.Frame(paned_window, width=self.window_width * 3 // 5)
        self.plot_frame.pack_propagate(False)
        paned_window.add(self.plot_frame, weight=0)
        self.right_frame = ttk.Frame(paned_window, width=self.window_width // 5)
        self.right_frame.pack_propagate(False)
        paned_window.add(self.right_frame, weight=0)
        
        print("Creando socket...")
        self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listener.bind(("192.168.103.100", 5000))
        self.listener.listen()
        print("Esperando conexion...")
        conn, addr = self.listener.accept()
        self.conn = conn
        print("Navegador conectado")
        
        self.data =  load_digits().data #np.random.rand(10, 4)
        client_thread = threading.Thread(target=self.receive_messages)
        client_thread.daemon = True
        client_thread.start()
        self.params = {
            "umap_metric": tk.StringVar(value="euclidean"),
            "umap_n_neighbors": tk.StringVar(value="15"),
            "umap_min_dist": tk.StringVar(value="0.01"),
            "hdbscan_metric": tk.StringVar(value="euclidean"),
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

        reduction = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="Método de reducción", menu=reduction)
        reduction.add_command(label="UMAP", command=self.load_umap())
        reduction.add_command(label="T-SNE", command=self.load_tsne())
        reduction.add_command(label="PCA", command=self.load_pca())

        about = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="Acerca de", menu=about)
        about.add_command(label="Acerca de", command=self.about)

        exit = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="Salir", menu=exit)
        exit.add_command(label="Salir", command=self.root.destroy)
        
        umap = UMAP(metric="euclidean", n_neighbors=15, min_dist=0.1, n_components=3)
        self.data = umap.fit_transform(self.dataset["vectors"])
        self.colors = [(0.0, 0.0, 0.0) for _ in range(self.dataset["size"])]
        self.create_plot()
        self.update_plot()
        self.conn.sendall(msgpack.packb({"type": "dataset", "points": self.data.tolist()}))
        self.load_left_frame()
        self.load_right_frame()

    # Seleccionar carpeta desde un file browser
    def load(self):
        folder_selected = filedialog.askdirectory()
        print(folder_selected)
        # Procesar imagenes
    
    def load_umap(self):
        pass
    def load_tsne(self):
        pass
    def load_pca(self):
        pass

    def save(self):
        pass

    def about(self):
        about_window = tk.Toplevel(self.root)
        about_window.title("Acerca de")
        about_window.geometry("300x200")
        about_label = tk.Label(about_window, text=ABOUT_TXT, justify="center")
        about_label.pack(expand=True, fill='both', padx=10, pady=10)

    def create_plot(self):
        fig = Figure(figsize=(self.window_width * 3 // 4 / 100, self.window_height / 100), dpi=100)
        self.ax = fig.add_subplot(111, projection='3d')
        self.ax.set_xlabel('X Label')
        self.ax.set_ylabel('Y Label')
        self.ax.set_zlabel('Z Label')
        self.ax.axis('equal')
        self.ax.axis('off')
        self.canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    
    def update_plot(self):
        self.ax.scatter(self.data[:,0], self.data[:,1], self.data[:,2], c=self.colors)
        self.canvas.draw()

    def receive_messages(self):
        unpacker = msgpack.Unpacker()
        while True:
            data = self.conn.recv(64)
            if not data:
                break
            unpacker.feed(data)
            for msg in unpacker:
                if msg['type'] == 'request_img':
                    idx = msg['index']
                    with open(path + "/" + self.dataset["folder_path"] + "/" + self.dataset["names"][idx], 'rb') as f:
                        img = bytearray(f.read())
                    img_msg = {
                        'type': 'response_img',
                        'txt': self.dataset["names"][idx],
                        'img': img,
                        'coords': self.data[idx].tolist(),
                    }
                    # print(img_msg)
                    self.conn.sendall(msgpack.packb(img_msg))
                    
                elif msg['type'] == 'selection':
                    for i in msg['indexes']:
                        self.colors[i] = (1.0, 0.0, 0.0)
                    self.update_plot()

                elif msg['type'] == 'clear_selection':
                    self.colors = [(0.0, 0.0, 0.0) for _ in range(len(self.data))]
                    self.update_plot()

    def load_left_frame(self):
        tk.Label(self.left_frame, text="Opciones", font=font.Font(size=15, weight="bold")).pack(pady=10)
        tk.Label(self.left_frame, text="Métrica").pack()
        tk.OptionMenu(self.left_frame, self.params["umap_metric"], *["euclidean", "manhattan", "cosine"]).pack()
        tk.Label(self.left_frame, text="Nro. de vecinos").pack()
        tk.Entry(self.left_frame, textvariable=self.params["umap_n_neighbors"]).pack()
        tk.Label(self.left_frame, text="Distancia mínima").pack()
        tk.Entry(self.left_frame, textvariable=self.params["umap_min_dist"]).pack()
        tk.Button(self.left_frame, text="Actualizar", command=self.update_visualization).pack()
    
    def load_right_frame(self):
        tk.Label(self.right_frame, text="Opciones HDBScan", font=font.Font(size=15, weight="bold")).pack(pady=10)

    def update_visualization(self):
        # Obtener valores de los parámetros
        metric = self.params["umap_metric"].get()
        n_neighbors = int(self.params["umap_n_neighbors"].get())
        min_dist = float(self.params["umap_min_dist"].get())

        # Aplicar uMAP con los parámetros seleccionados
        umap = UMAP(metric=metric, n_neighbors=n_neighbors, min_dist=min_dist, n_components=3)
        self.data = umap.fit_transform(self.dataset["vectors"])
        self.colors = [(0.0, 0.0, 0.0) for _ in range(self.dataset["size"])]
        self.update_plot()
        self.conn.sendall(msgpack.packb({"type": "dataset", "points": self.data.tolist()}))