import sqlite3
from datetime import datetime
from typing import List, Optional
from pathlib import Path
import shutil

from src.models import (
    Paciente, Sesion, Pago, Informe,
    TipoPaciente, TipoSesion, EstadoSesion, ConceptoPago,
    TipoInforme, EstadoInforme, EstadoPagoInforme
)

# Ruta a la base de datos
DB_PATH = Path("data/clinica.db")
BACKUPS_PATH = Path("backups")


def crear_backup() -> str:
    """
    Crea un backup de la base de datos con timestamp.
    Retorna la ruta del archivo creado.
    """
    # Crear carpeta backups si no existe
    BACKUPS_PATH.mkdir(exist_ok=True)
    
    # Generar nombre con timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_name = f"clinica_backup_{timestamp}.db"
    backup_path = BACKUPS_PATH / backup_name
    
    # Copiar base de datos
    if DB_PATH.exists():
        shutil.copy2(DB_PATH, backup_path)
        return str(backup_path)
    else:
        raise FileNotFoundError("La base de datos no existe aún")


def obtener_lista_backups() -> List[dict]:
    """
    Obtiene lista de backups ordenados por fecha (más reciente primero).
    Retorna lista de dicts con: {'nombre': str, 'fecha': str, 'tamaño': str, 'ruta': str}
    """
    if not BACKUPS_PATH.exists():
        return []
    
    backups = []
    for archivo in BACKUPS_PATH.glob("clinica_backup_*.db"):
        stat = archivo.stat()
        # Extraer fecha del nombre: clinica_backup_2025-12-02_14-30-45.db
        fecha_str = archivo.stem.replace("clinica_backup_", "")
        # Convertir a formato legible: 2025-12-02 14:30:45
        fecha_legible = fecha_str.replace("_", " ").replace("-", "-", 2)  # Mantener primer - como separador de fecha
        fecha_legible = fecha_str[:10] + " " + fecha_str[11:].replace("-", ":")
        
        tamaño_mb = f"{stat.st_size / (1024*1024):.2f} MB"
        
        backups.append({
            'nombre': archivo.name,
            'fecha': fecha_legible,
            'tamaño': tamaño_mb,
            'ruta': str(archivo)
        })
    
    # Ordenar por fecha más reciente primero
    backups.sort(key=lambda x: x['nombre'], reverse=True)
    return backups


def restaurar_backup(ruta_backup: str) -> bool:
    """
    Restaura la base de datos desde un backup específico.
    Crea un backup de la versión actual antes de restaurar.
    Retorna True si tuvo éxito.
    """
    ruta_backup_path = Path(ruta_backup)
    
    if not ruta_backup_path.exists():
        raise FileNotFoundError(f"El backup no existe: {ruta_backup}")
    
    # Crear backup de la versión actual antes de restaurar
    if DB_PATH.exists():
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_actual = BACKUPS_PATH / f"clinica_backup_prerestauracion_{timestamp}.db"
        BACKUPS_PATH.mkdir(exist_ok=True)
        shutil.copy2(DB_PATH, backup_actual)
    
    # Restaurar el backup deseado
    shutil.copy2(ruta_backup_path, DB_PATH)
    return True


def limpiar_backups_antiguos(dias: int = 30, cantidad_minima: int = 5):
    """
    Elimina backups más antiguos que 'dias' días, pero mantiene al menos 'cantidad_minima'.
    """
    if not BACKUPS_PATH.exists():
        return
    
    backups = obtener_lista_backups()
    
    # Siempre mantener al menos la cantidad mínima
    if len(backups) <= cantidad_minima:
        return
    
    from datetime import timedelta
    fecha_limite = datetime.now() - timedelta(days=dias)
    
    for backup in backups[cantidad_minima:]:  # Saltar los primeros (más recientes)
        ruta = Path(backup['ruta'])
        fecha_backup = datetime.fromtimestamp(ruta.stat().st_mtime)
        
        if fecha_backup < fecha_limite:
            try:
                ruta.unlink()
            except Exception as e:
                print(f"Error al eliminar backup {ruta.name}: {e}")


