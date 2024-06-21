import tkinter as tk
from tkinter import ttk, filedialog, font
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mpl_toolkits.mplot3d import Axes3D
from sklearn.datasets import load_digits
from sklearn.cluster import HDBSCAN
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from umap import UMAP
import socket
import numpy as np
import threading
from config import *
import os
import msgpack
import matplotlib.cm as cm

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
        
        self.params = {
            "umap_metric": tk.StringVar(value="euclidean"),
            "umap_n_neighbors": tk.StringVar(value="15"),
            "umap_min_dist": tk.StringVar(value="0.01"),
            "tsne_metric": tk.StringVar(value="euclidean"),
            "tsne_perplexity": tk.StringVar(value="30"),
            "tsne_learning_rate": tk.StringVar(value="200"),
            "tsne_early_exaggeration": tk.StringVar(value="12"),
            "pca_whiten": tk.BooleanVar(value=True),
            "pca_svd_solver": tk.StringVar(value="auto"),
            "pca_tol": tk.StringVar(value="0.0"),
            "hdbscan_metric": tk.StringVar(value="euclidean"),
            "hdbscan_min_cluster_size": tk.StringVar(value="5"),
            "hdbscan_cluster_selection_method": tk.StringVar(value="eom"),
            "hdbscan_algorithm": tk.StringVar(value="auto"),
        }
        self.reduction_method = "umap"
        self.reduction_options = {}
        self.load_reduction_options()
        print("Creando socket...")
        self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listener.bind(("127.0.0.1", 5000))
        self.listener.listen()
        print("Esperando conexion...")
        conn, addr = self.listener.accept()
        self.conn = conn
        print("Navegador conectado")
        
        self.data =  load_digits().data
        client_thread = threading.Thread(target=self.receive_messages)
        client_thread.daemon = True
        client_thread.start()
        self.configure()
        
    def start(self):
        self.root.mainloop()

    def configure(self):
        self.root.title("Dataverse - Controlador")
        self.root.resizable(0, 0)
        self.root.option_add("*Foreground", TEXT)
        self.root.option_add("*Background", BACKGROUND)
        self.root.option_add("*Label.background", BACKGROUND)
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
        reduction.add_command(label="UMAP", command=lambda: self.update_left_frame("umap"))
        reduction.add_command(label="T-SNE", command=lambda: self.update_left_frame("tsne"))
        reduction.add_command(label="PCA", command=lambda: self.update_left_frame("pca"))
        about = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="Acerca de", menu=about)
        about.add_command(label="Acerca de", command=self.about)
        exit = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="Salir", menu=exit)
        exit.add_command(label="Salir", command=self.root.destroy)
        umap = UMAP(metric="euclidean", n_neighbors=15, min_dist=0.1, n_components=3, random_state=42)
        self.data = umap.fit_transform(self.dataset["vectors"])
        self.colors = [(1.0, 1.0, 1.0) for _ in range(self.dataset["size"])]
        self.edgecolors = [(0.0, 0.0, 0.0) for _ in range(self.dataset["size"])]
        self.create_plot()
        self.update_plot()
        self.conn.sendall(msgpack.packb({"type": "dataset", "points": self.data.tolist()}))
        self.update_left_frame(self.reduction_method)
        self.load_right_frame()

    # Seleccionar carpeta desde un file browser
    def load(self):
        folder_selected = filedialog.askdirectory()
        print(folder_selected)
        # Procesar imagenes

    def save(self):
        pass

    def about(self):
        about_window = tk.Toplevel(self.root)
        about_window.title("Acerca de")
        x = self.window_width // 2 - 150
        y = self.window_height // 2 - 100
        about_window.geometry(f"300x200+{x}+{y}")
        about_label = tk.Label(about_window, text=ABOUT_TXT, justify="center")
        about_label.pack(expand=True, fill='both', padx=10, pady=10)

    def create_plot(self):
        fig = Figure(figsize=(self.window_width / 100, self.window_height / 100), dpi=100)
        self.ax = fig.add_subplot(111, projection='3d')
        self.ax.axis('equal')
        self.ax.axis('off')
        self.canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    
    def update_plot(self):
        self.ax.scatter(self.data[:,0], self.data[:,1], self.data[:,2], c=self.colors, edgecolors=self.edgecolors)
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
                        self.edgecolors[i] = (1.0, 0.0, 0.0)
                    print(self.edgecolors)
                    self.update_plot()

                elif msg['type'] == 'clear_selection':
                    self.edgecolors = [(0.0, 0.0, 0.0) for _ in range(len(self.data))]
                    self.update_plot()

    def load_reduction_options(self):
        self.reduction_options = {
            "umap": tk.Frame(self.left_frame),
            "tsne": tk.Frame(self.left_frame),
            "pca": tk.Frame(self.left_frame),
        }
        tk.Label(self.reduction_options["umap"], text="Opciones UMAP", font=font.Font(size=15, weight="bold")).pack(pady=10)
        tk.Label(self.reduction_options["umap"], text="Métrica").pack(pady = 5)
        tk.OptionMenu(self.reduction_options["umap"], self.params["umap_metric"], *["euclidean", "manhattan", "cosine"]).pack(pady = 5)
        tk.Label(self.reduction_options["umap"], text="Nro. de vecinos").pack(pady = 5)
        tk.Entry(self.reduction_options["umap"], textvariable=self.params["umap_n_neighbors"]).pack(pady = 5)
        tk.Label(self.reduction_options["umap"], text="Distancia mínima").pack(pady = 5)
        tk.Entry(self.reduction_options["umap"], textvariable=self.params["umap_min_dist"]).pack(pady = 5)
        tk.Button(self.reduction_options["umap"], text="Actualizar", command=self.update_visualization).pack(pady = 5)

        tk.Label(self.reduction_options["tsne"], text="Opciones TSNE", font=font.Font(size=15, weight="bold")).pack(pady=10)
        tk.Label(self.reduction_options["tsne"], text="Métrica").pack(pady = 5)
        tk.OptionMenu(self.reduction_options["tsne"], self.params["tsne_metric"], *["euclidean", "manhattan", "cosine"]).pack(pady = 5)
        tk.Label(self.reduction_options["tsne"], text="Perplejidad").pack(pady = 5)
        tk.Entry(self.reduction_options["tsne"], textvariable=self.params["tsne_perplexity"]).pack(pady = 5)
        tk.Label(self.reduction_options["tsne"], text="Tasa de aprendizaje").pack(pady = 5)
        tk.Entry(self.reduction_options["tsne"], textvariable=self.params["tsne_learning_rate"]).pack(pady = 5)
        tk.Label(self.reduction_options["tsne"], text="Exageración de aprendizaje").pack(pady = 5)
        tk.Entry(self.reduction_options["tsne"], textvariable=self.params["tsne_early_exaggeration"]).pack(pady = 5)
        tk.Button(self.reduction_options["tsne"], text="Actualizar", command=self.update_visualization).pack(pady = 5)

        tk.Label(self.reduction_options["pca"], text="Opciones PCA", font=font.Font(size=15, weight="bold")).pack(pady=10)
        tk.Label(self.reduction_options["pca"], text="Blanqueamiento").pack(pady = 5)
        tk.Checkbutton(self.reduction_options["pca"], variable=self.params["pca_whiten"]).pack(pady = 5)
        tk.Label(self.reduction_options["pca"], text="SVD Solver").pack(pady = 5)
        tk.OptionMenu(self.reduction_options["pca"], self.params["pca_svd_solver"], *["auto", "full", "arpack", "randomized"]).pack(pady = 5)
        tk.Label(self.reduction_options["pca"], text="Tolerancia").pack(pady = 5)
        tk.Entry(self.reduction_options["pca"], textvariable=self.params["pca_tol"]).pack(pady = 5)
        tk.Button(self.reduction_options["pca"], text="Actualizar", command=self.update_visualization).pack(pady = 5)

    def update_left_frame(self, method):
        self.reduction_method = method
        for key, frame in self.reduction_options.items():
            if key == self.reduction_method:
                frame.pack(expand=True, fill='both', padx=10, pady=10)
            else:
                frame.pack_forget()
    
    def load_right_frame(self):
        tk.Label(self.right_frame, text="Opciones HDBScan", font=font.Font(size=15, weight="bold")).pack(pady=10)
        tk.Label(self.right_frame, text="Métrica").pack(pady = 5)
        tk.OptionMenu(self.right_frame, self.params["hdbscan_metric"], *["euclidean", "manhattan", "cosine"]).pack(pady = 5)
        tk.Label(self.right_frame, text="Mínimo tamano de cluster").pack(pady = 5)
        tk.Entry(self.right_frame, textvariable=self.params["hdbscan_min_cluster_size"]).pack(pady = 5)
        tk.Label(self.right_frame, text="Método de selección de cluster").pack(pady = 5)
        tk.OptionMenu(self.right_frame, self.params["hdbscan_cluster_selection_method"], *["eom", "leaf"]).pack(pady = 5)
        tk.Label(self.right_frame, text="Algoritmo de clustering").pack(pady = 5)
        tk.OptionMenu(self.right_frame, self.params["hdbscan_algorithm"], *["auto", "brute", "kd_tree", "ball_tree"]).pack(pady = 5)
        tk.Button(self.right_frame, text="Actualizar", command=self.update_hdb_clustering).pack(pady = 5)

    def update_visualization(self):
        # Obtener valores de los parámetros
        metric = self.params["umap_metric"].get()
        n_neighbors = int(self.params["umap_n_neighbors"].get())
        min_dist = float(self.params["umap_min_dist"].get())

        # Aplicar uMAP con los parámetros seleccionados
        umap = UMAP(metric=metric, n_neighbors=n_neighbors, min_dist=min_dist, n_components=3, random_state=42)
        self.data = umap.fit_transform(self.dataset["vectors"])
        self.colors = [(1.0, 1.0, 1.0) for _ in range(self.dataset["size"])]
        self.edgecolors = [(0.0, 0.0, 0.0) for _ in range(self.dataset["size"])]
        self.update_plot()
        self.conn.sendall(msgpack.packb({"type": "dataset", "points": self.data.tolist()}))

    def update_hdb_clustering(self):
        # Obtener valores de los parámetros
        metric = self.params["hdbscan_metric"].get()
        min_cluster_size = int(self.params["hdbscan_min_cluster_size"].get())
        cluster_selection_method = self.params["hdbscan_cluster_selection_method"].get()
        algorithm = self.params["hdbscan_algorithm"].get()

        # Aplicar HDBScan con los parámetros seleccionados
        hdb = HDBSCAN(metric=metric, min_cluster_size=min_cluster_size, cluster_selection_method=cluster_selection_method, algorithm=algorithm)
        hdb.fit(self.data)
        self.colors = [cm.tab10(label) if label >= 0 else (1.0, 1.0, 1.0) for label in hdb.labels_]
        print(len(self.colors), len(self.edgecolors), len(hdb.labels_))
        self.update_plot()