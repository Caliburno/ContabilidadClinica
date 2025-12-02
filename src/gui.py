import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
from typing import Optional

import database as db
from models import (
    Paciente, Sesion, Pago, Informe,
    TipoPaciente, TipoSesion, EstadoSesion, ConceptoPago,
    TipoInforme, EstadoInforme, EstadoPagoInforme
)


class AplicacionClinica:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestión Clínica - Contabilidad")
        self.root.geometry("1200x700")
        
        # Paciente actualmente seleccionado
        self.paciente_actual: Optional[Paciente] = None
        
        # Inicializar base de datos
        db.inicializar_base_datos()
        
        # Crear interfaz
        self.crear_interfaz()
        
        # Cargar lista de pacientes
        self.cargar_lista_pacientes()
    
    def crear_interfaz(self):
        """Crea la estructura principal de la interfaz"""
        
        # ===== BARRA SUPERIOR =====
        frame_superior = tk.Frame(self.root, bg="#2c3e50", height=60)
        frame_superior.pack(side=tk.TOP, fill=tk.X)
        frame_superior.pack_propagate(False)
        
        tk.Label(
            frame_superior, 
            text="Gestión de Clínica Psicológica",
            bg="#2c3e50",
            fg="white",
            font=("Arial", 16, "bold")
        ).pack(side=tk.LEFT, padx=20, pady=15)
        
        btn_nuevo_paciente = tk.Button(
            frame_superior,
            text="➕ Nuevo Paciente",
            command=self.abrir_dialogo_nuevo_paciente,
            bg="#27ae60",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=15,
            pady=5,
            relief=tk.FLAT,
            cursor="hand2"
        )
        btn_nuevo_paciente.pack(side=tk.RIGHT, padx=10, pady=10)
        
        btn_reporte = tk.Button(
            frame_superior,
            text="📊 Reporte Mensual",
            command=self.mostrar_reporte_mensual,
            bg="#3498db",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=15,
            pady=5,
            relief=tk.FLAT,
            cursor="hand2"
        )
        btn_reporte.pack(side=tk.RIGHT, padx=10, pady=10)
        
        # ===== CONTENEDOR PRINCIPAL =====
        contenedor_principal = tk.Frame(self.root)
        contenedor_principal.pack(fill=tk.BOTH, expand=True)
        
        # ===== PANEL IZQUIERDO: LISTA DE PACIENTES =====
        frame_izquierdo = tk.Frame(contenedor_principal, bg="#ecf0f1", width=300)
        frame_izquierdo.pack(side=tk.LEFT, fill=tk.BOTH)
        frame_izquierdo.pack_propagate(False)
        
        tk.Label(
            frame_izquierdo,
            text="Pacientes",
            bg="#34495e",
            fg="white",
            font=("Arial", 12, "bold"),
            pady=10
        ).pack(fill=tk.X)
        
        # Barra de búsqueda
        frame_busqueda = tk.Frame(frame_izquierdo, bg="#ecf0f1")
        frame_busqueda.pack(fill=tk.X, padx=10, pady=10)
        
        self.entry_busqueda = tk.Entry(frame_busqueda, font=("Arial", 10))
        self.entry_busqueda.pack(fill=tk.X)
        self.entry_busqueda.insert(0, "🔍 Buscar paciente...")
        self.entry_busqueda.bind("<FocusIn>", self.limpiar_placeholder_busqueda)
        self.entry_busqueda.bind("<KeyRelease>", self.filtrar_pacientes)
        
        # Listbox de pacientes
        frame_lista = tk.Frame(frame_izquierdo)
        frame_lista.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        scrollbar = tk.Scrollbar(frame_lista)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.listbox_pacientes = tk.Listbox(
            frame_lista,
            font=("Arial", 10),
            yscrollcommand=scrollbar.set,
            selectmode=tk.SINGLE
        )
        self.listbox_pacientes.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.listbox_pacientes.yview)
        
        self.listbox_pacientes.bind("<<ListboxSelect>>", self.seleccionar_paciente)
        
        # ===== PANEL DERECHO: DETALLES DEL PACIENTE =====
        self.frame_derecho = tk.Frame(contenedor_principal, bg="white")
        self.frame_derecho.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Mensaje inicial (cuando no hay paciente seleccionado)
        self.label_sin_seleccion = tk.Label(
            self.frame_derecho,
            text="← Selecciona un paciente de la lista",
            font=("Arial", 14),
            fg="#95a5a6"
        )
        self.label_sin_seleccion.pack(expand=True)
        
        # Notebook (pestañas) - inicialmente oculto
        self.notebook = ttk.Notebook(self.frame_derecho)
        
        # Crear las pestañas (vacías por ahora)
        self.tab_datos = tk.Frame(self.notebook, bg="white")
        self.tab_sesiones = tk.Frame(self.notebook, bg="white")
        self.tab_pagos = tk.Frame(self.notebook, bg="white")
        self.tab_informes = tk.Frame(self.notebook, bg="white")
        self.tab_resumen = tk.Frame(self.notebook, bg="white")
        
        self.notebook.add(self.tab_datos, text="📋 Datos del Paciente")
        self.notebook.add(self.tab_sesiones, text="🗓️ Sesiones")
        self.notebook.add(self.tab_pagos, text="💰 Pagos")
        self.notebook.add(self.tab_informes, text="📄 Informes")
        self.notebook.add(self.tab_resumen, text="📊 Resumen")
    
    # ===== FUNCIONES DE LA LISTA DE PACIENTES =====
    
    def cargar_lista_pacientes(self, filtro: str = ""):
        """Carga la lista de pacientes en el Listbox"""
        self.listbox_pacientes.delete(0, tk.END)
        
        pacientes = db.obtener_todos_pacientes()
        
        # Filtrar si hay texto de búsqueda
        if filtro:
            pacientes = [p for p in pacientes if filtro.lower() in p.nombre.lower()]
        
        # Guardar referencia para acceder después
        self.pacientes_lista = pacientes
        
        for paciente in pacientes:
            # Formato: "Nombre (Tipo) - $deuda"
            deuda_str = f"${paciente.deuda:,.0f}" if paciente.deuda >= 0 else f"-${abs(paciente.deuda):,.0f}"
            texto = f"{paciente.nombre} ({paciente.tipo.value[:3]}) - {deuda_str}"
            self.listbox_pacientes.insert(tk.END, texto)
    
    def limpiar_placeholder_busqueda(self, event):
        """Limpia el placeholder del campo de búsqueda"""
        if self.entry_busqueda.get() == "🔍 Buscar paciente...":
            self.entry_busqueda.delete(0, tk.END)
    
    def filtrar_pacientes(self, event):
        """Filtra la lista de pacientes según el texto de búsqueda"""
        filtro = self.entry_busqueda.get()
        if filtro != "🔍 Buscar paciente...":
            self.cargar_lista_pacientes(filtro)
    
    def seleccionar_paciente(self, event):
        """Se ejecuta cuando se selecciona un paciente de la lista"""
        seleccion = self.listbox_pacientes.curselection()
        if not seleccion:
            return
        
        indice = seleccion[0]
        self.paciente_actual = self.pacientes_lista[indice]
        
        # Ocultar mensaje inicial y mostrar notebook
        self.label_sin_seleccion.pack_forget()
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Actualizar contenido de las pestañas
        self.actualizar_pestañas()
    
    def actualizar_pestañas(self):
        """Actualiza el contenido de todas las pestañas con los datos del paciente actual"""
        self.actualizar_tab_datos()
        self.actualizar_tab_sesiones()
        self.actualizar_tab_pagos()
        self.actualizar_tab_informes()
        self.actualizar_tab_resumen()
    
    def actualizar_tab_datos(self):
        """Actualiza la pestaña de datos del paciente"""
        # Limpiar pestaña
        for widget in self.tab_datos.winfo_children():
            widget.destroy()
        
        if self.paciente_actual is None:
            return
        
        p = self.paciente_actual
        
        # Título
        tk.Label(
            self.tab_datos,
            text=p.nombre,
            font=("Arial", 18, "bold"),
            bg="white"
        ).pack(pady=15)
        
        # Frame con información principal
        info_frame = tk.Frame(self.tab_datos, bg="#ecf0f1", relief=tk.SOLID, borderwidth=1)
        info_frame.pack(pady=10, padx=30, fill=tk.X)
        
        campos = [
            ("Tipo de paciente:", p.tipo.value),
            ("Costo por sesión:", f"${p.costo_sesion:,.0f}"),
            ("Arancel social:", "✓ Sí" if p.arancel_social else "✗ No"),
            ("Fecha de registro:", p.fecha_creacion.strftime("%d/%m/%Y")),
        ]
        
        for i, (label, valor) in enumerate(campos):
            frame_fila = tk.Frame(info_frame, bg="#ecf0f1")
            frame_fila.pack(fill=tk.X, padx=15, pady=8)
            
            tk.Label(
                frame_fila,
                text=label,
                font=("Arial", 10, "bold"),
                bg="#ecf0f1",
                fg="#2c3e50",
                anchor="w",
                width=25
            ).pack(side=tk.LEFT)
            
            tk.Label(
                frame_fila,
                text=valor,
                font=("Arial", 10),
                bg="#ecf0f1",
                fg="#34495e"
            ).pack(side=tk.RIGHT, padx=10)
        
        # Frame con deuda (más destacado)
        deuda_color = "#e74c3c" if p.deuda > 0 else "#27ae60"
        deuda_frame = tk.Frame(self.tab_datos, bg=deuda_color, relief=tk.SOLID, borderwidth=2)
        deuda_frame.pack(pady=15, padx=30, fill=tk.X)
        
        tk.Label(
            deuda_frame,
            text="DEUDA ACTUAL",
            font=("Arial", 11, "bold"),
            bg=deuda_color,
            fg="white"
        ).pack(pady=(5, 0))
        
        deuda_texto = f"${p.deuda:,.0f}" if p.deuda >= 0 else f"${abs(p.deuda):,.0f} (Saldo a favor)"
        tk.Label(
            deuda_frame,
            text=deuda_texto,
            font=("Arial", 16, "bold"),
            bg=deuda_color,
            fg="white"
        ).pack(pady=(0, 10))
        
        # Resumen de sesiones, pagos e informes
        sesiones = db.obtener_sesiones_paciente(p.id)
        pagos = db.obtener_pagos_paciente(p.id)
        informes = db.obtener_informes_paciente(p.id)
        
        sesiones_paga = len([s for s in sesiones if s.estado == EstadoSesion.PAGA])
        sesiones_pendiente = len([s for s in sesiones if s.estado == EstadoSesion.PENDIENTE])
        informes_pagados = len([i for i in informes if i.estado_pago == EstadoPagoInforme.PAGADO])
        
        # Frame con estadísticas
        stats_frame = tk.Frame(self.tab_datos, bg="white")
        stats_frame.pack(pady=10, padx=30, fill=tk.X)
        
        stats = [
            (f"Sesiones: {len(sesiones)}", f"✓ {sesiones_paga} | ⏳ {sesiones_pendiente}"),
            (f"Pagos registrados: {len(pagos)}", f"Total: ${sum(p.monto for p in pagos):,.0f}"),
            (f"Informes: {len(informes)}", f"✓ {informes_pagados} | ⏳ {len(informes) - informes_pagados}"),
        ]
        
        for label, valor in stats:
            frame_stat = tk.Frame(stats_frame, bg="white")
            frame_stat.pack(fill=tk.X, pady=5)
            
            tk.Label(
                frame_stat,
                text=label,
                font=("Arial", 10),
                bg="white",
                fg="#7f8c8d",
                anchor="w"
            ).pack(side=tk.LEFT)
            
            tk.Label(
                frame_stat,
                text=valor,
                font=("Arial", 10, "bold"),
                bg="white",
                fg="#2c3e50"
            ).pack(side=tk.RIGHT)
        
        # Notas (si existen)
        if p.notas:
            tk.Label(
                self.tab_datos,
                text="Notas:",
                font=("Arial", 10, "bold"),
                bg="white"
            ).pack(pady=(15, 5), anchor="w", padx=30)
            
            notas_frame = tk.Frame(self.tab_datos, bg="#fffacd", relief=tk.SOLID, borderwidth=1)
            notas_frame.pack(padx=30, pady=(0, 15), fill=tk.BOTH, expand=False)
            
            tk.Label(
                notas_frame,
                text=p.notas,
                font=("Arial", 10),
                bg="#fffacd",
                fg="#2c3e50",
                wraplength=600,
                justify=tk.LEFT
            ).pack(padx=10, pady=10)
        
        # Botones de acción
        frame_botones = tk.Frame(self.tab_datos, bg="white")
        frame_botones.pack(pady=20)
        
        tk.Button(
            frame_botones,
            text="✏️ Editar",
            command=self.editar_paciente_actual,
            bg="#3498db",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=20,
            pady=5
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            frame_botones,
            text="🗑️ Eliminar",
            command=self.eliminar_paciente_actual,
            bg="#e74c3c",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=20,
            pady=5
        ).pack(side=tk.LEFT, padx=5)
    
    # ===== DIÁLOGOS Y ACCIONES =====
    
    def abrir_dialogo_nuevo_paciente(self):
        """Abre un diálogo para crear un nuevo paciente"""
        if self.paciente_actual is not None:
            # Si ya hay un paciente seleccionado, limpiar selección
            self.paciente_actual = None
            self.notebook.pack_forget()
            self.label_sin_seleccion.pack(expand=True)
        
        # Crear ventana de diálogo
        dialogo = tk.Toplevel(self.root)
        dialogo.title("Nuevo Paciente")
        dialogo.geometry("500x600")
        dialogo.resizable(False, False)
        
        # Centrar ventana
        dialogo.transient(self.root)
        dialogo.grab_set()
        
        # Título
        tk.Label(
            dialogo,
            text="Crear Nuevo Paciente",
            font=("Arial", 14, "bold")
        ).pack(pady=20)
        
        # Frame para campos
        frame_campos = tk.Frame(dialogo)
        frame_campos.pack(padx=30, pady=10, fill=tk.BOTH, expand=True)
        
        # Nombre
        tk.Label(frame_campos, text="Nombre:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w", pady=10)
        entry_nombre = tk.Entry(frame_campos, width=35, font=("Arial", 10))
        entry_nombre.grid(row=0, column=1, sticky="w", pady=10)
        
        # Tipo de paciente
        tk.Label(frame_campos, text="Tipo:", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky="w", pady=10)
        combo_tipo = ttk.Combobox(frame_campos, width=33, state="readonly")
        combo_tipo['values'] = [tipo.value for tipo in TipoPaciente]
        combo_tipo.current(0)
        combo_tipo.grid(row=1, column=1, sticky="w", pady=10)
        
        # Costo por sesión
        tk.Label(frame_campos, text="Costo por sesión:", font=("Arial", 10, "bold")).grid(row=2, column=0, sticky="w", pady=10)
        entry_costo = tk.Entry(frame_campos, width=15, font=("Arial", 10))
        entry_costo.insert(0, "0")
        entry_costo.grid(row=2, column=1, sticky="w", pady=10)
        
        # Arancel social
        tk.Label(frame_campos, text="Arancel social:", font=("Arial", 10, "bold")).grid(row=3, column=0, sticky="w", pady=10)
        var_arancel = tk.BooleanVar()
        check_arancel = tk.Checkbutton(
            frame_campos,
            variable=var_arancel,
            font=("Arial", 10),
            bg="white"
        )
        check_arancel.grid(row=3, column=1, sticky="w", pady=10)
        
        # Deuda inicial (opcional)
        tk.Label(frame_campos, text="Deuda inicial (opcional):", font=("Arial", 10, "bold")).grid(row=4, column=0, sticky="w", pady=10)
        entry_deuda = tk.Entry(frame_campos, width=15, font=("Arial", 10))
        entry_deuda.insert(0, "0")
        entry_deuda.grid(row=4, column=1, sticky="w", pady=10)
        
        # Notas
        tk.Label(frame_campos, text="Notas:", font=("Arial", 10, "bold")).grid(row=5, column=0, sticky="nw", pady=10)
        text_notas = tk.Text(frame_campos, width=35, height=5, font=("Arial", 10))
        text_notas.grid(row=5, column=1, sticky="w", pady=10)
        
        # Botones
        frame_botones = tk.Frame(dialogo)
        frame_botones.pack(pady=20)
        
        def guardar_paciente():
            try:
                # Validar campos obligatorios
                nombre = entry_nombre.get().strip()
                if not nombre:
                    messagebox.showerror("Error", "El nombre es obligatorio")
                    return
                
                tipo_paciente_str = combo_tipo.get()
                costo_str = entry_costo.get().strip()
                deuda_str = entry_deuda.get().strip()
                
                if not costo_str:
                    messagebox.showerror("Error", "El costo es obligatorio")
                    return
                
                try:
                    costo = float(costo_str)
                except ValueError:
                    messagebox.showerror("Error", "El costo debe ser un número válido")
                    return
                
                # Validar deuda inicial
                deuda = 0.0
                if deuda_str:
                    try:
                        deuda = float(deuda_str)
                    except ValueError:
                        messagebox.showerror("Error", "La deuda inicial debe ser un número válido")
                        return
                
                # Mapear el tipo de paciente
                tipo_map = {
                    "Estándar": TipoPaciente.ESTANDAR,
                    "Mensual": TipoPaciente.MENSUAL,
                    "Diagnóstico": TipoPaciente.DIAGNOSTICO
                }
                tipo_paciente = tipo_map[tipo_paciente_str]
                
                # Crear paciente
                paciente = Paciente(
                    id=None,
                    nombre=nombre,
                    tipo=tipo_paciente,
                    costo_sesion=costo,
                    deuda=deuda,
                    arancel_social=var_arancel.get(),
                    notas=text_notas.get("1.0", tk.END).strip(),
                    fecha_creacion=datetime.now()
                )
                
                # Guardar en BD
                db.guardar_paciente(paciente)
                
                # Recargar lista
                self.cargar_lista_pacientes()
                
                # Mostrar mensaje de éxito
                messagebox.showinfo("Éxito", f"Paciente {nombre} creado correctamente")
                
                # Cerrar diálogo
                dialogo.destroy()
                
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar paciente: {e}")
        
        tk.Button(
            frame_botones,
            text="✓ Guardar",
            command=guardar_paciente,
            bg="#27ae60",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=20,
            pady=5
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            frame_botones,
            text="✗ Cancelar",
            command=dialogo.destroy,
            bg="#95a5a6",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=20,
            pady=5
        ).pack(side=tk.LEFT, padx=5)
    
    def editar_paciente_actual(self):
        """Edita el paciente seleccionado"""
        if self.paciente_actual is None:
            return
        
        # Crear ventana de diálogo
        dialogo = tk.Toplevel(self.root)
        dialogo.title("Editar Paciente")
        dialogo.geometry("500x600")
        dialogo.resizable(False, False)
        
        # Centrar ventana
        dialogo.transient(self.root)
        dialogo.grab_set()
        
        # Título
        tk.Label(
            dialogo,
            text="Editar Paciente",
            font=("Arial", 14, "bold")
        ).pack(pady=20)
        
        # Frame para campos
        frame_campos = tk.Frame(dialogo)
        frame_campos.pack(padx=30, pady=10, fill=tk.BOTH, expand=True)
        
        p = self.paciente_actual
        
        # Nombre
        tk.Label(frame_campos, text="Nombre:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w", pady=10)
        entry_nombre = tk.Entry(frame_campos, width=35, font=("Arial", 10))
        entry_nombre.insert(0, p.nombre)
        entry_nombre.grid(row=0, column=1, sticky="w", pady=10)
        
        # Tipo de paciente
        tk.Label(frame_campos, text="Tipo:", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky="w", pady=10)
        combo_tipo = ttk.Combobox(frame_campos, width=33, state="readonly")
        combo_tipo['values'] = [tipo.value for tipo in TipoPaciente]
        combo_tipo.set(p.tipo.value)
        combo_tipo.grid(row=1, column=1, sticky="w", pady=10)
        
        # Costo por sesión
        tk.Label(frame_campos, text="Costo por sesión:", font=("Arial", 10, "bold")).grid(row=2, column=0, sticky="w", pady=10)
        entry_costo = tk.Entry(frame_campos, width=15, font=("Arial", 10))
        entry_costo.insert(0, str(p.costo_sesion))
        entry_costo.grid(row=2, column=1, sticky="w", pady=10)
        
        # Arancel social
        tk.Label(frame_campos, text="Arancel social:", font=("Arial", 10, "bold")).grid(row=3, column=0, sticky="w", pady=10)
        var_arancel = tk.BooleanVar(value=p.arancel_social)
        check_arancel = tk.Checkbutton(
            frame_campos,
            variable=var_arancel,
            font=("Arial", 10),
            bg="white"
        )
        check_arancel.grid(row=3, column=1, sticky="w", pady=10)
        
        # Deuda actual (editable)
        tk.Label(frame_campos, text="Deuda:", font=("Arial", 10, "bold")).grid(row=4, column=0, sticky="w", pady=10)
        entry_deuda = tk.Entry(frame_campos, width=15, font=("Arial", 10))
        entry_deuda.insert(0, str(p.deuda))
        entry_deuda.grid(row=4, column=1, sticky="w", pady=10)
        
        # Notas
        tk.Label(frame_campos, text="Notas:", font=("Arial", 10, "bold")).grid(row=5, column=0, sticky="nw", pady=10)
        text_notas = tk.Text(frame_campos, width=35, height=5, font=("Arial", 10))
        text_notas.insert("1.0", p.notas if p.notas else "")
        text_notas.grid(row=5, column=1, sticky="w", pady=10)
        
        # Botones
        frame_botones = tk.Frame(dialogo)
        frame_botones.pack(pady=20)
        
        def guardar_cambios():
            try:
                # Validar campos obligatorios
                nombre = entry_nombre.get().strip()
                if not nombre:
                    messagebox.showerror("Error", "El nombre es obligatorio")
                    return
                
                tipo_paciente_str = combo_tipo.get()
                costo_str = entry_costo.get().strip()
                deuda_str = entry_deuda.get().strip()
                
                if not costo_str:
                    messagebox.showerror("Error", "El costo es obligatorio")
                    return
                
                try:
                    costo = float(costo_str)
                except ValueError:
                    messagebox.showerror("Error", "El costo debe ser un número válido")
                    return
                
                # Validar deuda
                try:
                    deuda = float(deuda_str) if deuda_str else 0.0
                except ValueError:
                    messagebox.showerror("Error", "La deuda debe ser un número válido")
                    return
                
                # Mapear el tipo de paciente
                tipo_map = {
                    "Estándar": TipoPaciente.ESTANDAR,
                    "Mensual": TipoPaciente.MENSUAL,
                    "Diagnóstico": TipoPaciente.DIAGNOSTICO
                }
                tipo_paciente = tipo_map[tipo_paciente_str]
                
                # Actualizar paciente
                self.paciente_actual.nombre = nombre
                self.paciente_actual.tipo = tipo_paciente
                self.paciente_actual.costo_sesion = costo
                self.paciente_actual.deuda = deuda
                self.paciente_actual.arancel_social = var_arancel.get()
                self.paciente_actual.notas = text_notas.get("1.0", tk.END).strip()
                
                # Guardar en BD
                db.guardar_paciente(self.paciente_actual)
                
                # Recargar lista y actualizar vista
                self.cargar_lista_pacientes()
                self.actualizar_pestañas()
                
                # Mostrar mensaje de éxito
                messagebox.showinfo("Éxito", f"Paciente {nombre} actualizado correctamente")
                
                # Cerrar diálogo
                dialogo.destroy()
                
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar cambios: {e}")
        
        tk.Button(
            frame_botones,
            text="✓ Guardar",
            command=guardar_cambios,
            bg="#27ae60",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=20,
            pady=5
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            frame_botones,
            text="✗ Cancelar",
            command=dialogo.destroy,
            bg="#95a5a6",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=20,
            pady=5
        ).pack(side=tk.LEFT, padx=5)
    
    def eliminar_paciente_actual(self):
        """Elimina el paciente seleccionado con confirmación"""
        if self.paciente_actual is None:
            return
        
        respuesta = messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Estás seguro de que querés eliminar a {self.paciente_actual.nombre}?\n\n"
            "Esto eliminará TODOS los registros asociados:\n"
            "- Sesiones\n"
            "- Pagos\n"
            "- Informes\n\n"
            "Esta acción NO se puede deshacer."
        )
        
        if respuesta:
            db.eliminar_paciente(self.paciente_actual.id)
            messagebox.showinfo("Eliminado", f"{self.paciente_actual.nombre} fue eliminado correctamente")
            
            # Limpiar selección y recargar lista
            self.paciente_actual = None
            self.notebook.pack_forget()
            self.label_sin_seleccion.pack(expand=True)
            self.cargar_lista_pacientes()
    
    def mostrar_reporte_mensual(self):
        """Muestra el reporte mensual mejorado con desglose por tipo de paciente"""
        from datetime import datetime
        
        # Crear ventana de reporte
        ventana_reporte = tk.Toplevel(self.root)
        ventana_reporte.title("Reporte Mensual")
        ventana_reporte.geometry("900x750")
        
        # Título
        tk.Label(
            ventana_reporte,
            text="Reporte Mensual de Clínica",
            font=("Arial", 16, "bold"),
            fg="#2c3e50"
        ).pack(pady=10)
        
        # ===== SELECTOR DE MES/AÑO =====
        frame_selector = tk.Frame(ventana_reporte, bg="#ecf0f1", relief=tk.SOLID, borderwidth=1)
        frame_selector.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(
            frame_selector,
            text="Seleccionar mes:",
            font=("Arial", 10),
            bg="#ecf0f1"
        ).pack(side=tk.LEFT, padx=10, pady=10)
        
        meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                 "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        
        ahora = datetime.now()
        combo_mes = ttk.Combobox(
            frame_selector,
            values=meses,
            state="readonly",
            width=15,
            font=("Arial", 10)
        )
        combo_mes.set(meses[ahora.month - 1])
        combo_mes.pack(side=tk.LEFT, padx=5)
        
        tk.Label(
            frame_selector,
            text="Año:",
            font=("Arial", 10),
            bg="#ecf0f1"
        ).pack(side=tk.LEFT, padx=(20, 5))
        
        años = [str(año) for año in range(2020, ahora.year + 1)]
        combo_año = ttk.Combobox(
            frame_selector,
            values=años,
            state="readonly",
            width=10,
            font=("Arial", 10)
        )
        combo_año.set(str(ahora.year))
        combo_año.pack(side=tk.LEFT, padx=5)
        
        def actualizar_reporte():
            """Actualiza el reporte con el mes/año seleccionado"""
            mes = combo_mes.current() + 1
            año = int(combo_año.get())
            
            # Limpiar frame_reporte
            for widget in frame_reporte.winfo_children():
                widget.destroy()
            
            # Obtener estadísticas del mes seleccionado
            stats = db.obtener_estadisticas_mensuales(mes, año)
            
            # ===== SECCIÓN 1: INGRESOS DEL MES =====
            tk.Label(
                frame_reporte,
                text="💰 INGRESOS DEL MES",
                font=("Arial", 12, "bold"),
                bg="#f8f9fa",
                fg="#27ae60"
            ).pack(pady=(15, 10), anchor="w", padx=20)
            
            # Frame de ingresos
            frame_ingresos = tk.Frame(frame_reporte, bg="white", relief=tk.SOLID, borderwidth=1)
            frame_ingresos.pack(fill=tk.X, padx=20, pady=5)
            
            ingresos_data = [
                ("Total cobrado:", f"${stats['total_cobrado']:,.2f}", "#27ae60"),
                ("  └─ Pacientes Estándar:", f"${stats['cobrado_estandar']:,.2f}", "#3498db"),
                ("  └─ Pacientes Mensuales:", f"${stats['cobrado_mensual']:,.2f}", "#9b59b6"),
                ("  └─ Diagnósticos:", f"${stats['cobrado_diagnostico']:,.2f}", "#e74c3c"),
                ("Informes (por cobrar):", f"${stats['informes_total']:,.2f}", "#f39c12"),
            ]
            
            for label, valor, color in ingresos_data:
                frame_fila = tk.Frame(frame_ingresos, bg="white")
                frame_fila.pack(fill=tk.X, padx=15, pady=5)
                
                tk.Label(
                    frame_fila,
                    text=label,
                    font=("Arial", 10),
                    bg="white",
                    fg="#2c3e50",
                    anchor="w",
                    width=35
                ).pack(side=tk.LEFT)
                
                tk.Label(
                    frame_fila,
                    text=valor,
                    font=("Arial", 10, "bold"),
                    bg="white",
                    fg=color
                ).pack(side=tk.RIGHT, padx=10)
            
            # Separador
            ttk.Separator(frame_reporte, orient='horizontal').pack(fill=tk.X, pady=15, padx=20)
            
            # ===== SECCIÓN 2: DEUDA ACUMULADA =====
            tk.Label(
                frame_reporte,
                text="📊 DEUDA ACUMULADA",
                font=("Arial", 12, "bold"),
                bg="#f8f9fa",
                fg="#e74c3c"
            ).pack(pady=(15, 10), anchor="w", padx=20)
            
            # Frame de deuda
            frame_deuda = tk.Frame(frame_reporte, bg="white", relief=tk.SOLID, borderwidth=1)
            frame_deuda.pack(fill=tk.X, padx=20, pady=5)
            
            deuda_data = [
                ("Total deuda:", f"${stats['deuda_total']:,.2f}", "#e74c3c"),
                ("  └─ Pacientes Estándar:", f"${stats['deuda_estandar']:,.2f}", "#3498db"),
                ("  └─ Pacientes Mensuales:", f"${stats['deuda_mensual']:,.2f}", "#9b59b6"),
                ("  └─ Diagnósticos:", f"${stats['deuda_diagnostico']:,.2f}", "#e74c3c"),
            ]
            
            for label, valor, color in deuda_data:
                frame_fila = tk.Frame(frame_deuda, bg="white")
                frame_fila.pack(fill=tk.X, padx=15, pady=5)
                
                tk.Label(
                    frame_fila,
                    text=label,
                    font=("Arial", 10),
                    bg="white",
                    fg="#2c3e50",
                    anchor="w",
                    width=35
                ).pack(side=tk.LEFT)
                
                tk.Label(
                    frame_fila,
                    text=valor,
                    font=("Arial", 10, "bold"),
                    bg="white",
                    fg=color
                ).pack(side=tk.RIGHT, padx=10)
            
            # Separador
            ttk.Separator(frame_reporte, orient='horizontal').pack(fill=tk.X, pady=15, padx=20)
            
            # ===== SECCIÓN 3: RESUMEN POR PACIENTE =====
            if stats["detalle_pacientes"]:
                tk.Label(
                    frame_reporte,
                    text="👥 RESUMEN POR PACIENTE",
                    font=("Arial", 12, "bold"),
                    bg="#f8f9fa",
                    fg="#2c3e50"
                ).pack(pady=(15, 10), anchor="w", padx=20)
                
                for pac in stats["detalle_pacientes"]:
                    frame_pac = tk.Frame(frame_reporte, bg="#ecf0f1", relief=tk.SOLID, borderwidth=1)
                    frame_pac.pack(fill=tk.X, pady=5, padx=20)
                    
                    # Nombre y tipo
                    frame_header = tk.Frame(frame_pac, bg="#ecf0f1")
                    frame_header.pack(fill=tk.X, padx=10, pady=(8, 0))
                    
                    tk.Label(
                        frame_header,
                        text=pac["nombre"],
                        font=("Arial", 10, "bold"),
                        bg="#ecf0f1",
                        fg="#2c3e50"
                    ).pack(side=tk.LEFT)
                    
                    tipo_color = {
                        "Estándar": "#3498db",
                        "Mensual": "#9b59b6",
                        "Diagnóstico": "#e74c3c"
                    }.get(pac["tipo"], "#95a5a6")
                    
                    tk.Label(
                        frame_header,
                        text=f"({pac['tipo']})",
                        font=("Arial", 9),
                        bg="#ecf0f1",
                        fg=tipo_color
                    ).pack(side=tk.LEFT, padx=5)
                    
                    if pac["arancel_social"]:
                        tk.Label(
                            frame_header,
                            text="🏥 Arancel Social",
                            font=("Arial", 8),
                            bg="#ecf0f1",
                            fg="#f39c12"
                        ).pack(side=tk.LEFT, padx=5)
                    
                    # Cobrado y deuda
                    frame_datos = tk.Frame(frame_pac, bg="#ecf0f1")
                    frame_datos.pack(fill=tk.X, padx=20, pady=5)
                    
                    tk.Label(
                        frame_datos,
                        text=f"Cobrado: ${pac['cobrado']:,.2f}",
                        font=("Arial", 9),
                        bg="#ecf0f1",
                        fg="#27ae60"
                    ).pack(side=tk.LEFT)
                    
                    tk.Label(
                        frame_datos,
                        text=f"Deuda: ${pac['deuda']:,.2f}",
                        font=("Arial", 9),
                        bg="#ecf0f1",
                        fg="#e74c3c"
                    ).pack(side=tk.RIGHT, padx=10)
                    
                    tk.Label(frame_pac, bg="#ecf0f1").pack(pady=3)
            
            else:
                tk.Label(
                    frame_reporte,
                    text="No hay movimientos en el mes seleccionado",
                    font=("Arial", 11),
                    bg="#f8f9fa",
                    fg="#95a5a6"
                ).pack(pady=20)
            
            # Guardar stats para usar en exportar PDF
            actualizar_reporte.stats_actual = stats
        
        # Botón para actualizar
        tk.Button(
            frame_selector,
            text="🔄 Actualizar",
            command=actualizar_reporte,
            bg="#3498db",
            fg="white",
            font=("Arial", 10),
            padx=15
        ).pack(side=tk.LEFT, padx=20)
        
        # Botón para exportar PDF
        def exportar_pdf():
            """Exporta el reporte actual a PDF"""
            from tkinter import filedialog
            
            if not hasattr(actualizar_reporte, 'stats_actual'):
                messagebox.showwarning("Advertencia", "Primero genera el reporte")
                return
            
            ruta = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                initialfile=f"Reporte_{combo_mes.get()}_{combo_año.get()}.pdf"
            )
            
            if ruta:
                try:
                    mes = combo_mes.current() + 1
                    año = int(combo_año.get())
                    db.exportar_reporte_pdf(actualizar_reporte.stats_actual, mes, año, ruta)
                    messagebox.showinfo("Éxito", f"PDF exportado a:\n{ruta}")
                except Exception as e:
                    messagebox.showerror("Error", f"Error al exportar PDF:\n{e}")
        
        tk.Button(
            frame_selector,
            text="📄 Exportar PDF",
            command=exportar_pdf,
            bg="#27ae60",
            fg="white",
            font=("Arial", 10),
            padx=15
        ).pack(side=tk.LEFT, padx=5)
        
        # Frame con scroll para el reporte
        frame_scroll = tk.Frame(ventana_reporte)
        frame_scroll.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        canvas = tk.Canvas(frame_scroll, bg="#f8f9fa")
        scrollbar = tk.Scrollbar(frame_scroll, orient="vertical", command=canvas.yview)
        frame_reporte = tk.Frame(canvas, bg="#f8f9fa")
        
        frame_reporte.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=frame_reporte, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Cargar reporte inicial
        actualizar_reporte()
        
        # ===== SECCIÓN 1: INGRESOS DEL MES =====
        tk.Label(
            frame_reporte,
            text="💰 INGRESOS DEL MES",
            font=("Arial", 12, "bold"),
            bg="#f8f9fa",
            fg="#27ae60"
        ).pack(pady=(15, 10), anchor="w", padx=20)
        
        # Frame de ingresos
        frame_ingresos = tk.Frame(frame_reporte, bg="white", relief=tk.SOLID, borderwidth=1)
        frame_ingresos.pack(fill=tk.X, padx=20, pady=5)
        
        ingresos_data = [
            ("Total cobrado:", f"${stats['total_cobrado']:,.2f}", "#27ae60"),
            ("  └─ Pacientes Estándar:", f"${stats['cobrado_estandar']:,.2f}", "#3498db"),
            ("  └─ Pacientes Mensuales:", f"${stats['cobrado_mensual']:,.2f}", "#9b59b6"),
            ("  └─ Diagnósticos:", f"${stats['cobrado_diagnostico']:,.2f}", "#e74c3c"),
            ("Informes (por cobrar):", f"${stats['informes_total']:,.2f}", "#f39c12"),
        ]
        
        for label, valor, color in ingresos_data:
            frame_fila = tk.Frame(frame_ingresos, bg="white")
            frame_fila.pack(fill=tk.X, padx=15, pady=5)
            
            tk.Label(
                frame_fila,
                text=label,
                font=("Arial", 10),
                bg="white",
                fg="#2c3e50",
                anchor="w",
                width=35
            ).pack(side=tk.LEFT)
            
            tk.Label(
                frame_fila,
                text=valor,
                font=("Arial", 10, "bold"),
                bg="white",
                fg=color
            ).pack(side=tk.RIGHT, padx=10)
        
        # Separador
        ttk.Separator(frame_reporte, orient='horizontal').pack(fill=tk.X, pady=15, padx=20)
        
        # ===== SECCIÓN 2: DEUDA ACUMULADA =====
        tk.Label(
            frame_reporte,
            text="📊 DEUDA ACUMULADA",
            font=("Arial", 12, "bold"),
            bg="#f8f9fa",
            fg="#e74c3c"
        ).pack(pady=(15, 10), anchor="w", padx=20)
        
        # Frame de deuda
        frame_deuda = tk.Frame(frame_reporte, bg="white", relief=tk.SOLID, borderwidth=1)
        frame_deuda.pack(fill=tk.X, padx=20, pady=5)
        
        deuda_data = [
            ("Total deuda:", f"${stats['deuda_total']:,.2f}", "#e74c3c"),
            ("  └─ Pacientes Estándar:", f"${stats['deuda_estandar']:,.2f}", "#3498db"),
            ("  └─ Pacientes Mensuales:", f"${stats['deuda_mensual']:,.2f}", "#9b59b6"),
            ("  └─ Diagnósticos:", f"${stats['deuda_diagnostico']:,.2f}", "#e74c3c"),
        ]
        
        for label, valor, color in deuda_data:
            frame_fila = tk.Frame(frame_deuda, bg="white")
            frame_fila.pack(fill=tk.X, padx=15, pady=5)
            
            tk.Label(
                frame_fila,
                text=label,
                font=("Arial", 10),
                bg="white",
                fg="#2c3e50",
                anchor="w",
                width=35
            ).pack(side=tk.LEFT)
            
            tk.Label(
                frame_fila,
                text=valor,
                font=("Arial", 10, "bold"),
                bg="white",
                fg=color
            ).pack(side=tk.RIGHT, padx=10)
        
        # Separador
        ttk.Separator(frame_reporte, orient='horizontal').pack(fill=tk.X, pady=15, padx=20)
        
        # ===== SECCIÓN 3: RESUMEN POR PACIENTE =====
        if stats["detalle_pacientes"]:
            tk.Label(
                frame_reporte,
                text="👥 RESUMEN POR PACIENTE",
                font=("Arial", 12, "bold"),
                bg="#f8f9fa",
                fg="#2c3e50"
            ).pack(pady=(15, 10), anchor="w", padx=20)
            
            for pac in stats["detalle_pacientes"]:
                frame_pac = tk.Frame(frame_reporte, bg="#ecf0f1", relief=tk.SOLID, borderwidth=1)
                frame_pac.pack(fill=tk.X, pady=5, padx=20)
                
                # Nombre y tipo
                frame_header = tk.Frame(frame_pac, bg="#ecf0f1")
                frame_header.pack(fill=tk.X, padx=10, pady=(8, 0))
                
                tk.Label(
                    frame_header,
                    text=pac["nombre"],
                    font=("Arial", 10, "bold"),
                    bg="#ecf0f1",
                    fg="#2c3e50"
                ).pack(side=tk.LEFT)
                
                tipo_color = {
                    "Estándar": "#3498db",
                    "Mensual": "#9b59b6",
                    "Diagnóstico": "#e74c3c"
                }.get(pac["tipo"], "#95a5a6")
                
                tk.Label(
                    frame_header,
                    text=f"({pac['tipo']})",
                    font=("Arial", 9),
                    bg="#ecf0f1",
                    fg=tipo_color
                ).pack(side=tk.LEFT, padx=5)
                
                if pac["arancel_social"]:
                    tk.Label(
                        frame_header,
                        text="🏥 Arancel Social",
                        font=("Arial", 8),
                        bg="#ecf0f1",
                        fg="#f39c12"
                    ).pack(side=tk.LEFT, padx=5)
                
                # Cobrado y deuda
                frame_datos = tk.Frame(frame_pac, bg="#ecf0f1")
                frame_datos.pack(fill=tk.X, padx=20, pady=5)
                
                tk.Label(
                    frame_datos,
                    text=f"Cobrado: ${pac['cobrado']:,.2f}",
                    font=("Arial", 9),
                    bg="#ecf0f1",
                    fg="#27ae60"
                ).pack(side=tk.LEFT)
                
                tk.Label(
                    frame_datos,
                    text=f"Deuda: ${pac['deuda']:,.2f}",
                    font=("Arial", 9),
                    bg="#ecf0f1",
                    fg="#e74c3c"
                ).pack(side=tk.RIGHT, padx=10)
                
                tk.Label(frame_pac, bg="#ecf0f1").pack(pady=3)
    
    # ===== PESTAÑA DE SESIONES =====
    
    def actualizar_tab_sesiones(self):
        """Actualiza la pestaña de sesiones del paciente"""
        # Limpiar pestaña
        for widget in self.tab_sesiones.winfo_children():
            widget.destroy()
        
        if self.paciente_actual is None:
            return
        
        # Frame superior con botón de nueva sesión
        frame_superior = tk.Frame(self.tab_sesiones, bg="white")
        frame_superior.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(
            frame_superior,
            text="Sesiones",
            font=("Arial", 16, "bold"),
            bg="white"
        ).pack(side=tk.LEFT)
        
        tk.Button(
            frame_superior,
            text="➕ Nueva Sesión",
            command=self.abrir_dialogo_nueva_sesion,
            bg="#27ae60",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=15,
            pady=5
        ).pack(side=tk.RIGHT)
        
        # Obtener sesiones del paciente
        sesiones = db.obtener_sesiones_paciente(self.paciente_actual.id)
        
        if not sesiones:
            tk.Label(
                self.tab_sesiones,
                text="No hay sesiones registradas",
                font=("Arial", 12),
                fg="#95a5a6",
                bg="white"
            ).pack(expand=True)
            return
        
        # Frame con scroll para la lista de sesiones
        frame_scroll = tk.Frame(self.tab_sesiones, bg="white")
        frame_scroll.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        canvas = tk.Canvas(frame_scroll, bg="white")
        scrollbar = tk.Scrollbar(frame_scroll, orient="vertical", command=canvas.yview)
        frame_sesiones = tk.Frame(canvas, bg="white")
        
        frame_sesiones.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=frame_sesiones, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Mostrar cada sesión como una tarjeta
        for sesion in sesiones:
            self.crear_tarjeta_sesion(frame_sesiones, sesion)
    
    def crear_tarjeta_sesion(self, parent, sesion: Sesion):
        """Crea una tarjeta visual para una sesión"""
        # Frame de la tarjeta
        color_borde = "#27ae60" if sesion.estado == EstadoSesion.PAGA else "#e74c3c"
        
        frame_tarjeta = tk.Frame(
            parent,
            bg="white",
            relief=tk.SOLID,
            borderwidth=2,
            highlightbackground=color_borde,
            highlightthickness=2
        )
        frame_tarjeta.pack(fill=tk.X, pady=5, padx=5)
        
        # Contenido de la tarjeta
        frame_contenido = tk.Frame(frame_tarjeta, bg="white")
        frame_contenido.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # Primera fila: Fecha y estado
        frame_fila1 = tk.Frame(frame_contenido, bg="white")
        frame_fila1.pack(fill=tk.X)
        
        tk.Label(
            frame_fila1,
            text=sesion.fecha.strftime("%d/%m/%Y"),
            font=("Arial", 12, "bold"),
            bg="white"
        ).pack(side=tk.LEFT)
        
        estado_texto = "✓ PAGA" if sesion.estado == EstadoSesion.PAGA else "⏳ PENDIENTE"
        estado_color = "#27ae60" if sesion.estado == EstadoSesion.PAGA else "#e74c3c"
        
        tk.Label(
            frame_fila1,
            text=estado_texto,
            font=("Arial", 10, "bold"),
            bg="white",
            fg=estado_color
        ).pack(side=tk.RIGHT)
        
        # Segunda fila: Tipo y precio
        frame_fila2 = tk.Frame(frame_contenido, bg="white")
        frame_fila2.pack(fill=tk.X, pady=5)
        
        tk.Label(
            frame_fila2,
            text=f"Tipo: {sesion.tipo.value}",
            font=("Arial", 10),
            bg="white",
            fg="#7f8c8d"
        ).pack(side=tk.LEFT)
        
        tk.Label(
            frame_fila2,
            text=f"${sesion.precio:,.0f}",
            font=("Arial", 11, "bold"),
            bg="white"
        ).pack(side=tk.RIGHT)
        
        # Tercera fila: Notas (si hay)
        if sesion.notas:
            tk.Label(
                frame_contenido,
                text=f"Notas: {sesion.notas}",
                font=("Arial", 9),
                bg="white",
                fg="#95a5a6",
                wraplength=600,
                justify=tk.LEFT
            ).pack(anchor=tk.W, pady=(5, 0))
        
        # Botones de acción
        frame_botones = tk.Frame(frame_contenido, bg="white")
        frame_botones.pack(fill=tk.X, pady=(10, 0))
        
        if sesion.estado == EstadoSesion.PENDIENTE:
            tk.Button(
                frame_botones,
                text="✓ Marcar como Paga",
                command=lambda s=sesion: self.marcar_sesion_paga(s),
                bg="#27ae60",
                fg="white",
                font=("Arial", 9),
                padx=10,
                pady=3
            ).pack(side=tk.LEFT, padx=(0, 5))
        
        tk.Button(
            frame_botones,
            text="✏️ Editar",
            command=lambda s=sesion: self.editar_sesion(s),
            bg="#3498db",
            fg="white",
            font=("Arial", 9),
            padx=10,
            pady=3
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            frame_botones,
            text="🗑️ Eliminar",
            command=lambda s=sesion: self.eliminar_sesion(s),
            bg="#e74c3c",
            fg="white",
            font=("Arial", 9),
            padx=10,
            pady=3
        ).pack(side=tk.LEFT, padx=5)
    
    def marcar_sesion_paga(self, sesion: Sesion):
        """Marca una sesión como paga manualmente"""
        respuesta = messagebox.askyesno(
            "Confirmar",
            f"¿Marcar esta sesión como paga?\n\nFecha: {sesion.fecha.strftime('%d/%m/%Y')}\nPrecio: ${sesion.precio:,.0f}"
        )
        
        if respuesta:
            sesion.estado = EstadoSesion.PAGA
            db.guardar_sesion(sesion)
            
            # Actualizar deuda del paciente
            db.actualizar_deuda_paciente(self.paciente_actual.id)
            
            # Recargar paciente y actualizar vista
            self.paciente_actual = db.obtener_paciente(self.paciente_actual.id)
            self.actualizar_pestañas()
            self.cargar_lista_pacientes()
    
    def eliminar_sesion(self, sesion: Sesion):
        """Elimina una sesión con confirmación"""
        respuesta = messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Estás seguro de eliminar esta sesión?\n\n"
            f"Fecha: {sesion.fecha.strftime('%d/%m/%Y')}\n"
            f"Tipo: {sesion.tipo.value}\n"
            f"Precio: ${sesion.precio:,.0f}"
        )
        
        if respuesta:
            db.eliminar_sesion(sesion.id)
            
            # Actualizar deuda del paciente
            db.actualizar_deuda_paciente(self.paciente_actual.id)
            
            # Recargar y actualizar
            self.paciente_actual = db.obtener_paciente(self.paciente_actual.id)
            self.actualizar_pestañas()
            self.cargar_lista_pacientes()
    
    def eliminar_pago(self, pago: Pago):
        """Elimina un pago con confirmación"""
        respuesta = messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Estás seguro de eliminar este pago?\n\n"
            f"Fecha: {pago.fecha.strftime('%d/%m/%Y')}\n"
            f"Monto: ${pago.monto:,.0f}\n"
            f"Concepto: {pago.concepto.value}"
        )
        
        if respuesta:
            db.eliminar_pago(pago.id)
            
            # Actualizar deuda del paciente
            db.actualizar_deuda_paciente(self.paciente_actual.id)
            
            # Recargar y actualizar
            self.paciente_actual = db.obtener_paciente(self.paciente_actual.id)
            self.actualizar_pestañas()
            self.cargar_lista_pacientes()
    
    def editar_sesion(self, sesion: Sesion):
        """Edita una sesión existente"""
        if self.paciente_actual is None:
            return
        
        # Crear ventana de diálogo
        dialogo = tk.Toplevel(self.root)
        dialogo.title("Editar Sesión")
        dialogo.geometry("500x450")
        dialogo.resizable(False, False)
        
        # Centrar ventana
        dialogo.transient(self.root)
        dialogo.grab_set()
        
        # Título
        tk.Label(
            dialogo,
            text="Editar Sesión",
            font=("Arial", 14, "bold")
        ).pack(pady=20)
        
        # Frame para campos
        frame_campos = tk.Frame(dialogo)
        frame_campos.pack(padx=30, pady=10, fill=tk.BOTH, expand=True)
        
        # Fecha
        tk.Label(frame_campos, text="Fecha:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w", pady=10)
        frame_fecha = tk.Frame(frame_campos)
        frame_fecha.grid(row=0, column=1, sticky="w", pady=10)
        
        entry_dia = tk.Entry(frame_fecha, width=5, font=("Arial", 10))
        entry_dia.insert(0, sesion.fecha.strftime("%d"))
        entry_dia.pack(side=tk.LEFT)
        tk.Label(frame_fecha, text="/").pack(side=tk.LEFT)
        
        entry_mes = tk.Entry(frame_fecha, width=5, font=("Arial", 10))
        entry_mes.insert(0, sesion.fecha.strftime("%m"))
        entry_mes.pack(side=tk.LEFT)
        tk.Label(frame_fecha, text="/").pack(side=tk.LEFT)
        
        entry_año = tk.Entry(frame_fecha, width=8, font=("Arial", 10))
        entry_año.insert(0, sesion.fecha.strftime("%Y"))
        entry_año.pack(side=tk.LEFT)
        
        # Tipo de sesión
        tk.Label(frame_campos, text="Tipo:", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky="w", pady=10)
        combo_tipo = ttk.Combobox(frame_campos, width=25, state="readonly")
        combo_tipo['values'] = [tipo.value for tipo in TipoSesion]
        combo_tipo.set(sesion.tipo.value)
        combo_tipo.grid(row=1, column=1, sticky="w", pady=10)
        
        # Precio
        tk.Label(frame_campos, text="Precio:", font=("Arial", 10, "bold")).grid(row=2, column=0, sticky="w", pady=10)
        entry_precio = tk.Entry(frame_campos, width=15, font=("Arial", 10))
        entry_precio.insert(0, str(int(sesion.precio)))
        entry_precio.grid(row=2, column=1, sticky="w", pady=10)
        
        # Estado
        tk.Label(frame_campos, text="Estado:", font=("Arial", 10, "bold")).grid(row=3, column=0, sticky="w", pady=10)
        combo_estado = ttk.Combobox(frame_campos, width=15, state="readonly")
        combo_estado['values'] = [estado.value for estado in EstadoSesion]
        combo_estado.set(sesion.estado.value)
        combo_estado.grid(row=3, column=1, sticky="w", pady=10)
        
        # Notas
        tk.Label(frame_campos, text="Notas:", font=("Arial", 10, "bold")).grid(row=4, column=0, sticky="nw", pady=10)
        text_notas = tk.Text(frame_campos, width=30, height=5, font=("Arial", 10))
        text_notas.insert("1.0", sesion.notas if sesion.notas else "")
        text_notas.grid(row=4, column=1, sticky="w", pady=10)
        
        # Botones
        frame_botones = tk.Frame(dialogo)
        frame_botones.pack(pady=20)
        
        def guardar_cambios():
            try:
                # Validar y crear fecha
                dia = int(entry_dia.get())
                mes = int(entry_mes.get())
                año = int(entry_año.get())
                fecha = datetime(año, mes, dia)
                
                # Mapeo para tipos y estados
                tipo_map = {
                    "Estándar": TipoSesion.ESTANDAR,
                    "Tratamiento de trauma": TipoSesion.TRAUMA,
                    "Pareja": TipoSesion.PAREJA,
                    "Familiar": TipoSesion.FAMILIAR,
                    "Diagnóstico": TipoSesion.DIAGNOSTICO
                }
                
                estado_map = {
                    "Paga": EstadoSesion.PAGA,
                    "Pendiente": EstadoSesion.PENDIENTE
                }
                
                # Actualizar sesión
                sesion.fecha = fecha
                sesion.precio = float(entry_precio.get())
                sesion.tipo = tipo_map[combo_tipo.get()]
                sesion.estado = estado_map[combo_estado.get()]
                sesion.notas = text_notas.get("1.0", tk.END).strip()
                
                # Guardar en BD
                db.guardar_sesion(sesion)
                
                # Actualizar deuda
                db.actualizar_deuda_paciente(self.paciente_actual.id)
                
                # Recargar y actualizar
                self.paciente_actual = db.obtener_paciente(self.paciente_actual.id)
                self.actualizar_pestañas()
                self.cargar_lista_pacientes()
                
                messagebox.showinfo("Éxito", "Sesión actualizada correctamente")
                dialogo.destroy()
                
            except ValueError as e:
                messagebox.showerror("Error", f"Datos inválidos: {e}")
        
        tk.Button(
            frame_botones,
            text="✓ Guardar",
            command=guardar_cambios,
            bg="#27ae60",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=20,
            pady=5
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            frame_botones,
            text="✗ Cancelar",
            command=dialogo.destroy,
            bg="#95a5a6",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=20,
            pady=5
        ).pack(side=tk.LEFT, padx=5)
    
    def abrir_dialogo_nueva_sesion(self):
        """Abre un diálogo para crear una nueva sesión"""
        if self.paciente_actual is None:
            return
        
        # Crear ventana de diálogo
        dialogo = tk.Toplevel(self.root)
        dialogo.title("Nueva Sesión")
        dialogo.geometry("500x450")
        dialogo.resizable(False, False)
        
        # Centrar ventana
        dialogo.transient(self.root)
        dialogo.grab_set()
        
        # Título
        tk.Label(
            dialogo,
            text=f"Nueva sesión para {self.paciente_actual.nombre}",
            font=("Arial", 14, "bold")
        ).pack(pady=20)
        
        # Frame para campos
        frame_campos = tk.Frame(dialogo)
        frame_campos.pack(padx=30, pady=10, fill=tk.BOTH, expand=True)
        
        # Fecha
        tk.Label(frame_campos, text="Fecha:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w", pady=10)
        frame_fecha = tk.Frame(frame_campos)
        frame_fecha.grid(row=0, column=1, sticky="w", pady=10)
        
        entry_dia = tk.Entry(frame_fecha, width=5, font=("Arial", 10))
        entry_dia.insert(0, datetime.now().strftime("%d"))
        entry_dia.pack(side=tk.LEFT)
        tk.Label(frame_fecha, text="/").pack(side=tk.LEFT)
        
        entry_mes = tk.Entry(frame_fecha, width=5, font=("Arial", 10))
        entry_mes.insert(0, datetime.now().strftime("%m"))
        entry_mes.pack(side=tk.LEFT)
        tk.Label(frame_fecha, text="/").pack(side=tk.LEFT)
        
        entry_año = tk.Entry(frame_fecha, width=8, font=("Arial", 10))
        entry_año.insert(0, datetime.now().strftime("%Y"))
        entry_año.pack(side=tk.LEFT)
        
        # Tipo de sesión
        tk.Label(frame_campos, text="Tipo:", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky="w", pady=10)
        combo_tipo = ttk.Combobox(frame_campos, width=25, state="readonly")
        combo_tipo['values'] = [tipo.value for tipo in TipoSesion]
        combo_tipo.current(0)
        combo_tipo.grid(row=1, column=1, sticky="w", pady=10)
        
        # Precio
        tk.Label(frame_campos, text="Precio:", font=("Arial", 10, "bold")).grid(row=2, column=0, sticky="w", pady=10)
        entry_precio = tk.Entry(frame_campos, width=15, font=("Arial", 10))
        entry_precio.insert(0, str(int(self.paciente_actual.costo_sesion)))
        entry_precio.grid(row=2, column=1, sticky="w", pady=10)
        
        # Estado
        tk.Label(frame_campos, text="Estado:", font=("Arial", 10, "bold")).grid(row=3, column=0, sticky="w", pady=10)
        combo_estado = ttk.Combobox(frame_campos, width=15, state="readonly")
        combo_estado['values'] = [estado.value for estado in EstadoSesion]
        combo_estado.current(1)  # Por defecto PENDIENTE
        combo_estado.grid(row=3, column=1, sticky="w", pady=10)
        
        # Notas
        tk.Label(frame_campos, text="Notas:", font=("Arial", 10, "bold")).grid(row=4, column=0, sticky="nw", pady=10)
        text_notas = tk.Text(frame_campos, width=30, height=5, font=("Arial", 10))
        text_notas.grid(row=4, column=1, sticky="w", pady=10)
        
        # Botones
        frame_botones = tk.Frame(dialogo)
        frame_botones.pack(pady=20)
        
        def guardar_sesion():
            try:
                # Validar y crear fecha
                dia = int(entry_dia.get())
                mes = int(entry_mes.get())
                año = int(entry_año.get())
                fecha = datetime(año, mes, dia)
                
                # Mapeo correcto para tipos con nombres largos
                tipo_map = {
                    "Estándar": TipoSesion.ESTANDAR,
                    "Tratamiento de trauma": TipoSesion.TRAUMA,
                    "Pareja": TipoSesion.PAREJA,
                    "Familiar": TipoSesion.FAMILIAR,
                    "Diagnóstico": TipoSesion.DIAGNOSTICO
                }
                
                estado_map = {
                    "Paga": EstadoSesion.PAGA,
                    "Pendiente": EstadoSesion.PENDIENTE
                }
                
                # Crear sesión
                sesion = Sesion(
                    id=None,
                    paciente_id=self.paciente_actual.id,
                    fecha=fecha,
                    precio=float(entry_precio.get()),
                    estado=estado_map[combo_estado.get()],
                    tipo=tipo_map[combo_tipo.get()],
                    notas=text_notas.get("1.0", tk.END).strip()
                )
                
                # Guardar en BD
                db.guardar_sesion(sesion)
                
                # Aplicar saldo a favor si existe
                db.aplicar_saldo_a_favor_a_nueva_sesion(self.paciente_actual.id, sesion)
                
                # Actualizar deuda
                db.actualizar_deuda_paciente(self.paciente_actual.id)
                
                # Recargar y cerrar
                self.paciente_actual = db.obtener_paciente(self.paciente_actual.id)
                self.actualizar_pestañas()
                self.cargar_lista_pacientes()
                dialogo.destroy()
                
                messagebox.showinfo("Éxito", "Sesión registrada correctamente")
                
            except ValueError as e:
                messagebox.showerror("Error", f"Datos inválidos: {e}")
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar sesión: {e}")
        
        tk.Button(
            frame_botones,
            text="✓ Guardar",
            command=guardar_sesion,
            bg="#27ae60",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=20,
            pady=5
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            frame_botones,
            text="✗ Cancelar",
            command=dialogo.destroy,
            bg="#95a5a6",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=20,
            pady=5
        ).pack(side=tk.LEFT, padx=5)