def inicializar_base_datos():
    """Crea las tablas si no existen"""
    # Asegurarse de que existe la carpeta data
    DB_PATH.parent.mkdir(exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tabla pacientes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pacientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            tipo TEXT NOT NULL,
            costo_sesion REAL NOT NULL,
            deuda REAL NOT NULL,
            arancel_social INTEGER NOT NULL,
            notas TEXT,
            fecha_creacion TEXT NOT NULL
        )
    """)
    
    # Tabla sesiones
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sesiones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paciente_id INTEGER NOT NULL,
            fecha TEXT NOT NULL,
            precio REAL NOT NULL,
            estado TEXT NOT NULL,
            tipo TEXT NOT NULL,
            notas TEXT,
            FOREIGN KEY (paciente_id) REFERENCES pacientes(id)
        )
    """)
    
    # Tabla pagos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pagos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paciente_id INTEGER NOT NULL,
            fecha TEXT NOT NULL,
            monto REAL NOT NULL,
            concepto TEXT NOT NULL,
            notas TEXT,
            FOREIGN KEY (paciente_id) REFERENCES pacientes(id)
        )
    """)
    
    # Tabla informes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS informes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paciente_id INTEGER NOT NULL,
            tipo TEXT NOT NULL,
            estado TEXT NOT NULL,
            estado_pago TEXT NOT NULL,
            precio REAL NOT NULL,
            monto_pagado REAL NOT NULL,
            notas TEXT,
            fecha_creacion TEXT NOT NULL,
            FOREIGN KEY (paciente_id) REFERENCES pacientes(id)
        )
    """)
    
    conn.commit()
    conn.close()


# ========== FUNCIONES PARA PACIENTES ==========

def guardar_paciente(paciente: Paciente) -> int:
    """Guarda un paciente nuevo o actualiza uno existente. Retorna el ID."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if paciente.id is None:
        # Insertar nuevo
        cursor.execute("""
            INSERT INTO pacientes (nombre, tipo, costo_sesion, deuda, arancel_social, notas, fecha_creacion)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            paciente.nombre,
            paciente.tipo.name,  # Guarda el nombre del enum (ej: "ESTANDAR")
            paciente.costo_sesion,
            paciente.deuda,
            1 if paciente.arancel_social else 0,  # SQLite no tiene boolean
            paciente.notas,
            paciente.fecha_creacion.isoformat()
        ))
        paciente.id = cursor.lastrowid
        paciente_id = paciente.id
    else:
        # Actualizar existente
        cursor.execute("""
            UPDATE pacientes 
            SET nombre=?, tipo=?, costo_sesion=?, deuda=?, arancel_social=?, notas=?
            WHERE id=?
        """, (
            paciente.nombre,
            paciente.tipo.name,
            paciente.costo_sesion,
            paciente.deuda,
            1 if paciente.arancel_social else 0,
            paciente.notas,
            paciente.id
        ))
        paciente_id = paciente.id
    
    conn.commit()
    conn.close()
    return paciente_id


def obtener_todos_pacientes() -> List[Paciente]:
    """Obtiene todos los pacientes"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM pacientes ORDER BY nombre")
    rows = cursor.fetchall()
    conn.close()
    
    pacientes = []
    for row in rows:
        pacientes.append(Paciente(
            id=row[0],
            nombre=row[1],
            tipo=TipoPaciente[row[2]],  # Convierte string a enum
            costo_sesion=row[3],
            deuda=row[4],
            arancel_social=bool(row[5]),
            notas=row[6],
            fecha_creacion=datetime.fromisoformat(row[7])
        ))
    
    return pacientes


def obtener_paciente(paciente_id: int) -> Optional[Paciente]:
    """Obtiene un paciente por ID"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM pacientes WHERE id=?", (paciente_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row is None:
        return None
    
    return Paciente(
        id=row[0],
        nombre=row[1],
        tipo=TipoPaciente[row[2]],
        costo_sesion=row[3],
        deuda=row[4],
        arancel_social=bool(row[5]),
        notas=row[6],
        fecha_creacion=datetime.fromisoformat(row[7])
    )


# ========== FUNCIONES PARA SESIONES ==========

def guardar_sesion(sesion: Sesion) -> int:
    """Guarda una sesión nueva o actualiza una existente"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if sesion.id is None:
        cursor.execute("""
            INSERT INTO sesiones (paciente_id, fecha, precio, estado, tipo, notas)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            sesion.paciente_id,
            sesion.fecha.isoformat(),
            sesion.precio,
            sesion.estado.name,
            sesion.tipo.name,
            sesion.notas
        ))
        sesion.id = cursor.lastrowid
        sesion_id = sesion.id
    else:
        cursor.execute("""
            UPDATE sesiones 
            SET paciente_id=?, fecha=?, precio=?, estado=?, tipo=?, notas=?
            WHERE id=?
        """, (
            sesion.paciente_id,
            sesion.fecha.isoformat(),
            sesion.precio,
            sesion.estado.name,
            sesion.tipo.name,
            sesion.notas,
            sesion.id
        ))
        sesion_id = sesion.id
    
    conn.commit()
    conn.close()
    
    return sesion_id

