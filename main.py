import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests

BASE_URL = "http://127.0.0.1:8000"  # Dirección de la API


class LoginWindow(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("Inicio de Sesión")
        self.geometry("400x300")
        self.resizable(False, False)
        
        tk.Label(self, text="Usuario:").pack(pady=10)
        self.user_entry = tk.Entry(self)
        self.user_entry.pack(pady=5)
        
        tk.Label(self, text="Contraseña:").pack(pady=10)
        self.password_entry = tk.Entry(self, show="*")
        self.password_entry.pack(pady=5)
        
        tk.Button(self, text="Iniciar Sesión", command=self.authenticate_user).pack(pady=20)
        self.credentials = None

    def authenticate_user(self):
        user = self.user_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not user or not password:
            messagebox.showerror("Error", "Por favor, completa todos los campos.")
            return
        
        try:    
            response = requests.post(f"{BASE_URL}/login", json={"user": user, "password": password})
            if response.status_code == 200:
                messagebox.showinfo("Éxito", "Inicio de sesión exitoso.")
                self.credentials = {"user": user, "password": password}
                self.destroy()  # Cerrar ventana de login
            else:
                messagebox.showerror("Error", response.json().get("detail", "Error desconocido en la conexión."))
        except requests.RequestException as e:
            messagebox.showerror("Error", f"No se pudo conectar al servidor:\n{e}")


class MainApplication(tk.Tk):
    def __init__(self, credentials):
        super().__init__()
        self.title("Depósitos Judiciales")
        self.geometry("800x600")
        self.credentials = credentials
        
        tk.Button(self, text="Cargar Archivo", command=self.upload_file).pack(pady=10)
        
        self.tree = ttk.Treeview(self, columns=("nombre_predio", "numero_proceso"), show="headings")
        self.tree.heading("nombre_predio", text="Nombre Predio")
        self.tree.heading("numero_proceso", text="Número Proceso")
        self.tree.pack(expand=True, fill="both")
        
    def upload_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xls *.xlsx")])
        if not file_path:
            return
        try:
            with open(file_path, "rb") as file:
                response = requests.post(
                    f"{BASE_URL}/upload",
                    files={"file": file},
                    data=self.credentials  # Pasar usuario y contraseña
                )
                if response.status_code == 200:
                    messagebox.showinfo("Éxito", "Archivo cargado correctamente.")
                else:
                    messagebox.showerror("Error", response.json().get("detail", "Error desconocido."))
        except requests.RequestException as e:
            messagebox.showerror("Error", f"No se pudo cargar el archivo:\n{e}")


if __name__ == "__main__":
    app = tk.Tk()
    app.withdraw()  # Ocultar la ventana principal inicialmente
    
    login_window = LoginWindow()
    login_window.wait_window()  # Esperar a que se cierre la ventana de login
    
    if login_window.credentials:
        main_app = MainApplication(login_window.credentials)
        main_app.mainloop()