# ===== PESTAÑA DE PAGOS =====

    def actualizar_tab_pagos(self):
        """Actualiza la pestaña de pagos del paciente"""
        # Limpiar pestaña
        for widget in self.tab_pagos.winfo_children():
            widget.destroy()
        
        if self.paciente_actual is None:
            return
        
        # Frame superior con botón de nuevo pago
        frame_superior = tk.Frame(self.tab_pagos, bg="white")
        frame_superior.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(
            frame_superior,
            text="Pagos",
            font=("Arial", 16, "bold"),
            bg="white"
        ).pack(side=tk.LEFT)
        
        tk.Button(
            frame_superior,
            text="➕ Nuevo Pago",
            command=self.abrir_dialogo_nuevo_pago,
            bg="#27ae60",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=15,
            pady=5
        ).pack(side=tk.RIGHT)
        
        # Obtener pagos del paciente
        pagos = db.obtener_pagos_paciente(self.paciente_actual.id)
        
        if not pagos:
            tk.Label(
                self.tab_pagos,
                text="No hay pagos registrados",
                font=("Arial", 12),
                fg="#95a5a6",
                bg="white"
            ).pack(expand=True)
            return
        
        # Frame con scroll para la lista de pagos
        frame_scroll = tk.Frame(self.tab_pagos, bg="white")
        frame_scroll.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        canvas = tk.Canvas(frame_scroll, bg="white")
        scrollbar = tk.Scrollbar(frame_scroll, orient="vertical", command=canvas.yview)
        frame_pagos = tk.Frame(canvas, bg="white")
        
        frame_pagos.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=frame_pagos, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Mostrar cada pago como una tarjeta
        for pago in pagos:
            self.crear_tarjeta_pago(frame_pagos, pago)
    def crear_tarjeta_pago(self, parent, pago: Pago):
        """Crea una tarjeta visual para un pago"""
        # Frame de la tarjeta
        frame_tarjeta = tk.Frame(
            parent,
            bg="white",
            relief=tk.SOLID,
            borderwidth=2,
            highlightbackground="#2980b9",
            highlightthickness=2
        )
        frame_tarjeta.pack(fill=tk.X, pady=5, padx=5)
        
        # Contenido de la tarjeta
        frame_contenido = tk.Frame(frame_tarjeta, bg="white")
        frame_contenido.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # Primera fila: Fecha y monto
        frame_fila1 = tk.Frame(frame_contenido, bg="white")
        frame_fila1.pack(fill=tk.X)
        
        tk.Label(
            frame_fila1,
            text=pago.fecha.strftime("%d/%m/%Y"),
            font=("Arial", 12, "bold"),
            bg="white"
        ).pack(side=tk.LEFT)
        
        tk.Label(
            frame_fila1,
            text=f"${pago.monto:,.0f}",
            font=("Arial", 11, "bold"),
            bg="white"
        ).pack(side=tk.RIGHT)
        
        # Segunda fila: Concepto
        tk.Label(
            frame_contenido,
            text=f"Concepto: {pago.concepto.value}",
            font=("Arial", 10),
            bg="white",
            fg="#7f8c8d"
        ).pack(anchor=tk.W, pady=(5, 0))
        
        # Tercera fila: Notas (si hay)
        if pago.notas:
            tk.Label(
                frame_contenido,
                text=f"Notas: {pago.notas}",
                font=("Arial", 9),
                bg="white",
                fg="#95a5a6",
                wraplength=600,
                justify=tk.LEFT
            ).pack(anchor=tk.W, pady=(5, 0))
        
        # Botones de acción
        frame_botones = tk.Frame(frame_contenido, bg="white")
        frame_botones.pack(fill=tk.X, pady=(10, 0))
        
        tk.Button(
            frame_botones,
            text="🗑️ Eliminar",
            command=lambda p=pago: self.eliminar_pago(p),
            bg="#e74c3c",
            fg="white",
            font=("Arial", 9),
            padx=10,
            pady=3
        ).pack(side=tk.LEFT, padx=(0, 5))