def obtener_sesiones_paciente(paciente_id: int) -> List[Sesion]:
    """Obtiene todas las sesiones de un paciente"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM sesiones 
        WHERE paciente_id=? 
        ORDER BY fecha DESC
    """, (paciente_id,))
    rows = cursor.fetchall()
    conn.close()
    
    sesiones = []
    for row in rows:
        sesiones.append(Sesion(
            id=row[0],
            paciente_id=row[1],
            fecha=datetime.fromisoformat(row[2]),
            precio=row[3],
            estado=EstadoSesion[row[4]],
            tipo=TipoSesion[row[5]],
            notas=row[6]
        ))
    
    return sesiones


# ========== FUNCIONES PARA PAGOS ==========

def guardar_pago(pago: Pago) -> int:
    """Guarda un pago nuevo"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO pagos (paciente_id, fecha, monto, concepto, notas)
        VALUES (?, ?, ?, ?, ?)
    """, (
        pago.paciente_id,
        pago.fecha.isoformat(),
        pago.monto,
        pago.concepto.name,
        pago.notas
    ))
    pago_id = cursor.lastrowid
    
    conn.commit()
    conn.close()
    return pago_id


def obtener_pagos_paciente(paciente_id: int) -> List[Pago]:
    """Obtiene todos los pagos de un paciente"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM pagos 
        WHERE paciente_id=? 
        ORDER BY fecha DESC
    """, (paciente_id,))
    rows = cursor.fetchall()
    conn.close()
    
    pagos = []
    for row in rows:
        pagos.append(Pago(
            id=row[0],
            paciente_id=row[1],
            fecha=datetime.fromisoformat(row[2]),
            monto=row[3],
            concepto=ConceptoPago[row[4]],
            notas=row[5]
        ))
    
    return pagos


# ========== FUNCIONES PARA INFORMES ==========

def guardar_informe(informe: Informe) -> int:
    """Guarda un informe nuevo o actualiza uno existente"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if informe.id is None:
        cursor.execute("""
            INSERT INTO informes (paciente_id, tipo, estado, estado_pago, precio, monto_pagado, notas, fecha_creacion)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            informe.paciente_id,
            informe.tipo.name,
            informe.estado.name,
            informe.estado_pago.name,
            informe.precio,
            informe.monto_pagado,
            informe.notas,
            informe.fecha_creacion.isoformat()
        ))
        informe.id = cursor.lastrowid
        informe_id = informe.id
    else:
        cursor.execute("""
            UPDATE informes 
            SET tipo=?, estado=?, estado_pago=?, precio=?, monto_pagado=?, notas=?
            WHERE id=?
        """, (
            informe.tipo.name,
            informe.estado.name,
            informe.estado_pago.name,
            informe.precio,
            informe.monto_pagado,
            informe.notas,
            informe.id
        ))
        informe_id = informe.id
    
    conn.commit()
    conn.close()
    return informe_id


def obtener_informes_paciente(paciente_id: int) -> List[Informe]:
    """Obtiene todos los informes de un paciente"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM informes 
        WHERE paciente_id=? 
        ORDER BY fecha_creacion DESC
    """, (paciente_id,))
    rows = cursor.fetchall()
    conn.close()
    
    informes = []
    for row in rows:
        informes.append(Informe(
            id=row[0],
            paciente_id=row[1],
            tipo=TipoInforme[row[2]],
            estado=EstadoInforme[row[3]],
            estado_pago=EstadoPagoInforme[row[4]],
            precio=row[5],
            monto_pagado=row[6],
            notas=row[7],
            fecha_creacion=datetime.fromisoformat(row[8])
        ))
    
    return informes


