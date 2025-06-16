import sqlite3
import customtkinter as ctk
from tkinter import messagebox
from PIL import Image
import cv2
import face_recognition
import numpy as np

class RegistroFacial:
    def __init__(self, parent):
        self.parent = parent
        self.entry_autorizado = {}
        self.entry_fields = {}
        self.foto_cv2 = None
        self.encoding_actual = None
        self.photo_preview_autorizado = None

        self.mostrar_formulario_registro()

    def capturar_y_comparar_foto(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            messagebox.showerror("Error", "No se pudo abrir la cámara.")
            return

        messagebox.showinfo("Instrucciones", "Presiona 'Espacio' para tomar la foto, 'Esc' para cancelar.")

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            cv2.imshow("Captura de rostro", frame)
            key = cv2.waitKey(1)

            if key % 256 == 27:
                cap.release()
                cv2.destroyAllWindows()
                return
            elif key % 256 == 32:
                break

        cap.release()
        cv2.destroyAllWindows()

        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb).resize((207, 169))
        self.photo_preview_autorizado = ctk.CTkImage(img_pil, size=(207, 169))
        self.lbl_foto_autorizado.configure(image=self.photo_preview_autorizado, text="")
        self.foto_cv2 = frame

        faces = face_recognition.face_encodings(img_rgb)
        if not faces:
            messagebox.showerror("Error", "No se detectó ningún rostro.")
            return

        self.encoding_actual = faces[0]

        conn = sqlite3.connect('acceso.db')
        cursor = conn.cursor()
        cursor.execute("SELECT nombre, apellido, empresa, encoding FROM personal_autorizado WHERE encoding IS NOT NULL")
        candidatos = cursor.fetchall()
        conn.close()

        for nombre, apellido, empresa, enc_blob in candidatos:
            enc_guardado = np.frombuffer(enc_blob, dtype=np.float64)
            distancia = face_recognition.face_distance([enc_guardado], self.encoding_actual)[0]
            if distancia < 0.5:
                if messagebox.askyesno("Coincidencia encontrada", f"¿Deseas usar los datos de {nombre} {apellido} de {empresa}?"):
                    for campo, valor in {
                        "Nombre": nombre,
                        "Apellido": apellido,
                        "Empresa": empresa
                    }.items():
                        entry = self.entry_fields.get(campo)
                        if entry:
                            entry.delete(0, "end")
                            entry.insert(0, valor)
                break

    def mostrar_formulario_registro(self):
        for widget in self.parent.winfo_children():
            widget.destroy()

        title = ctk.CTkLabel(self.parent, text="Nuevo Registro", font=("Arial", 22, "bold"))
        title.pack(anchor="nw", padx=30, pady=(20, 10))

        form_frame = ctk.CTkFrame(self.parent, fg_color="white")
        form_frame.pack(pady=10)

        campos_izquierda = ["Nombre", "Empresa", "Motivo"]
        campos_derecha = ["Apellido", "Área", "Entrada"]

        for i, campo in enumerate(campos_izquierda):
            lbl = ctk.CTkLabel(form_frame, text=campo, font=("Arial", 14), anchor="w")
            lbl.grid(row=i, column=0, sticky="w", padx=10, pady=5)
            entry = ctk.CTkEntry(form_frame, width=300)
            entry.grid(row=i, column=1, padx=10, pady=5)
            self.entry_fields[campo] = entry

        for i, campo in enumerate(campos_derecha):
            lbl = ctk.CTkLabel(form_frame, text=campo, font=("Arial", 14), anchor="w")
            lbl.grid(row=i, column=2, sticky="w", padx=10, pady=5)
            entry = ctk.CTkEntry(form_frame, width=300)
            if campo == "Entrada":
                from datetime import datetime
                entry.insert(0, datetime.now().strftime("%I:%M %p"))
                entry.configure(state="disabled")
            entry.grid(row=i, column=3, padx=10, pady=5)
            self.entry_fields[campo] = entry

        self.lbl_foto_autorizado = ctk.CTkLabel(
            self.parent,
            text="Haz clic para tomar foto",
            font=("Arial", 12),
            width=207,
            height=169,
            fg_color="#dddddd",
            corner_radius=10
        )
        self.lbl_foto_autorizado.pack(pady=(10, 5))
        self.lbl_foto_autorizado.bind("<Button-1>", lambda e: self.capturar_y_comparar_foto())

        btn_guardar = ctk.CTkButton(
            self.parent, text="Guardar", fg_color="#4CAF50", hover_color="#45a049",
            text_color="white", width=140, corner_radius=10,
            command=self.guardar_registro
        )
        btn_guardar.pack(pady=20)

    def guardar_registro(self):
        datos = [self.entry_fields[campo].get() for campo in ["Nombre", "Apellido", "Empresa", "Motivo", "Área", "Entrada"]]

        if any(dato.strip() == "" for dato in datos):
            messagebox.showwarning("Campos vacíos", "Por favor completa todos los campos.")
            return

        if not hasattr(self, "foto_cv2") or not hasattr(self, "encoding_actual"):
            messagebox.showwarning("Faltan datos", "Toma una foto antes de guardar.")
            return

        conn = sqlite3.connect('acceso.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS registros (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                apellido TEXT NOT NULL,
                empresa TEXT NOT NULL,
                motivo TEXT NOT NULL,
                area TEXT NOT NULL,
                hora_entrada TEXT,
                hora_salida TEXT
            )
        ''')

        cursor.execute('''
            INSERT INTO registros (nombre, apellido, empresa, motivo, area, hora_entrada, hora_salida)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (*datos, ""))

        conn.commit()
        conn.close()

        messagebox.showinfo("Éxito", "Registro guardado exitosamente.")