# ===== PESTAÑA DE INFORMES =====
    
    def actualizar_tab_informes(self):
        """Actualiza la pestaña de informes del paciente"""
        # Limpiar pestaña
        for widget in self.tab_informes.winfo_children():
            widget.destroy()
        
        if self.paciente_actual is None:
            return
        
        # Frame superior con botón de nuevo informe
        frame_superior = tk.Frame(self.tab_informes, bg="white")
        frame_superior.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(
            frame_superior,
            text="Informes",
            font=("Arial", 16, "bold"),
            bg="white"
        ).pack(side=tk.LEFT)
        
        tk.Button(
            frame_superior,
            text="➕ Nuevo Informe",
            command=self.abrir_dialogo_nuevo_informe,
            bg="#27ae60",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=15,
            pady=5
        ).pack(side=tk.RIGHT)
        
        # Obtener informes del paciente
        informes = db.obtener_informes_paciente(self.paciente_actual.id)
        
        if not informes:
            tk.Label(
                self.tab_informes,
                text="No hay informes registrados",
                font=("Arial", 12),
                fg="#95a5a6",
                bg="white"
            ).pack(expand=True)
            return
        
        # Frame con scroll para la lista de informes
        frame_scroll = tk.Frame(self.tab_informes, bg="white")
        frame_scroll.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        canvas = tk.Canvas(frame_scroll, bg="white")
        scrollbar = tk.Scrollbar(frame_scroll, orient="vertical", command=canvas.yview)
        frame_informes = tk.Frame(canvas, bg="white")
        
        frame_informes.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=frame_informes, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Mostrar cada informe como una tarjeta
        for informe in informes:
            self.crear_tarjeta_informe(frame_informes, informe)
    def crear_tarjeta_informe(self, parent, informe: Informe):
        """Crea una tarjeta visual para un informe"""
        # Frame de la tarjeta
        color_borde = "#27ae60" if informe.estado_pago == EstadoPagoInforme.PAGADO else "#e74c3c"
        
        frame_tarjeta = tk.Frame(
            parent,
            bg="white",
            relief=tk.SOLID,
            borderwidth=2,
            highlightbackground=color_borde,
            highlightthickness=2
        )
        frame_tarjeta.pack(fill=tk.X, pady=5, padx=5)
        
        # Contenido de la tarjeta
        frame_contenido = tk.Frame(frame_tarjeta, bg="white")
        frame_contenido.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # Primera fila: Tipo y estado
        frame_fila1 = tk.Frame(frame_contenido, bg="white")
        frame_fila1.pack(fill=tk.X)
        
        tk.Label(
            frame_fila1,
            text=informe.tipo.value,
            font=("Arial", 12, "bold"),
            bg="white"
        ).pack(side=tk.LEFT)
        
        estado_texto = f"Estado: {informe.estado.value}"
        
        tk.Label(
            frame_fila1,
            text=estado_texto,
            font=("Arial", 10, "bold"),
            bg="white",
            fg="#7f8c8d"
        ).pack(side=tk.RIGHT)
        
        # Segunda fila: Precio y monto pagado
        frame_fila2 = tk.Frame(frame_contenido, bg="white")
        frame_fila2.pack(fill=tk.X, pady=5)
        
        tk.Label(
            frame_fila2,
            text=f"Precio: ${informe.precio:,.0f}",
            font=("Arial", 11),
            bg="white"
        ).pack(side=tk.LEFT)
        
        tk.Label(
            frame_fila2,
            text=f"Pagado: ${informe.monto_pagado:,.0f}",
            font=("Arial", 11),
            bg="white"
        ).pack(side=tk.RIGHT)
        
        # Tercera fila: Notas (si hay)
        if informe.notas:
            tk.Label(
                frame_contenido,
                text=f"Notas: {informe.notas}",
                font=("Arial", 9),
                bg="white",
                fg  ="#95a5a6",
                wraplength=600,
                justify=tk.LEFT
            ).pack(anchor=tk.W, pady=(5, 0))

        # Botones de acción
        frame_botones = tk.Frame(frame_contenido, bg="white")
        frame_botones.pack(fill=tk.X, pady=(10, 0))
        if informe.estado_pago != EstadoPagoInforme.PAGADO:
            tk.Button(
                frame_botones,
                text="✓ Marcar como Pagado",
                command=lambda i=informe: self.marcar_informe_pagado(i),
                bg="#27ae60",
                fg="white",
                font=("Arial", 9),
                padx=10,
                pady=3
            ).pack(side=tk.LEFT, padx=(0, 5))
        tk.Button(
            frame_botones,
            text="✏️ Editar",
            command=lambda i=informe: self.editar_informe(i),
            bg="#3498db",
            fg="white",
            font=("Arial", 9),
            padx=10,
            pady=3
        ).pack(side=tk.LEFT, padx=5)
        tk.Button(
            frame_botones,
            text="🗑️ Eliminar",
            command=lambda i=informe: self.eliminar_informe(i),
            bg="#e74c3c",
            fg="white",
            font=("Arial", 9),
            padx=10,
            pady=3
        ).pack(side=tk.LEFT, padx=5)
    def marcar_informe_pagado(self, informe: Informe):
        """Marca un informe como pagado manualmente"""
        respuesta = messagebox.askyesno(
            "Confirmar",
            f"¿Marcar este informe como pagado?\n\nTipo: {informe.tipo.value}\nPrecio: ${informe.precio:,.0f}"
        )
        
        if respuesta:
            informe.estado_pago = EstadoPagoInforme.PAGADO
            db.guardar_informe(informe)
            
            # Actualizar deuda del paciente
            db.actualizar_deuda_paciente(self.paciente_actual.id)
            
            # Recargar paciente y actualizar vista
            self.paciente_actual = db.obtener_paciente(self.paciente_actual.id)
            self.actualizar_pestañas()
            self.cargar_lista_pacientes()
    def eliminar_informe(self, informe: Informe):
        """Elimina un informe con confirmación"""
        respuesta = messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Estás seguro de eliminar este informe?\n\n"
            f"Tipo: {informe.tipo.value}\n"
            f"Precio: ${informe.precio:,.0f}"
        )
        
        if respuesta:
            db.eliminar_informe(informe.id)
            
            # Actualizar deuda del paciente
            db.actualizar_deuda_paciente(self.paciente_actual.id)
            
            # Recargar y actualizar
            self.paciente_actual = db.obtener_paciente(self.paciente_actual.id)
            self.actualizar_pestañas()
            self.cargar_lista_pacientes()
    def editar_informe(self, informe: Informe):
        """Edita un informe existente"""
        if self.paciente_actual is None:
            return
        
        # Crear ventana de diálogo
        dialogo = tk.Toplevel(self.root)
        dialogo.title("Editar Informe")
        dialogo.geometry("550x500")
        dialogo.resizable(False, False)
        
        # Centrar ventana
        dialogo.transient(self.root)
        dialogo.grab_set()
        
        # Título
        tk.Label(
            dialogo,
            text="Editar Informe",
            font=("Arial", 14, "bold")
        ).pack(pady=20)
        
        # Frame para campos
        frame_campos = tk.Frame(dialogo)
        frame_campos.pack(padx=30, pady=10, fill=tk.BOTH, expand=True)
        
        # Tipo de informe
        tk.Label(frame_campos, text="Tipo:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w", pady=10)
        combo_tipo = ttk.Combobox(frame_campos, width=40, state="readonly")
        combo_tipo['values'] = [tipo.value for tipo in TipoInforme]
        combo_tipo.set(informe.tipo.value)
        combo_tipo.grid(row=0, column=1, sticky="w", pady=10)
        
        # Estado del informe
        tk.Label(frame_campos, text="Estado:", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky="w", pady=10)
        combo_estado = ttk.Combobox(frame_campos, width=25, state="readonly")
        combo_estado['values'] = [estado.value for estado in EstadoInforme]
        combo_estado.set(informe.estado.value)
        combo_estado.grid(row=1, column=1, sticky="w", pady=10)
        
        # Precio
        tk.Label(frame_campos, text="Precio:", font=("Arial", 10, "bold")).grid(row=2, column=0, sticky="w", pady=10)
        entry_precio = tk.Entry(frame_campos, width=15, font=("Arial", 10))
        entry_precio.insert(0, str(int(informe.precio)))
        entry_precio.grid(row=2, column=1, sticky="w", pady=10)
        
        # Monto pagado
        tk.Label(frame_campos, text="Monto pagado:", font=("Arial", 10, "bold")).grid(row=3, column=0, sticky="w", pady=10)
        entry_pagado = tk.Entry(frame_campos, width=15, font=("Arial", 10))
        entry_pagado.insert(0, str(int(informe.monto_pagado)))
        entry_pagado.grid(row=3, column=1, sticky="w", pady=10)
        
        # Estado de pago
        tk.Label(frame_campos, text="Estado de pago:", font=("Arial", 10, "bold")).grid(row=4, column=0, sticky="w", pady=10)
        combo_estado_pago = ttk.Combobox(frame_campos, width=25, state="readonly")
        combo_estado_pago['values'] = [estado.value for estado in EstadoPagoInforme]
        combo_estado_pago.set(informe.estado_pago.value)
        combo_estado_pago.grid(row=4, column=1, sticky="w", pady=10)
        
        # Notas
        tk.Label(frame_campos, text="Notas:", font=("Arial", 10, "bold")).grid(row=5, column=0, sticky="nw", pady=10)
        text_notas = tk.Text(frame_campos, width=40, height=4, font=("Arial", 10))
        text_notas.insert("1.0", informe.notas if informe.notas else "")
        text_notas.grid(row=5, column=1, sticky="w", pady=10)
        
        # Botones
        frame_botones = tk.Frame(dialogo)
        frame_botones.pack(pady=20)
        
        def guardar_cambios():
            try:
                # Mapeo para tipos
                tipo_map = {
                    "Carta - Instituciones, psiquiatras, trabajo, etc.": TipoInforme.CARTA,
                    "Comprobante de tratamiento": TipoInforme.COMPROBANTE,
                    "Psicodiagnóstico": TipoInforme.PSICODIAGNOSTICO,
                    "Reunión (colegios, etc.)": TipoInforme.REUNION
                }
                
                estado_map = {
                    "Pendiente": EstadoInforme.PENDIENTE,
                    "Falta aplicar pruebas": EstadoInforme.FALTA_PRUEBAS,
                    "Terminado": EstadoInforme.TERMINADO,
                    "Entregado": EstadoInforme.ENTREGADO
                }
                
                estado_pago_map = {
                    "Pendiente": EstadoPagoInforme.PENDIENTE,
                    "Pago parcial": EstadoPagoInforme.PAGO_PARCIAL,
                    "Pagado": EstadoPagoInforme.PAGADO
                }
                
                # Actualizar informe
                informe.tipo = tipo_map[combo_tipo.get()]
                informe.estado = estado_map[combo_estado.get()]
                informe.precio = float(entry_precio.get())
                informe.monto_pagado = float(entry_pagado.get())
                informe.estado_pago = estado_pago_map[combo_estado_pago.get()]
                informe.notas = text_notas.get("1.0", tk.END).strip()
                
                # Guardar en BD
                db.guardar_informe(informe)
                
                # Actualizar deuda
                db.actualizar_deuda_paciente(self.paciente_actual.id)
                
                # Recargar y actualizar
                self.paciente_actual = db.obtener_paciente(self.paciente_actual.id)
                self.actualizar_pestañas()
                self.cargar_lista_pacientes()
                
                messagebox.showinfo("Éxito", "Informe actualizado correctamente")
                dialogo.destroy()
                
            except ValueError as e:
                messagebox.showerror("Error", f"Datos inválidos: {e}")
        
        tk.Button(
            frame_botones,
            text="✓ Guardar",
            command=guardar_cambios,
            bg="#27ae60",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=20,
            pady=5
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            frame_botones,
            text="✗ Cancelar",
            command=dialogo.destroy,
            bg="#95a5a6",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=20,
            pady=5
        ).pack(side=tk.LEFT, padx=5)
    
    def abrir_dialogo_nuevo_informe(self):
        """Abre un diálogo para crear un nuevo informe"""
        if self.paciente_actual is None:
            return
        
        # Crear ventana de diálogo
        dialogo = tk.Toplevel(self.root)
        dialogo.title("Nuevo Informe")
        dialogo.geometry("550x500")
        dialogo.resizable(False, False)
        
        # Centrar ventana
        dialogo.transient(self.root)
        dialogo.grab_set()
        
        # Título
        tk.Label(
            dialogo,
            text=f"Nuevo informe para {self.paciente_actual.nombre}",
            font=("Arial", 14, "bold")
        ).pack(pady=20)
        
        # Frame para campos
        frame_campos = tk.Frame(dialogo)
        frame_campos.pack(padx=30, pady=10, fill=tk.BOTH, expand=True)
        
        # Tipo de informe
        tk.Label(frame_campos, text="Tipo:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w", pady=10)
        combo_tipo = ttk.Combobox(frame_campos, width=40, state="readonly")
        combo_tipo['values'] = [tipo.value for tipo in TipoInforme]
        combo_tipo.current(0)
        combo_tipo.grid(row=0, column=1, sticky="w", pady=10)
        
        # Estado del informe
        tk.Label(frame_campos, text="Estado:", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky="w", pady=10)
        combo_estado = ttk.Combobox(frame_campos, width=25, state="readonly")
        combo_estado['values'] = [estado.value for estado in EstadoInforme]
        combo_estado.current(0)
        combo_estado.grid(row=1, column=1, sticky="w", pady=10)
        
        # Estado del pago del informe
        tk.Label(frame_campos, text="Estado del pago:", font=("Arial", 10, "bold")).grid(row=2, column=0, sticky="w", pady=10)
        combo_estado_pago = ttk.Combobox(frame_campos, width=25, state="readonly")
        combo_estado_pago['values'] = [estado.value for estado in EstadoPagoInforme]
        combo_estado_pago.current(0)
        combo_estado_pago.grid(row=2, column=1, sticky="w", pady=10)
        
        # Precio
        tk.Label(frame_campos, text="Precio:", font=("Arial", 10, "bold")).grid(row=3, column=0, sticky="w", pady=10)
        entry_precio = tk.Entry(frame_campos, width=15, font=("Arial", 10))
        entry_precio.insert(0, "0")
        entry_precio.grid(row=3, column=1, sticky="w", pady=10)
        
        # Monto pagado
        tk.Label(frame_campos, text="Monto pagado:", font=("Arial", 10, "bold")).grid(row=4, column=0, sticky="w", pady=10)
        entry_pagado = tk.Entry(frame_campos, width=15, font=("Arial", 10))
        entry_pagado.insert(0, "0")
        entry_pagado.grid(row=4, column=1, sticky="w", pady=10)
        
        # Notas
        tk.Label(frame_campos, text="Notas:", font=("Arial", 10, "bold")).grid(row=5, column=0, sticky="nw", pady=10)
        text_notas = tk.Text(frame_campos, width=40, height=4, font=("Arial", 10))
        text_notas.grid(row=5, column=1, sticky="w", pady=10)
        
        # Botones
        frame_botones = tk.Frame(dialogo)
        frame_botones.pack(pady=20)
        
        def guardar_informe():
            try:
                # Mapeo para tipos
                tipo_map = {
                    "Carta - Instituciones, psiquiatras, trabajo, etc.": TipoInforme.CARTA,
                    "Comprobante de tratamiento": TipoInforme.COMPROBANTE,
                    "Psicodiagnóstico": TipoInforme.PSICODIAGNOSTICO,
                    "Reunión (colegios, etc.)": TipoInforme.REUNION
                }
                
                estado_map = {
                    "Pendiente": EstadoInforme.PENDIENTE,
                    "Falta aplicar pruebas": EstadoInforme.FALTA_PRUEBAS,
                    "Terminado": EstadoInforme.TERMINADO,
                    "Entregado": EstadoInforme.ENTREGADO
                }
                
                estado_pago_map = {
                    "Pendiente": EstadoPagoInforme.PENDIENTE,
                    "Pago parcial": EstadoPagoInforme.PAGO_PARCIAL,
                    "Pagado": EstadoPagoInforme.PAGADO
                }
                
                # Crear informe
                informe = Informe(
                    id=None,
                    paciente_id=self.paciente_actual.id,
                    tipo=tipo_map[combo_tipo.get()],
                    estado=estado_map[combo_estado.get()],
                    estado_pago=estado_pago_map[combo_estado_pago.get()],
                    precio=float(entry_precio.get()),
                    monto_pagado=float(entry_pagado.get()),
                    notas=text_notas.get("1.0", tk.END).strip(),
                    fecha_creacion=datetime.now()
                )
                
                # Guardar en BD
                db.guardar_informe(informe)
                
                # Actualizar deuda
                db.actualizar_deuda_paciente(self.paciente_actual.id)
                
                # Recargar y actualizar
                self.paciente_actual = db.obtener_paciente(self.paciente_actual.id)
                self.actualizar_pestañas()
                self.cargar_lista_pacientes()
                
                messagebox.showinfo("Éxito", f"Informe creado correctamente")
                dialogo.destroy()
                
            except ValueError as e:
                messagebox.showerror("Error", f"Datos inválidos: {e}")
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar informe: {e}")
        
        tk.Button(
            frame_botones,
            text="✓ Guardar",
            command=guardar_informe,
            bg="#27ae60",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=20,
            pady=5
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            frame_botones,
            text="✗ Cancelar",
            command=dialogo.destroy,
            bg="#95a5a6",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=20,
            pady=5
        ).pack(side=tk.LEFT, padx=5)
    
    # ===== PESTAÑA DE RESUMEN/DEUDA =====
    
    def actualizar_tab_resumen(self):
        """Actualiza la pestaña de resumen/deuda del paciente"""
        # Limpiar pestaña
        for widget in self.tab_resumen.winfo_children():
            widget.destroy()
        
        if self.paciente_actual is None:
            return
        
        p = self.paciente_actual
        
        # Título
        tk.Label(
            self.tab_resumen,
            text="Resumen Financiero",
            font=("Arial", 18, "bold"),
            bg="white"
        ).pack(pady=20)
        
        # Marco principal
        frame_resumen = tk.Frame(self.tab_resumen, bg="white")
        frame_resumen.pack(pady=10, padx=30, fill=tk.BOTH, expand=True)
        
        # Deuda total
        deuda_color = "#e74c3c" if p.deuda > 0 else "#27ae60"
        deuda_texto = f"${p.deuda:,.0f}" if p.deuda >= 0 else f"-${abs(p.deuda):,.0f}"
        
        tk.Label(
            frame_resumen,
            text="Deuda Total",
            font=("Arial", 14, "bold"),
            bg="white"
        ).pack(pady=(20, 0))
        
        tk.Label(
            frame_resumen,
            text=deuda_texto,
            font=("Arial", 32, "bold"),
            bg="white",
            fg=deuda_color
        ).pack(pady=(0, 20))
        
        # Estadísticas
        sesiones_total = db.obtener_sesiones_paciente(p.id)
        sesiones_pagadas = [s for s in sesiones_total if s.estado == EstadoSesion.PAGA]
        sesiones_pendientes = [s for s in sesiones_total if s.estado == EstadoSesion.PENDIENTE]
        
        pagos_total = db.obtener_pagos_paciente(p.id)
        monto_pagado = sum(pago.monto for pago in pagos_total)
        
        estadisticas = [
            ("Total de sesiones:", len(sesiones_total)),
            ("Sesiones pagadas:", len(sesiones_pagadas)),
            ("Sesiones pendientes:", len(sesiones_pendientes)),
            ("Monto total pagado:", f"${monto_pagado:,.0f}"),
        ]
        
        for label, valor in estadisticas:
            tk.Label(
                frame_resumen,
                text=label,
                font=("Arial", 11, "bold"),
                bg="white"
            ).pack(pady=(10, 0), anchor="w")
            
            tk.Label(
                frame_resumen,
                text=str(valor),
                font=("Arial", 11),
                bg="white",
                fg="#7f8c8d"
            ).pack(anchor="w", padx=(20, 0))
    
    def abrir_dialogo_nuevo_pago(self):
        """Abre un diálogo para crear un nuevo pago"""
        if self.paciente_actual is None:
            return
        
        # Crear ventana de diálogo
        dialogo = tk.Toplevel(self.root)
        dialogo.title("Nuevo Pago")
        dialogo.geometry("500x450")
        dialogo.resizable(False, False)
        
        # Centrar ventana
        dialogo.transient(self.root)
        dialogo.grab_set()
        
        # Título
        tk.Label(
            dialogo,
            text=f"Nuevo pago para {self.paciente_actual.nombre}",
            font=("Arial", 14, "bold")
        ).pack(pady=20)
        
        # Frame para campos
        frame_campos = tk.Frame(dialogo)
        frame_campos.pack(padx=30, pady=10, fill=tk.BOTH, expand=True)
        
        # Fecha
        tk.Label(frame_campos, text="Fecha:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w", pady=10)
        frame_fecha = tk.Frame(frame_campos)
        frame_fecha.grid(row=0, column=1, sticky="w", pady=10)
        
        entry_dia = tk.Entry(frame_fecha, width=5, font=("Arial", 10))
        entry_dia.insert(0, datetime.now().strftime("%d"))
        entry_dia.pack(side=tk.LEFT)
        tk.Label(frame_fecha, text="/").pack(side=tk.LEFT)
        
        entry_mes = tk.Entry(frame_fecha, width=5, font=("Arial", 10))
        entry_mes.insert(0, datetime.now().strftime("%m"))
        entry_mes.pack(side=tk.LEFT)
        tk.Label(frame_fecha, text="/").pack(side=tk.LEFT)
        
        entry_año = tk.Entry(frame_fecha, width=8, font=("Arial", 10))
        entry_año.insert(0, datetime.now().strftime("%Y"))
        entry_año.pack(side=tk.LEFT)
        
        # Monto
        tk.Label(frame_campos, text="Monto:", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky="w", pady=10)
        entry_monto = tk.Entry(frame_campos, width=15, font=("Arial", 10))
        entry_monto.grid(row=1, column=1, sticky="w", pady=10)
        
        # Concepto
        tk.Label(frame_campos, text="Concepto:", font=("Arial", 10, "bold")).grid(row=2, column=0, sticky="w", pady=10)
        combo_concepto = ttk.Combobox(frame_campos, width=25, state="readonly")
        combo_concepto['values'] = [concepto.value for concepto in ConceptoPago]
        combo_concepto.current(0)
        combo_concepto.grid(row=2, column=1, sticky="w", pady=10)
        
        # Notas
        tk.Label(frame_campos, text="Notas:", font=("Arial", 10, "bold")).grid(row=3, column=0, sticky="nw", pady=10)
        text_notas = tk.Text(frame_campos, width=30, height=5, font=("Arial", 10))
        text_notas.grid(row=3, column=1, sticky="w", pady=10)
        
        # Botones
        frame_botones = tk.Frame(dialogo)
        frame_botones.pack(pady=20)
        
        def guardar_pago():
            try:
                # Validar y crear fecha
                dia = int(entry_dia.get())
                mes = int(entry_mes.get())
                año = int(entry_año.get())
                fecha = datetime(año, mes, dia)
                
                # Validar monto
                monto_str = entry_monto.get().strip()
                if not monto_str:
                    messagebox.showerror("Error", "El monto es obligatorio")
                    return
                
                monto = float(monto_str)
                
                if monto <= 0:
                    messagebox.showerror("Error", "El monto debe ser mayor a 0")
                    return
                
                # Mapeo para conceptos
                concepto_map = {
                    "Sesión": ConceptoPago.SESION,
                    "Mensual": ConceptoPago.MENSUAL,
                    "Diagnóstico": ConceptoPago.DIAGNOSTICO,
                    "Informe": ConceptoPago.INFORME
                }
                
                # Crear pago
                pago = Pago(
                    id=None,
                    paciente_id=self.paciente_actual.id,
                    fecha=fecha,
                    monto=monto,
                    concepto=concepto_map[combo_concepto.get()],
                    notas=text_notas.get("1.0", tk.END).strip()
                )
                
                # Guardar pago en BD
                db.guardar_pago(pago)
                
                # APLICAR EL PAGO AUTOMÁTICAMENTE
                resultado = db.aplicar_pago_automatico(self.paciente_actual.id, monto)
                
                # Construir mensaje de éxito con detalles
                mensaje_detalle = f"Pago de ${monto:,.2f} registrado y aplicado:\n\n"
                
                # Sesiones pagadas
                if resultado["sesiones_pagadas"]:
                    mensaje_detalle += f"✓ Sesiones pagadas: {len(resultado['sesiones_pagadas'])}\n"
                    for sesion in resultado["sesiones_pagadas"]:
                        mensaje_detalle += f"  • {sesion['tipo']} ({sesion['fecha']}) - ${sesion['precio']:,.2f}\n"
                    mensaje_detalle += "\n"
                
                # Informes actualizados
                if resultado["informes_actualizados"]:
                    mensaje_detalle += f"✓ Informes actualizados: {len(resultado['informes_actualizados'])}\n"
                    for informe in resultado["informes_actualizados"]:
                        mensaje_detalle += f"  • {informe['tipo']} - ${informe['monto_aplicado']:,.2f} ({informe['nuevo_estado']})\n"
                    mensaje_detalle += "\n"
                
                # Saldo a favor
                if resultado["saldo_a_favor"] > 0.01:
                    mensaje_detalle += f"✓ Saldo a favor: ${resultado['saldo_a_favor']:,.2f}\n\n"
                
                # Deuda actualizada
                deuda_anterior = resultado["deuda_anterior"]
                deuda_nueva = resultado["deuda_nueva"]
                mensaje_detalle += f"Deuda: ${deuda_anterior:,.2f} → ${deuda_nueva:,.2f}"
                
                messagebox.showinfo("Pago Registrado", mensaje_detalle)
                
                # Recargar y actualizar
                self.paciente_actual = db.obtener_paciente(self.paciente_actual.id)
                self.actualizar_pestañas()
                self.cargar_lista_pacientes()
                
                dialogo.destroy()
                
            except ValueError as e:
                messagebox.showerror("Error", f"Datos inválidos: {e}")
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar pago: {e}")
        
        tk.Button(
            frame_botones,
            text="✓ Guardar",
            command=guardar_pago,
            bg="#27ae60",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=20,
            pady=5
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            frame_botones,
            text="✗ Cancelar",
            command=dialogo.destroy,
            bg="#95a5a6",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=20,
            pady=5
        ).pack(side=tk.LEFT, padx=5)


def iniciar_aplicacion():
    """Función para iniciar la aplicación"""
    root = tk.Tk()
    app = AplicacionClinica(root)
    root.mainloop()


if __name__ == "__main__":
    iniciar_aplicacion()