# ========== LÓGICA DE APLICACIÓN DE PAGOS ==========

def aplicar_pago_automatico(paciente_id: int, monto: float) -> dict:
    """
    Aplica un pago automáticamente siguiendo esta prioridad:
    1. Sesiones pendientes (más antiguas primero)
    2. Informes pendientes con pago faltante
    3. Saldo a favor (deuda negativa)
    
    Retorna un diccionario con los detalles de qué se pagó
    """
    monto_restante = monto
    aplicaciones = {
        "sesiones_pagadas": [],
        "informes_actualizados": [],
        "saldo_a_favor": 0
    }
    
    # PASO 1: Aplicar a sesiones pendientes (más antiguas primero)
    sesiones = obtener_sesiones_paciente(paciente_id)
    sesiones_pendientes = [s for s in sesiones if s.estado == EstadoSesion.PENDIENTE]
    sesiones_pendientes.sort(key=lambda s: s.fecha)  # Más antiguas primero
    
    for sesion in sesiones_pendientes:
        if monto_restante <= 0.01:  # Permitir pequeños errores de redondeo
            break
        
        if monto_restante >= sesion.precio - 0.01:
            # Paga la sesión completa
            sesion.estado = EstadoSesion.PAGA
            guardar_sesion(sesion)
            aplicaciones["sesiones_pagadas"].append({
                "id": sesion.id,
                "tipo": sesion.tipo.value,
                "fecha": sesion.fecha.strftime("%d/%m/%Y"),
                "precio": sesion.precio
            })
            monto_restante -= sesion.precio
        else:
            # No alcanza para esta sesión
            break
    
    # PASO 2: Aplicar a informes pendientes
    if monto_restante > 0.01:
        informes = obtener_informes_paciente(paciente_id)
        informes_pendientes = [
            i for i in informes 
            if i.estado_pago != EstadoPagoInforme.PAGADO
        ]
        # Ordenar por fecha de creación (más antiguos primero)
        informes_pendientes.sort(key=lambda i: i.fecha_creacion)
        
        for informe in informes_pendientes:
            if monto_restante <= 0.01:
                break
            
            deuda_informe = informe.precio - informe.monto_pagado
            
            if monto_restante >= deuda_informe - 0.01:
                # Paga el informe completo
                informe.monto_pagado = informe.precio
                informe.estado_pago = EstadoPagoInforme.PAGADO
                monto_restante -= deuda_informe
                aplicaciones["informes_actualizados"].append({
                    "id": informe.id,
                    "tipo": informe.tipo.value,
                    "monto_aplicado": deuda_informe,
                    "nuevo_estado": EstadoPagoInforme.PAGADO.value
                })
            else:
                # Pago parcial
                informe.monto_pagado += monto_restante
                informe.estado_pago = EstadoPagoInforme.PAGO_PARCIAL
                aplicaciones["informes_actualizados"].append({
                    "id": informe.id,
                    "tipo": informe.tipo.value,
                    "monto_aplicado": monto_restante,
                    "nuevo_estado": EstadoPagoInforme.PAGO_PARCIAL.value
                })
                monto_restante = 0
            
            guardar_informe(informe)
    
    # PASO 3: Si sobra dinero, queda como saldo a favor (deuda negativa)
    if monto_restante > 0.01:
        aplicaciones["saldo_a_favor"] = round(monto_restante, 2)
    
    # Actualizar deuda del paciente
    paciente = obtener_paciente(paciente_id)
    deuda_anterior = paciente.deuda
    
    # Recalcular deuda desde cero basada en sesiones e informes pendientes
    deuda_sesiones = sum(s.precio for s in obtener_sesiones_paciente(paciente_id) 
                         if s.estado == EstadoSesion.PENDIENTE)
    deuda_informes = sum(i.precio - i.monto_pagado 
                         for i in obtener_informes_paciente(paciente_id) 
                         if i.estado_pago != EstadoPagoInforme.PAGADO)
    
    deuda_total = deuda_sesiones + deuda_informes
    
    # Si hay saldo a favor (monto_restante), restar de la deuda (quedará negativa)
    if monto_restante > 0.01:
        deuda_total -= monto_restante
    
    paciente.deuda = deuda_total
    guardar_paciente(paciente)
    
    aplicaciones["deuda_anterior"] = deuda_anterior
    aplicaciones["deuda_nueva"] = paciente.deuda
    
    return aplicaciones


