import sqlite3
import customtkinter as ctk
from PIL import Image
from datetime import datetime
from tkinter import messagebox
from tkinter import filedialog
import face_recognition
import numpy as np
import cv2
import io

class MenuPrincipal(ctk.CTk):
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

            if key % 256 == 27:  # Esc
                cap.release()
                cv2.destroyAllWindows()
                return
            elif key % 256 == 32:  # Space
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
        encontrados = cursor.fetchall()
        conn.close()

        for nombre, apellido, empresa, blob in encontrados:
            encoding_guardado = np.frombuffer(blob, dtype=np.float64)
            distancia = face_recognition.face_distance([encoding_guardado], self.encoding_actual)[0]
            if distancia < 0.5:
                respuesta = messagebox.askyesno("Coincidencia encontrada",
                                                f"¿Deseas usar los datos de {nombre} {apellido} de {empresa}?")
                if respuesta:
                    # Detectar qué conjunto de campos está activo
                    entries = getattr(self, "entry_fields", None)
                    if entries is None:
                        entries = getattr(self, "entry_autorizado", {})

                    for campo, valor in {
                        "Nombre": nombre,
                        "Apellido": apellido,
                        "Empresa": empresa
                    }.items():
                        if campo in entries:
                            entries[campo].delete(0, "end")
                            entries[campo].insert(0, valor)
                break

    def __init__(self):
        super().__init__()
        self.title("Menú")
        self.geometry("1300x700")  # Ventana más ancha
        self.resizable(False, False)
        self.configure(fg_color="white")

        self.sidebar_visible = True

        # Íconos
        self.hamburger_icon = ctk.CTkImage(Image.open("menu_icon.png"), size=(25, 25))
        self.user_icon = ctk.CTkImage(Image.open("user_icon_lavanda_rounded.png"), size=(100, 100))

        # Layout principal
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=250, fg_color="#d9d9d9", corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="ns")

        # Contenido
        self.content = ctk.CTkFrame(self, fg_color="white")
        self.content.grid(row=0, column=1, sticky="nsew")

        # Botón toggle
        self.btn_toggle_sidebar = ctk.CTkButton(
            self.sidebar, image=self.hamburger_icon, text="", width=30, height=30,
            fg_color="transparent", hover_color="#d0d0d0", command=self.toggle_sidebar
        )
        self.btn_toggle_sidebar.pack(anchor="ne", pady=10, padx=10)

        avatar_label = ctk.CTkLabel(self.sidebar, image=self.user_icon, text="", fg_color="transparent")
        avatar_label.pack(pady=(10, 5))

        user_label = ctk.CTkLabel(self.sidebar, text="Usuario", font=("Arial", 16, "bold"), text_color="black")
        user_label.pack(pady=(0, 20))

        # Botones menú

        self.btn_usuarios = ctk.CTkButton(
            self.sidebar, text="Usuarios", fg_color="white", text_color="black",
            hover_color="#e6e6e6", command=self.mostrar_gestion_usuarios
        )
        self.btn_usuarios.pack(pady=5, fill="x", padx=15)




        # Botón hamburguesa flotante
        self.btn_floating = ctk.CTkButton(
            self, image=self.hamburger_icon, text="", width=30, height=30,
            fg_color="transparent", hover_color="#eeeeee", command=self.toggle_sidebar
        )
        self.btn_floating.place(x=10, y=10)
        self.btn_floating.lower()

        self.btn_lista = ctk.CTkButton(self.sidebar, text="Lista de registro", fg_color="white", text_color="black",
                                       hover_color="#e6e6e6", command=self.mostrar_lista_registro)
        self.btn_lista.pack(pady=5, fill="x", padx=15)

        self.btn_bd = ctk.CTkButton(self.sidebar, text="Base de Datos", fg_color="white", text_color="black",
                                    hover_color="#e6e6e6", command=self.mostrar_base_datos)
        self.btn_bd.pack(pady=5, fill="x", padx=15)

        # Simulador de registros
        self.registros = []


    def toggle_sidebar(self):
        if self.sidebar_visible:
            self.sidebar.grid_remove()
            self.btn_floating.lift()
            self.sidebar_visible = False
        else:
            self.sidebar.grid(row=0, column=0, sticky="ns")
            self.btn_floating.lower()
            self.sidebar_visible = True

    def eliminar_fila(self, row):
        # Eliminar la fila seleccionada
        del self.registros[row]
        messagebox.showinfo("Eliminado", "El registro ha sido eliminado.")
        self.mostrar_lista_registro()

    def mostrar_gestion_usuarios(self):
        for widget in self.content.winfo_children():
            widget.destroy()

        title = ctk.CTkLabel(self.content, text="Gestión de Usuarios", font=("Arial", 22, "bold"))
        title.pack(anchor="nw", padx=30, pady=(20, 10))

        # Formulario para agregar nuevo usuario
        form_frame = ctk.CTkFrame(self.content, fg_color="white")
        form_frame.pack(pady=10)

        lbl_user = ctk.CTkLabel(form_frame, text="Usuario:", font=("Arial", 14))
        lbl_user.grid(row=0, column=0, padx=10, pady=5)
        entry_user = ctk.CTkEntry(form_frame, width=200)
        entry_user.grid(row=0, column=1, padx=10, pady=5)

        lbl_pass = ctk.CTkLabel(form_frame, text="Contraseña:", font=("Arial", 14))
        lbl_pass.grid(row=1, column=0, padx=10, pady=5)
        entry_pass = ctk.CTkEntry(form_frame, width=200)
        entry_pass.grid(row=1, column=1, padx=10, pady=5)

        def agregar_usuario():
            usuario = entry_user.get()
            contrasena = entry_pass.get()

            if usuario.strip() == "" or contrasena.strip() == "":
                messagebox.showwarning("Error", "Debes completar todos los campos.")
                return

            conn = sqlite3.connect('acceso.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO usuarios (usuario, contrasena) VALUES (?, ?)", (usuario, contrasena))
            conn.commit()
            conn.close()

            messagebox.showinfo("Usuario agregado", f"El usuario '{usuario}' fue agregado exitosamente.")
            self.mostrar_gestion_usuarios()

        btn_agregar = ctk.CTkButton(form_frame, text="Agregar Usuario", fg_color="#6A0DAD", text_color="white",
                                    hover_color="#5A0CA0", corner_radius=8, command=agregar_usuario)
        btn_agregar.grid(row=2, columnspan=2, pady=10)

        # Tabla de usuarios existentes
        tabla = ctk.CTkScrollableFrame(self.content, height=400, fg_color="#f5f5f5", corner_radius=10)
        tabla.pack(fill="both", expand=True, padx=30, pady=10)

        encabezados = ["Usuario", "Eliminar"]
        for i, texto in enumerate(encabezados):
            etiqueta = ctk.CTkLabel(tabla, text=texto, font=("Arial", 13, "bold"), text_color="black",
                                    fg_color="#cde4f9", width=150 if i == 0 else 50, anchor="center")
            etiqueta.grid(row=0, column=i, padx=1, pady=1)

        conn = sqlite3.connect('acceso.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, usuario FROM usuarios")
        usuarios = cursor.fetchall()
        conn.close()

        for r, (id_usuario, usuario) in enumerate(usuarios, start=1):
            label_user = ctk.CTkLabel(tabla, text=usuario, font=("Arial", 12), text_color="black",
                                      width=150, fg_color="#eeeeee")
            label_user.grid(row=r, column=0, padx=1, pady=1)

            def eliminar_usuario(id_usuario=id_usuario):
                confirm = messagebox.askyesno("Confirmar", "¿Seguro que quieres eliminar este usuario?")
                if confirm:
                    conn = sqlite3.connect('acceso.db')
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM usuarios WHERE id=?", (id_usuario,))
                    conn.commit()
                    conn.close()
                    messagebox.showinfo("Eliminado", "Usuario eliminado exitosamente.")
                    self.mostrar_gestion_usuarios()

            btn_eliminar = ctk.CTkButton(tabla, text="❌", width=40, height=30, font=("Arial", 14),
                                         fg_color="#ff4d4d", hover_color="#ff1a1a", text_color="white",
                                         corner_radius=5, command=eliminar_usuario)
            btn_eliminar.grid(row=r, column=1, padx=1, pady=1)

    def mostrar_formulario_registro(self):
        for widget in self.content.winfo_children():
            widget.destroy()

        # Título
        title = ctk.CTkLabel(self.content, text="Nuevo Registro", font=("Arial", 24, "bold"))
        title.pack(anchor="nw", padx=30, pady=(20, 10))

        # Botón Regresar
        btn_regresar = ctk.CTkButton(
            self.content, text="Regresar", fg_color="#6A0DAD", text_color="white",
            hover_color="#5A0CA0", corner_radius=8, width=140,
            command=self.mostrar_lista_registro
        )
        btn_regresar.place(relx=1.0, x=-30, y=30, anchor="ne")

        # Frame con dos columnas
        form_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        form_frame.pack(padx=40, pady=20)

        campos_izquierda = ["Nombre", "Empresa", "Motivo"]
        campos_derecha = ["Apellido", "Área", "Entrada"]
        self.entry_fields = {}

        for i, campo in enumerate(campos_izquierda):
            lbl = ctk.CTkLabel(form_frame, text=campo, font=("Arial", 14), anchor="w")
            lbl.grid(row=i, column=0, sticky="w", padx=10, pady=10)
            entry = ctk.CTkEntry(form_frame, width=300, height=40, corner_radius=10)
            entry.grid(row=i, column=1, padx=10, pady=10)
            self.entry_fields[campo] = entry

        for i, campo in enumerate(campos_derecha):
            lbl = ctk.CTkLabel(form_frame, text=campo, font=("Arial", 14), anchor="w")
            lbl.grid(row=i, column=2, sticky="w", padx=10, pady=10)
            if campo == "Entrada":
                # Mostrar la hora actual automáticamente
                hora_actual = datetime.now().strftime("%I:%M %p")
                entry = ctk.CTkEntry(form_frame, width=300, height=40, corner_radius=10)
                entry.insert(0, hora_actual)
                entry.configure(state="disabled")  # Deshabilitar edición
            else:
                entry = ctk.CTkEntry(form_frame, width=300, height=40, corner_radius=10)
            entry.grid(row=i, column=3, padx=10, pady=10)
            self.entry_fields[campo] = entry

        # Opción para cargar foto
        self.lbl_foto_autorizado = ctk.CTkLabel(
            self.content, text="Haz clic para tomar foto",
            font=("Arial", 12), width=207, height=169, fg_color="#dddddd", corner_radius=10
        )
        self.lbl_foto_autorizado.pack(pady=(10, 5))
        self.lbl_foto_autorizado.bind("<Button-1>", lambda e: self.capturar_y_comparar_foto())
        def cargar_foto():
            self.photo_path = filedialog.askopenfilename(
                title="Seleccionar Foto",
                filetypes=[("Archivos de Imagen", "*.png;*.jpg;*.jpeg")]
            )
            if self.photo_path:
                # Cargar y redimensionar la imagen
                img = Image.open(self.photo_path)
                img = img.resize((200, 200))  # Tamaño mediano para la vista previa
                self.photo_preview = ctk.CTkImage(img)
                lbl_foto.configure(image=self.photo_preview, text="")  # Mostrar la imagen

        lbl_foto = ctk.CTkLabel(self.content, text="No se ha cargado ninguna foto", font=("Arial", 12))
        lbl_foto.pack(pady=(10, 5))


        # Botón Realizar Registro
        btn_guardar = ctk.CTkButton(
            self.content,
            text="Realizar Registro",
            fg_color="#6A0DAD",
            hover_color="#5A0CA0",
            text_color="white",
            width=180,
            height=45,
            font=("Arial", 14, "bold"),
            corner_radius=10,
            command=self.guardar_registro
        )
        btn_guardar.pack(anchor="w", padx=70, pady=30)

    def guardar_registro(self):
        datos = [entry.get() for entry in self.entry_fields.values()]

        if any(dato.strip() == "" for dato in datos if dato != "Entrada"):
            messagebox.showwarning("Campos vacíos", "Por favor, llena todos los campos.")
            return

        if not hasattr(self, "foto_cv2") or not hasattr(self, "encoding_actual"):
            messagebox.showwarning("Faltan datos", "Toma una foto antes de guardar.")
            return

        conn = sqlite3.connect('acceso.db')
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS registros (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT,
                apellido TEXT,
                empresa TEXT,
                motivo TEXT,
                area TEXT,
                hora_entrada TEXT,
                hora_salida TEXT
            )
        """)

        cursor.execute("""
            INSERT INTO registros (nombre, apellido, empresa, motivo, area, hora_entrada, hora_salida)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            datos[0],  # Nombre
            datos[3],  # Apellido
            datos[1],  # Empresa
            datos[2],  # Motivo
            datos[4],  # Área
            datos[5],  # Entrada
            ""  # Salida (vacío al principio)
        ))

        conn.commit()
        conn.close()

        messagebox.showinfo("Éxito", "Registro guardado correctamente.")
        self.mostrar_lista_registro()

    def ver_foto_grande(self, ruta_imagen):
        ventana_foto = ctk.CTkToplevel(self)
        ventana_foto.title("Foto en grande")
        ventana_foto.geometry("600x600")  # Aumenté el tamaño de la ventana

        # Cargar imagen
        img = Image.open(ruta_imagen)

        # Ajustar tamaño para que llene la ventana, pero manteniendo proporciones
        img.thumbnail((550, 550))  # Cambia el tamaño pero respeta la proporción
        img_ctk = ctk.CTkImage(img, size=img.size)

        lbl_img = ctk.CTkLabel(ventana_foto, image=img_ctk, text="")
        lbl_img.image = img_ctk
        lbl_img.pack(expand=True, fill="both", padx=10, pady=10)

    def mostrar_base_datos(self):
        for widget in self.content.winfo_children():
            widget.destroy()

        title = ctk.CTkLabel(self.content, text="Base de datos (Personal autorizado)", font=("Arial", 22, "bold"))
        title.pack(anchor="nw", padx=30, pady=(20, 10))

        btn_nuevo = ctk.CTkButton(
            self.content, text="Nuevo autorizado", fg_color="#6A0DAD", text_color="white",
            hover_color="#5A0CA0", corner_radius=8, width=140,
            command=self.mostrar_formulario_autorizado
        )

        btn_nuevo.pack(anchor="ne", padx=30)

        tabla = ctk.CTkScrollableFrame(self.content, height=450, fg_color="#f5f5f5", corner_radius=10)
        tabla.pack(fill="both", expand=True, padx=30, pady=10)

        columnas = ["Foto", "Nombre", "Apellido", "Empresa", "Actividad empresarial", "🗑️"]

        for i, texto in enumerate(columnas):
            etiqueta = ctk.CTkLabel(tabla, text=texto, font=("Arial", 13, "bold"), text_color="black",
                                    fg_color="#cde4f9", width=120, anchor="center")
            etiqueta.grid(row=0, column=i, padx=1, pady=1)

        conn = sqlite3.connect('acceso.db')
        cursor = conn.cursor()
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS personal_autorizado (id IzNTEGER PRIMARY KEY, nombre TEXT, apellido TEXT, empresa TEXT, actividad TEXT, foto TEXT)"
        )
        cursor.execute("SELECT id, nombre, apellido, empresa, actividad, foto FROM personal_autorizado")
        autorizados = cursor.fetchall()
        conn.close()

        for r, fila in enumerate(autorizados, start=1):
            foto_blob = fila[5]  # Campo 'foto' como BLOB
            if foto_blob:
                try:
                    imagen = Image.open(io.BytesIO(foto_blob))
                    imagen.thumbnail((80, 80))  # Miniatura
                    imagen_ctk = ctk.CTkImage(imagen)

                    lbl_imagen = ctk.CTkLabel(tabla, image=imagen_ctk, text="", cursor="hand2")
                    lbl_imagen.image = imagen_ctk
                    lbl_imagen.grid(row=r, column=0, padx=1, pady=1)

                    def mostrar_grande(blob=foto_blob):
                        img_grande = Image.open(io.BytesIO(blob))
                        img_grande.thumbnail((500, 500))  # Ajustar tamaño grande
                        img_ctk = ctk.CTkImage(img_grande, size=img_grande.size)

                        ventana = ctk.CTkToplevel(self)
                        ventana.title("Foto en grande")
                        ventana.transient(self)  # Se coloca delante de la ventana principal
                        ventana.grab_set()  # Modal: bloquea la ventana principal hasta cerrar esta
                        ventana.focus_set()  # Pone foco en la ventana emergente

                        lbl = ctk.CTkLabel(ventana, image=img_ctk, text="")
                        lbl.image = img_ctk
                        lbl.pack(padx=20, pady=20)

                    lbl_imagen.bind("<Button-1>", lambda e, b=foto_blob: mostrar_grande(b))

                except Exception as e:
                    lbl_imagen = ctk.CTkLabel(tabla, text="Error Img", fg_color="#eeeeee")
                    lbl_imagen.grid(row=r, column=0, padx=1, pady=1)
            else:
                lbl_imagen = ctk.CTkLabel(tabla, text="Sin foto", fg_color="#eeeeee")
                lbl_imagen.grid(row=r, column=0, padx=1, pady=1)

            # Resto de columnas
            for c in range(1, len(columnas) - 1):
                valor = fila[c]
                cell = ctk.CTkLabel(tabla, text=valor, font=("Arial", 12), text_color="black",
                                    width=120, fg_color="#eeeeee")
                cell.grid(row=r, column=c, padx=1, pady=1)

            # Botón eliminar
            def eliminar_persona(id_persona=fila[0]):
                if messagebox.askyesno("Confirmar", "¿Eliminar este autorizado?"):
                    conn = sqlite3.connect('acceso.db')
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM personal_autorizado WHERE id=?", (id_persona,))
                    conn.commit()
                    conn.close()
                    messagebox.showinfo("Eliminado", "Personal eliminado exitosamente.")
                    self.mostrar_base_datos()

            btn_eliminar = ctk.CTkButton(tabla, text="❌", width=40, height=30, font=("Arial", 14),
                                         fg_color="#ff4d4d", hover_color="#ff1a1a",
                                         text_color="white", corner_radius=5,
                                         command=eliminar_persona)
            btn_eliminar.grid(row=r, column=len(columnas) - 1, padx=1, pady=1)

    def mostrar_formulario_autorizado(self):
        for widget in self.content.winfo_children():
            widget.destroy()

        title = ctk.CTkLabel(self.content, text="Nuevo Personal Autorizado", font=("Arial", 22, "bold"))
        title.pack(anchor="nw", padx=30, pady=(20, 10))

        form_frame = ctk.CTkFrame(self.content, fg_color="white")
        form_frame.pack(pady=10)

        campos = ["Nombre", "Apellido", "Empresa", "Actividad empresarial"]
        self.entry_autorizado = {}

        for i, campo in enumerate(campos):
            lbl = ctk.CTkLabel(form_frame, text=campo, font=("Arial", 14), anchor="w", width=200)
            lbl.grid(row=i, column=0, sticky="w", padx=10, pady=5)
            entry = ctk.CTkEntry(form_frame, width=300)
            entry.grid(row=i, column=1, padx=10, pady=5)
            self.entry_autorizado[campo] = entry

        # Foto desde cámara
        self.lbl_foto_autorizado = ctk.CTkLabel(
            self.content,
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
            self.content, text="Guardar", fg_color="#4CAF50", hover_color="#45a049",
            text_color="white", width=140, corner_radius=10,
            command=self.guardar_autorizado
        )
        btn_guardar.pack(pady=20)

    def guardar_autorizado(self):
        datos = [entry.get() for entry in self.entry_autorizado.values()]

        if any(dato.strip() == "" for dato in datos):
            messagebox.showwarning("Campos vacíos", "Por favor completa todos los campos.")
            return

        if not hasattr(self, "foto_cv2") or not hasattr(self, "encoding_actual"):
            messagebox.showwarning("Foto faltante", "Por favor, toma una foto antes de guardar.")
            return

        if not hasattr(self, "foto_cv2") or not hasattr(self, "encoding_actual"):
            messagebox.showwarning("Faltan datos", "Toma una foto antes de guardar.")
            return

        # Convertir a BLOB
        _, buffer = cv2.imencode('.jpg', self.foto_cv2)
        foto_blob = buffer.tobytes()
        encoding_blob = self.encoding_actual.tobytes()

        conn = sqlite3.connect('acceso.db')
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS personal_autorizado (
                id INTEGER PRIMARY KEY,
                nombre TEXT,
                apellido TEXT,
                empresa TEXT,
                actividad TEXT,
                foto BLOB,
                encoding BLOB
        )
        """)

        cursor.execute("""
            INSERT INTO personal_autorizado (nombre, apellido, empresa, actividad, foto, encoding)
            VALUES (?, ?, ?, ?, ?, ?)
        """, datos + [foto_blob, encoding_blob])

        conn.commit()
        conn.close()

        messagebox.showinfo("Éxito", "Nuevo personal autorizado guardado.")
        self.mostrar_base_datos()

    def mostrar_lista_registro(self):
        for widget in self.content.winfo_children():
            widget.destroy()

        title = ctk.CTkLabel(self.content, text="Lista de Registro", font=("Arial", 22, "bold"))
        title.pack(anchor="nw", padx=30, pady=(20, 10))

        # ---------------- NUEVO: BOTÓN PARA NUEVO REGISTRO ----------------
        btn_nuevo_registro = ctk.CTkButton(
            self.content, text="Nuevo Registro", fg_color="#6A0DAD", text_color="white",
            hover_color="#5A0CA0", corner_radius=8, width=140,
            command=self.mostrar_formulario_registro
        )

        btn_nuevo_registro.pack(anchor="ne", padx=30, pady=(0, 20))
        # ------------------------------------------------------------------

        tabla = ctk.CTkScrollableFrame(self.content, height=450, fg_color="#f5f5f5", corner_radius=10)
        tabla.pack(fill="both", expand=True, padx=30, pady=10)

        columnas = ["Nombre", "Apellido", "Empresa", "Motivo", "Área", "Entrada", "Salida", "🗑️"]

        for i, texto in enumerate(columnas):
            etiqueta = ctk.CTkLabel(tabla, text=texto, font=("Arial", 13, "bold"), text_color="black",
                                    fg_color="#cde4f9", width=100, anchor="center")
            etiqueta.grid(row=0, column=i, padx=1, pady=1)

        conn = sqlite3.connect('acceso.db')
        cursor = conn.cursor()
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS registros (id INTEGER PRIMARY KEY, nombre TEXT, apellido TEXT, empresa TEXT, motivo TEXT, area TEXT, hora_entrada TEXT, hora_salida TEXT)")
        cursor.execute("SELECT * FROM registros")
        registros = cursor.fetchall()
        conn.close()

        for r, fila in enumerate(registros, start=1):
            for c in range(len(columnas)):
                if c < 6:
                    # Mostrar Nombre, Apellido, Empresa, Motivo, Área, Entrada
                    valor = fila[c + 1]
                    cell = ctk.CTkLabel(tabla, text=valor, font=("Arial", 12), text_color="black",
                                        width=100, fg_color="#eeeeee")
                    cell.grid(row=r, column=c, padx=1, pady=1)

                elif c == 6:
                    # Columna de Salida → Botón o mostrar hora
                    hora_salida = fila[7]

                    if hora_salida == "" or hora_salida is None:
                        # Botón para registrar salida
                        def registrar_salida(id_registro=fila[0]):
                            hora_actual = datetime.now().strftime("%I:%M %p")
                            conn = sqlite3.connect('acceso.db')
                            cursor = conn.cursor()
                            cursor.execute("UPDATE registros SET hora_salida = ? WHERE id = ?",
                                           (hora_actual, id_registro))
                            conn.commit()
                            conn.close()
                            messagebox.showinfo("Salida registrada", "La hora de salida ha sido registrada.")
                            self.mostrar_lista_registro()

                        btn_salida = ctk.CTkButton(tabla, text="Registrar salida", fg_color="#4CAF50",
                                                   text_color="white", hover_color="#45a049",
                                                   width=120, height=30, corner_radius=5,
                                                   command=registrar_salida)
                        btn_salida.grid(row=r, column=c, padx=1, pady=1)
                    else:
                        # Mostrar hora de salida en color verde
                        lbl_salida = ctk.CTkLabel(tabla, text=f"{hora_salida}", font=("Arial", 12, "bold"),
                                                  text_color="#4CAF50", width=100, fg_color="#eeeeee")
                        lbl_salida.grid(row=r, column=c, padx=1, pady=1)

                elif c == 7:
                    # Última columna → Botón eliminar registro
                    def eliminar_registro(id_registro=fila[0]):
                        if messagebox.askyesno("Confirmar", "¿Eliminar este registro?"):
                            conn = sqlite3.connect('acceso.db')
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM registros WHERE id=?", (id_registro,))
                            conn.commit()
                            conn.close()
                            messagebox.showinfo("Eliminado", "Registro eliminado.")
                            self.mostrar_lista_registro()

                    btn_eliminar = ctk.CTkButton(tabla, text="❌", width=40, height=30, font=("Arial", 14),
                                                 fg_color="#ff4d4d", hover_color="#ff1a1a",
                                                 text_color="white", corner_radius=5,
                                                 command=eliminar_registro)
                    btn_eliminar.grid(row=r, column=c, padx=1, pady=1)


def validar_usuario(usuario, contrasena):
    conn = sqlite3.connect('acceso.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM usuarios WHERE usuario=? AND contrasena=?", (usuario, contrasena))
    resultado = cursor.fetchone()

    conn.close()

    return resultado is not None




def mostrar_login():
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")

    login = ctk.CTk(fg_color="white")
    login.title("Login")
    login.geometry("1300x700")
    login.resizable(False, False)

    frame = ctk.CTkFrame(login, fg_color="white", corner_radius=20)
    frame.place(relx=0.5, rely=0.5, anchor="center")

    user_icon = ctk.CTkImage(Image.open("user_icon_lavanda_rounded.png"), size=(120, 120))
    icon_label = ctk.CTkLabel(frame, image=user_icon, text="", fg_color="transparent")
    icon_label.pack(pady=(40, 20))

    entry_user = ctk.CTkEntry(frame, placeholder_text="Usuario", width=300, height=40, corner_radius=10)
    entry_user.pack(pady=10)

    entry_pass = ctk.CTkEntry(frame, placeholder_text="Contraseña", show="*", width=300, height=40, corner_radius=10)
    entry_pass.pack(pady=10)

    def iniciar_sesion():
        usuario = entry_user.get()
        contrasena = entry_pass.get()

        if validar_usuario(usuario, contrasena):
            login.destroy()
            menu = MenuPrincipal()
            menu.mainloop()
        else:
            messagebox.showerror("Error", "Usuario o contraseña incorrectos.")

    btn_login = ctk.CTkButton(
        frame, text="Ingresar", fg_color="#6A0DAD", hover_color="#5A0CA0",
        text_color="white", width=140, height=40, corner_radius=20, command=iniciar_sesion
    )
    btn_login.pack(pady=(20, 40))

    login.mainloop()

# Iniciar aplicación
if __name__ == "__main__":
    mostrar_login()