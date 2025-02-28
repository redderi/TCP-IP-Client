import socket
import tkinter as tk
from tkinter import messagebox
from tkinter import PhotoImage
from PIL import Image, ImageTk 
from tkinter import filedialog, ttk
import os
import re
from res.style.styles import SEND_BUTTON_STYLE, CONNECT_BUTTON_STYLE
import threading
import time

from chardet.universaldetector import UniversalDetector

class MainWindow(tk.Tk):
    import tkinter as tk

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.file_data_dict = {}
        self.title("ipClient")
        self.geometry("800x700")
        self.resizable(False, False)
        self.configure(bg="#ADD8E6")
        self.iconphoto(True, self.resize_icon(".\\res\\icon\\mainWindow.png", 32, 32))
        self.button_icon = self.load_icon()

        self.connect_button = tk.Button(
            self, 
            text="Connect", 
            command=self.open_connection_window,
            **CONNECT_BUTTON_STYLE
        )
        self.connect_button.pack(anchor="nw", padx=10, pady=10)

        self.file_listbox = tk.Listbox(self, height=15, width=50)  
        self.file_listbox.pack(pady=5, side="top", fill="x", padx=10)  

        self.chat_display = tk.Text(self, state="disabled", height=15, width=50) 
        self.chat_display.pack(pady=5, fill="x", padx=10) 

        input_frame = tk.Frame(self)
        input_frame.pack(fill="x", padx=40, pady=20)

        self.message_entry = tk.Entry(
            input_frame, 
            font=("Arial", 14), 
            fg="#333333", 
            bg="#FFFFFF", 
            bd=2,  
            relief="solid"  
        )
        self.message_entry.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        self.message_entry.focus_set() 

        self.send_button = tk.Button(input_frame, text="Отправить", command=self.send_message, **SEND_BUTTON_STYLE)
        self.send_button.pack(side="left")

        self.upload_button = tk.Button(
            self, 
            text="Загрузить", 
            command=self.upload_file, 
            **SEND_BUTTON_STYLE  
        )
        self.upload_button.pack(side="left", padx=5, pady=5)

        self.download_button = tk.Button(
            self, 
            text="Скачать", 
            command=self.download_file, 
            **SEND_BUTTON_STYLE 
        )
        self.download_button.pack(side="left", padx=5, pady=5)

        self.progress_label = tk.Label(self, text="Прогресс:")
        self.progress_label.pack()

        self.progress_bar = ttk.Progressbar(self, length=300, mode="determinate")
        self.progress_bar.pack(pady=5)

        self.progress_label.pack_forget()
        self.progress_bar.pack_forget()

        self.client_socket = None

        self.bind("<Return>", self.on_enter_pressed)


    def on_enter_pressed(self, event):
        self.send_button.invoke()


    def show_progress_bar(self):
        self.progress_label.pack()
        self.progress_bar.pack()
        self.progress_bar["value"] = 0

    def hide_progress_bar(self):
        self.progress_label.pack_forget()
        self.progress_bar.pack_forget()


    def download_file(self):
        if not self.client_socket:
            messagebox.showerror("Ошибка", "Сначала подключитесь к серверу.")
            return

        selected_file = self.file_listbox.get(tk.ACTIVE)
        if not selected_file:
            messagebox.showerror("Ошибка", "Выберите файл для скачивания.")
            return

        save_path = filedialog.asksaveasfilename(initialfile=selected_file)
        if not save_path:
            return

        threading.Thread(target=self.download_file_thread, args=(selected_file, save_path), daemon=True).start()

    def download_file_thread(self, filename, save_path):
        try:
            self.show_progress_bar()
            self.client_socket.send(f"DOWNLOAD {filename.split()[0]}\r\n".encode())
            #file_size = int(self.client_socket.recv(1024).decode().strip())

            received_size = 0
            self.progress_bar["maximum"] = file_size

            with open(save_path, "wb") as file:
                while received_size < file_size:
                    chunk = self.client_socket.recv(1024)
                    if not chunk:
                        break
                    file.write(chunk)
                    print(chunk)
                    received_size += len(chunk)
                    self.progress_bar["value"] = received_size
                    self.update_idletasks()

            messagebox.showinfo("Успех", f"Файл '{filename}' успешно скачан!")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при скачивании файла: {e}")
        finally:
            self.hide_progress_bar()


    def load_icon(self):
        try:
            return self.resize_icon(".\\res\\icon\\connectionButton.png", 24, 24)
        except Exception as e:
            print(f"Ошибка при загрузке иконки: {e}")
            return None

    def resize_icon(self, path, width, height):
        try:
            image = Image.open(path) 
            image = image.resize((width, height), Image.Resampling.LANCZOS) 
            return ImageTk.PhotoImage(image) 
        except Exception as e:
            print(f"Ошибка при изменении размера иконки: {e}")
            return None

    def open_connection_window(self):
        ConnectionWindow(self)

    def connect_to_server(self, ip, port):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.settimeout(5)  
            self.client_socket.connect((ip, port))
            self.update_chat("Подключение установлено!")

            # Получение списка файлов от сервера
            self.get_file_list() 

        except socket.timeout:
            messagebox.showerror("Ошибка", f"Не удалось подключиться к {ip}:{port}, попробуйте позже")
        except socket.error as e:
            messagebox.showerror("Ошибка", f"Ошибка соединения: {e}")

    def get_file_list(self):
        try:
            self.client_socket.send("DOCS_LIST\r\n".encode())  # Запрашиваем список файлов
            file_data = self.client_socket.recv(1024).decode()  # Получаем данные от сервера

            if not file_data:
                messagebox.showerror("Ошибка", "Не удалось получить список файлов.")
                return

            # Обновляем список файлов
            self.update_file_list(file_data)

        except socket.error as e:
            messagebox.showerror("Ошибка", f"Не удалось получить список файлов: {e}")

    def update_chat(self, message):
        self.chat_display.config(state="normal")
        self.chat_display.insert("end", f"{message}\n")
        self.chat_display.config(state="disabled")
        self.chat_display.yview("end")


    def format_file_size(self, size_in_bytes):
        if size_in_bytes < 1024:
            return f"{size_in_bytes} Б"
        elif size_in_bytes < 1024**2:
            return f"{size_in_bytes / 1024:.2f} КБ"
        elif size_in_bytes < 1024**3:
            return f"{size_in_bytes / 1024**2:.2f} МБ"
        else:
            return f"{size_in_bytes / 1024**3:.2f} ГБ"
        
        
    # сервер присылает строки "file1.txt 1234"
    #                         "file2.txt 3245" размер в байтах
    def update_file_list(self, file_data):
        files = file_data.split("\r\n") 
        self.file_listbox.delete(0, "end")  

        for file in files:
            if file.strip():  
                file_info = file.split()  
                if len(file_info) == 2:
                    file_name, file_size = file_info
                    print(file_info)
                    try:
                        file_size = int(file_size)  
                        formatted_size = self.format_file_size(file_size)  
                        display_text = f"{file_name} ({formatted_size})"
                        self.file_listbox.insert("end", display_text)  
                    except ValueError:
                        print(f"Ошибка преобразования размера файла: {file_size}")


    def send_message(self, event=None):
        if not self.client_socket:
            messagebox.showerror("Ошибка", "Сначала подключитесь к серверу.")
            return

        message = self.message_entry.get().strip()
        if not message:
            return

        try:
            self.client_socket.send((message + "\r\n").encode())
            print("Жду ответ")
            response = self.client_socket.recv(1024).decode()
            print("ответ пришел")
            self.update_chat(f"Вы: {message}")
            self.update_chat(f"Сервер: {response}")

            self.message_entry.delete(0, "end")

        except socket.error as e:
            messagebox.showerror("Ошибка", f"Связь с сервером потеряна: {e}")
            self.client_socket.close()
            self.client_socket = None


    def upload_file(self):
        if not self.client_socket:
            messagebox.showerror("Ошибка", "Сначала подключитесь к серверу.")
            return

        file_path = filedialog.askopenfilename()
        if not file_path:
            return

        threading.Thread(target=self.upload_file_thread, args=(file_path,), daemon=True).start()

    def upload_file_thread(self, file_path):
        try:
            self.show_progress_bar()
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)

            self.client_socket.send(f"UPLOAD {file_name} {file_size}\r\n".encode())
            time.sleep(1)
            sent_size = 0
            self.progress_bar["maximum"] = file_size

            with open(file_path, "rb") as file:
                while chunk := file.read(1024):
                    self.client_socket.send(chunk)
                    print(chunk)
                    sent_size += len(chunk)
                    self.progress_bar["value"] = sent_size
                    self.update_idletasks()

            messagebox.showinfo("Успех", f"Файл '{file_name}' успешно загружен!")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось отправить файл: {e}")
        finally:
            self.hide_progress_bar()


class ConnectionWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Подключение")
        self.geometry("300x200")
        self.resizable(False, False)

        tk.Label(self, text="IP сервера:").pack(pady=5)
        self.ip_entry = tk.Entry(self)
        self.ip_entry.pack(pady=5)
        self.ip_entry.insert(0, "192.168.54.104")

        tk.Label(self, text="Порт:").pack(pady=5)
        self.port_entry = tk.Entry(self)
        self.port_entry.pack(pady=5)
        self.port_entry.insert(0, "12345")

        self.connect_button = tk.Button(self, text="Подключиться", command=self.connect_to_server)
        self.connect_button.pack(pady=10)

        self.parent = parent

    def connect_to_server(self):
        ip = self.ip_entry.get()
        port = self.port_entry.get()
        ip_pattern = r"^(?:\d{1,3}\.){3}\d{1,3}$"
        port_pattern = r"^\d+$"
        if not re.match(ip_pattern, ip) or not re.match(port_pattern, port):
            messagebox.showerror("Ошибка", "Введите корректные IP и порт")
            return
        port = int(port)
        if not (0 < port < 65536):
            messagebox.showerror("Ошибка", "Порт должен быть в диапазоне 1-65535")
            return
        self.parent.connect_to_server(ip, port)
        self.destroy()


if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