def actualizar_deuda_paciente(paciente_id: int):
    """
    Recalcula la deuda total del paciente basándose en sesiones e informes pendientes
    """
    sesiones = obtener_sesiones_paciente(paciente_id)
    informes = obtener_informes_paciente(paciente_id)
    
    deuda_sesiones = sum(s.precio for s in sesiones if s.estado == EstadoSesion.PENDIENTE)
    deuda_informes = sum(i.precio - i.monto_pagado for i in informes if i.estado_pago != EstadoPagoInforme.PAGADO)
    
    paciente = obtener_paciente(paciente_id)
    paciente.deuda = deuda_sesiones + deuda_informes
    guardar_paciente(paciente)


def aplicar_saldo_a_favor_a_nueva_sesion(paciente_id: int, sesion: Sesion):
    """
    Si el paciente tiene saldo a favor (deuda negativa), aplica automáticamente
    a la nueva sesión. Si el saldo cubre toda la sesión, la marca como PAGA.
    """
    paciente = obtener_paciente(paciente_id)
    
    # Si no hay saldo a favor, no hacer nada
    if paciente.deuda >= 0:
        return
    
    saldo_a_favor = abs(paciente.deuda)
    
    # Si el saldo a favor cubre toda la sesión
    if saldo_a_favor >= sesion.precio:
        # Marcar sesión como PAGA y ajustar deuda
        sesion.estado = EstadoSesion.PAGA
        guardar_sesion(sesion)
        
        # Actualizar deuda: restar el precio de la sesión del saldo a favor
        paciente.deuda = -(saldo_a_favor - sesion.precio)
        guardar_paciente(paciente)
    # Si el saldo a favor cubre parcialmente
    elif saldo_a_favor > 0:
        # La sesión queda como PENDIENTE pero la deuda se ajusta
        # La parte del saldo se aplica, el resto queda pendiente
        paciente.deuda = saldo_a_favor - sesion.precio
        guardar_paciente(paciente)


def obtener_estadisticas_mensuales(mes: int = None, año: int = None) -> dict:
    """
    Obtiene estadísticas de facturación de un mes específico.
    Si no se especifica mes/año, usa el mes actual.
    Retorna un diccionario con:
    - total_cobrado: dinero total cobrado en el mes
    - desglose_cobrado: desglose por tipo de paciente
    - informes_total: monto total de informes cobrables
    - deuda_total: deuda total acumulada
    - deuda_por_tipo: desglose de deuda por tipo de paciente
    """
    from datetime import datetime as dt
    
    ahora = dt.now()
    mes_actual = mes if mes is not None else ahora.month
    año_actual = año if año is not None else ahora.year
    
    stats = {
        "total_cobrado": 0,
        "cobrado_estandar": 0,
        "cobrado_mensual": 0,
        "cobrado_diagnostico": 0,
        "informes_total": 0,
        "deuda_total": 0,
        "deuda_estandar": 0,
        "deuda_mensual": 0,
        "deuda_diagnostico": 0,
        "detalle_pacientes": []
    }
    
    pacientes = obtener_todos_pacientes()
    
    for paciente in pacientes:
        sesiones = obtener_sesiones_paciente(paciente.id)
        pagos = obtener_pagos_paciente(paciente.id)
        informes = obtener_informes_paciente(paciente.id)
        
        # Pagos del mes actual
        pagos_mes = [p for p in pagos 
                     if p.fecha.month == mes_actual and p.fecha.year == año_actual]
        
        monto_pagado_mes = sum(p.monto for p in pagos_mes)
        
        # Desglose por tipo
        if monto_pagado_mes > 0:
            stats["total_cobrado"] += monto_pagado_mes
            if paciente.tipo == TipoPaciente.ESTANDAR:
                stats["cobrado_estandar"] += monto_pagado_mes
            elif paciente.tipo == TipoPaciente.MENSUAL:
                stats["cobrado_mensual"] += monto_pagado_mes
            elif paciente.tipo == TipoPaciente.DIAGNOSTICO:
                stats["cobrado_diagnostico"] += monto_pagado_mes
        
        # Informes pendientes de cobro
        informes_no_pagados = [i for i in informes 
                               if i.estado_pago != EstadoPagoInforme.PAGADO]
        deuda_informes = sum(i.precio - i.monto_pagado for i in informes_no_pagados)
        stats["informes_total"] += deuda_informes
        
        # Deuda del paciente
        deuda_paciente = sum(s.precio for s in sesiones if s.estado == EstadoSesion.PENDIENTE)
        deuda_paciente += deuda_informes
        
        stats["deuda_total"] += deuda_paciente
        
        if paciente.tipo == TipoPaciente.ESTANDAR:
            stats["deuda_estandar"] += deuda_paciente
        elif paciente.tipo == TipoPaciente.MENSUAL:
            stats["deuda_mensual"] += deuda_paciente
        elif paciente.tipo == TipoPaciente.DIAGNOSTICO:
            stats["deuda_diagnostico"] += deuda_paciente
        
        # Agregar a detalle si hay información relevante
        if monto_pagado_mes > 0 or deuda_paciente > 0:
            stats["detalle_pacientes"].append({
                "nombre": paciente.nombre,
                "tipo": paciente.tipo.value,
                "cobrado": monto_pagado_mes,
                "deuda": deuda_paciente,
                "arancel_social": paciente.arancel_social
            })
    
    return stats


# ========== FUNCIONES PARA ELIMINAR ==========

def eliminar_paciente(paciente_id: int):
    """
    Elimina un paciente y TODOS sus registros asociados (sesiones, pagos, informes)
    CUIDADO: Esta operación no se puede deshacer
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Eliminar todos los registros asociados primero
    cursor.execute("DELETE FROM sesiones WHERE paciente_id=?", (paciente_id,))
    cursor.execute("DELETE FROM pagos WHERE paciente_id=?", (paciente_id,))
    cursor.execute("DELETE FROM informes WHERE paciente_id=?", (paciente_id,))
    
    # Eliminar el paciente
    cursor.execute("DELETE FROM pacientes WHERE id=?", (paciente_id,))
    
    conn.commit()
    conn.close()


def eliminar_sesion(sesion_id: int):
    """Elimina una sesión específica"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM sesiones WHERE id=?", (sesion_id,))
    
    conn.commit()
    conn.close()


def eliminar_pago(pago_id: int):
    """Elimina un pago específico"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM pagos WHERE id=?", (pago_id,))
    
    conn.commit()
    conn.close()


def eliminar_informe(informe_id: int):
    """Elimina un informe específico"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM informes WHERE id=?", (informe_id,))
    
    conn.commit()
    conn.close()


def exportar_reporte_pdf(stats: dict, mes: int, año: int, ruta_archivo: str):
    """
    Exporta el reporte mensual a un archivo PDF.
    
    Parámetros:
    - stats: diccionario de estadísticas (retornado por obtener_estadisticas_mensuales)
    - mes: número del mes (1-12)
    - año: año del reporte
    - ruta_archivo: ruta donde guardar el PDF
    """
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib import colors
    from datetime import datetime as dt
    
    # Crear documento
    doc = SimpleDocTemplate(ruta_archivo, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []
    styles = getSampleStyleSheet()
    
    # Estilo personalizado para título
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=30,
        alignment=1  # Centro
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=13,
        textColor=colors.HexColor('#27ae60'),
        spaceBefore=12,
        spaceAfter=6
    )
    
    # Título
    mes_nombre = dt(año, mes, 1).strftime("%B %Y")
    elements.append(Paragraph(f"Reporte Mensual - {mes_nombre}", title_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # SECCIÓN 1: INGRESOS
    elements.append(Paragraph("💰 INGRESOS DEL MES", heading_style))
    
    ingresos_data = [
        ["Concepto", "Monto"],
        ["Total cobrado", f"${stats['total_cobrado']:,.2f}"],
        ["  • Pacientes Estándar", f"${stats['cobrado_estandar']:,.2f}"],
        ["  • Pacientes Mensuales", f"${stats['cobrado_mensual']:,.2f}"],
        ["  • Diagnósticos", f"${stats['cobrado_diagnostico']:,.2f}"],
        ["Informes (por cobrar)", f"${stats['informes_total']:,.2f}"],
    ]
    
    ingresos_table = Table(ingresos_data, colWidths=[4*inch, 2*inch])
    ingresos_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27ae60')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#d5f4e6')),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 2), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')]),
    ]))
    elements.append(ingresos_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # SECCIÓN 2: DEUDA
    elements.append(Paragraph("📊 DEUDA ACUMULADA", heading_style))
    
    deuda_data = [
        ["Concepto", "Monto"],
        ["Total deuda", f"${stats['deuda_total']:,.2f}"],
        ["  • Pacientes Estándar", f"${stats['deuda_estandar']:,.2f}"],
        ["  • Pacientes Mensuales", f"${stats['deuda_mensual']:,.2f}"],
        ["  • Diagnósticos", f"${stats['deuda_diagnostico']:,.2f}"],
    ]
    
    deuda_table = Table(deuda_data, colWidths=[4*inch, 2*inch])
    deuda_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#fadbd8')),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 2), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')]),
    ]))
    elements.append(deuda_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # SECCIÓN 3: DETALLE POR PACIENTE
    if stats["detalle_pacientes"]:
        elements.append(Paragraph("👥 RESUMEN POR PACIENTE", heading_style))
        
        detalle_data = [
            ["Paciente", "Tipo", "Cobrado", "Deuda"],
        ]
        
        for pac in stats["detalle_pacientes"]:
            detalle_data.append([
                pac["nombre"],
                pac["tipo"],
                f"${pac['cobrado']:,.2f}",
                f"${pac['deuda']:,.2f}"
            ])
        
        detalle_table = Table(detalle_data, colWidths=[2.5*inch, 1.5*inch, 1.2*inch, 1.2*inch])
        detalle_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')]),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        elements.append(detalle_table)
    
    # Construir PDF
    doc.build(elements)


# ===== FUNCIONES DE EXPORTACIÓN A CSV =====

def exportar_pacientes_csv(ruta_archivo: str):
    """
    Exporta la lista de pacientes a CSV con información resumida.
    Incluye: Nombre, Tipo, Costo Sesión, Deuda Actual, Arancel Social, Notas
    """
    import csv
    
    pacientes = obtener_todos_pacientes()
    
    with open(ruta_archivo, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Nombre', 'Tipo', 'Costo Sesión', 'Deuda Actual', 'Arancel Social', 'Notas']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for pac in pacientes:
            writer.writerow({
                'Nombre': pac.nombre,
                'Tipo': pac.tipo.value,
                'Costo Sesión': f"${pac.costo_sesion:,.2f}",
                'Deuda Actual': f"${pac.deuda:,.2f}",
                'Arancel Social': 'Sí' if pac.arancel_social else 'No',
                'Notas': pac.notas
            })


def exportar_sesiones_csv(ruta_archivo: str):
    """
    Exporta todas las sesiones a CSV.
    Incluye: Paciente, Fecha, Tipo, Precio, Estado, Notas
    """
    import csv
    
    pacientes = obtener_todos_pacientes()
    
    with open(ruta_archivo, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Paciente', 'Fecha', 'Tipo', 'Precio', 'Estado', 'Notas']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for pac in pacientes:
            sesiones = obtener_sesiones_paciente(pac.id)
            for sesion in sesiones:
                writer.writerow({
                    'Paciente': pac.nombre,
                    'Fecha': sesion.fecha.strftime("%d/%m/%Y"),
                    'Tipo': sesion.tipo.value,
                    'Precio': f"${sesion.precio:,.2f}",
                    'Estado': sesion.estado.value,
                    'Notas': sesion.notas
                })


def exportar_pagos_csv(ruta_archivo: str):
    """
    Exporta todos los pagos a CSV.
    Incluye: Paciente, Fecha, Monto, Concepto, Notas
    """
    import csv
    
    pacientes = obtener_todos_pacientes()
    
    with open(ruta_archivo, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Paciente', 'Fecha', 'Monto', 'Concepto', 'Notas']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for pac in pacientes:
            pagos = obtener_pagos_paciente(pac.id)
            for pago in pagos:
                writer.writerow({
                    'Paciente': pac.nombre,
                    'Fecha': pago.fecha.strftime("%d/%m/%Y"),
                    'Monto': f"${pago.monto:,.2f}",
                    'Concepto': pago.concepto.value,
                    'Notas': pago.notas
                })


def exportar_informes_csv(ruta_archivo: str):
    """
    Exporta todos los informes a CSV.
    Incluye: Paciente, Tipo, Estado, Precio, Monto Pagado, Estado de Pago, Notas
    """
    import csv
    
    pacientes = obtener_todos_pacientes()
    
    with open(ruta_archivo, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Paciente', 'Tipo', 'Estado', 'Precio', 'Monto Pagado', 'Estado Pago', 'Notas']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for pac in pacientes:
            informes = obtener_informes_paciente(pac.id)
            for informe in informes:
                writer.writerow({
                    'Paciente': pac.nombre,
                    'Tipo': informe.tipo.value,
                    'Estado': informe.estado.value,
                    'Precio': f"${informe.precio:,.2f}",
                    'Monto Pagado': f"${informe.monto_pagado:,.2f}",
                    'Estado Pago': informe.estado_pago.value,
                    'Notas': informe.notas
                })


def exportar_resumen_csv(ruta_archivo: str):
    """
    Exporta un resumen general con estadísticas.
    """
    import csv
    from datetime import datetime as dt
    
    pacientes = obtener_todos_pacientes()
    
    total_deuda = sum(p.deuda for p in pacientes if p.deuda > 0)
    total_saldo_favor = sum(abs(p.deuda) for p in pacientes if p.deuda < 0)
    
    # Contar entidades
    total_sesiones = sum(len(obtener_sesiones_paciente(p.id)) for p in pacientes)
    total_pagos = sum(len(obtener_pagos_paciente(p.id)) for p in pacientes)
    total_informes = sum(len(obtener_informes_paciente(p.id)) for p in pacientes)
    
    with open(ruta_archivo, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Métrica', 'Valor']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        writer.writerow({'Métrica': 'Fecha de Exportación', 'Valor': dt.now().strftime("%d/%m/%Y %H:%M:%S")})
        writer.writerow({'Métrica': '', 'Valor': ''})
        writer.writerow({'Métrica': 'Total Pacientes', 'Valor': len(pacientes)})
        writer.writerow({'Métrica': 'Total Sesiones', 'Valor': total_sesiones})
        writer.writerow({'Métrica': 'Total Pagos', 'Valor': total_pagos})
        writer.writerow({'Métrica': 'Total Informes', 'Valor': total_informes})
        writer.writerow({'Métrica': '', 'Valor': ''})
        writer.writerow({'Métrica': 'Deuda Total (owed)', 'Valor': f"${total_deuda:,.2f}"})
        writer.writerow({'Métrica': 'Saldo a Favor (prepaid)', 'Valor': f"${total_saldo_favor:,.2f}"})
        writer.writerow({'Métrica': '', 'Valor': ''})
        
        # Por tipo de paciente
        for tipo in TipoPaciente:
            pacientes_tipo = [p for p in pacientes if p.tipo == tipo]
            if pacientes_tipo:
                deuda_tipo = sum(p.deuda for p in pacientes_tipo if p.deuda > 0)
                writer.writerow({'Métrica': f'Deuda - {tipo.value}', 'Valor': f"${deuda_tipo:,.2f}"})


def exportar_todo(directorio: str) -> dict:
    """
    Exporta todos los datos en múltiples archivos CSV.
    Retorna un diccionario con las rutas de los archivos creados.
    """
    from pathlib import Path
    
    ruta_dir = Path(directorio)
    ruta_dir.mkdir(parents=True, exist_ok=True)
    
    archivos = {}
    
    # Exportar cada tipo de datos
    archivos['pacientes'] = str(ruta_dir / 'pacientes.csv')
    exportar_pacientes_csv(archivos['pacientes'])
    
    archivos['sesiones'] = str(ruta_dir / 'sesiones.csv')
    exportar_sesiones_csv(archivos['sesiones'])
    
    archivos['pagos'] = str(ruta_dir / 'pagos.csv')
    exportar_pagos_csv(archivos['pagos'])
    
    archivos['informes'] = str(ruta_dir / 'informes.csv')
    exportar_informes_csv(archivos['informes'])
    
    archivos['resumen'] = str(ruta_dir / 'resumen.csv')
    exportar_resumen_csv(archivos['resumen'])
    
    return archivos