import sqlite3
from datetime import datetime
from typing import List, Optional
from pathlib import Path

from models import (
    Paciente, Sesion, Pago, Informe,
    TipoPaciente, TipoSesion, EstadoSesion, ConceptoPago,
    TipoInforme, EstadoInforme, EstadoPagoInforme
)

# Ruta a la base de datos
DB_PATH = Path("data/clinica.db")


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
        paciente_id = cursor.lastrowid
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
        sesion_id = cursor.lastrowid
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


def editar_pago(pago: Pago):
    """Edita un pago existente"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE pagos 
        SET fecha=?, monto=?, concepto=?, notas=?
        WHERE id=?
    """, (
        pago.fecha.isoformat(),
        pago.monto,
        pago.concepto.name,
        pago.notas,
        pago.id
    ))
    
    conn.commit()
    conn.close()


def eliminar_pago(pago_id: int):
    """Elimina un pago"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM pagos WHERE id=?", (pago_id,))
    
    conn.commit()
    conn.close()


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
        informe_id = cursor.lastrowid
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


def actualizar_deuda_paciente(paciente_id: int):
    """
    Recalcula la deuda del paciente distribuyendo pagos según prioridad.
    
    Algoritmo:
    1. Construir lista de ítems pendientes (sesiones + informes)
    2. Sumar todos los pagos del paciente
    3. Calcular qué se paga sin modificar estados
    4. Actualizar estados en BD
    5. Calcular deuda final = suma de lo que quedó pendiente
    """
    sesiones = obtener_sesiones_paciente(paciente_id)
    informes = obtener_informes_paciente(paciente_id)
    pagos = obtener_pagos_paciente(paciente_id)
    
    # Obtener saldo total disponible para pagar
    saldo_pagador = sum(p.monto for p in pagos)
    
    # PASO 1: Construir lista de ítems pendientes en orden de prioridad
    # (sin modificar nada en la BD todavía)
    items_pendientes = []
    
    # Agregar sesiones pendientes (más antiguas primero)
    sesiones_pendientes = [s for s in sesiones if s.estado == EstadoSesion.PENDIENTE]
    sesiones_pendientes.sort(key=lambda s: s.fecha)
    for sesion in sesiones_pendientes:
        items_pendientes.append({
            'tipo': 'sesion',
            'objeto': sesion,
            'valor': sesion.precio,
            'pagado': False,
            'monto_pagado': 0
        })
    
    # Agregar informes pendientes/parciales (más antiguos primero)
    informes_por_pagar = [
        i for i in informes 
        if i.estado_pago != EstadoPagoInforme.PAGADO
    ]
    informes_por_pagar.sort(key=lambda i: i.fecha_creacion)
    for informe in informes_por_pagar:
        deuda_restante = informe.precio - informe.monto_pagado
        items_pendientes.append({
            'tipo': 'informe',
            'objeto': informe,
            'valor': deuda_restante,
            'pagado': False,
            'monto_pagado': 0
        })
    
    # PASO 2: Simular distribución de pagos sin modificar BD
    saldo_restante = saldo_pagador
    
    for item in items_pendientes:
        if saldo_restante <= 0.01:
            break
        
        valor_item = item['valor']
        
        if item['tipo'] == 'sesion':
            if saldo_restante >= valor_item - 0.01:
                # Sesión se paga completamente
                item['pagado'] = True
                item['monto_pagado'] = valor_item
                saldo_restante -= valor_item
            else:
                # No alcanza para pagar esta sesión
                break
        
        elif item['tipo'] == 'informe':
            if saldo_restante >= valor_item - 0.01:
                # Informe se paga completamente
                item['pagado'] = True
                item['monto_pagado'] = valor_item
                saldo_restante -= valor_item
            else:
                # Pago parcial al informe
                item['monto_pagado'] = saldo_restante
                saldo_restante = 0
                break
    
    # PASO 3: Actualizar estados en BD según lo calculado
    for item in items_pendientes:
        objeto = item['objeto']
        
        if item['tipo'] == 'sesion':
            if item['pagado']:
                objeto.estado = EstadoSesion.PAGA
            else:
                objeto.estado = EstadoSesion.PENDIENTE
            guardar_sesion(objeto)
        
        elif item['tipo'] == 'informe':
            # Sumar lo que ya estaba pagado con lo nuevo que se pagó en esta ronda
            objeto.monto_pagado = objeto.monto_pagado + item['monto_pagado']
            
            # Asegurar que no supere el precio
            if objeto.monto_pagado >= objeto.precio - 0.01:
                objeto.monto_pagado = objeto.precio
                objeto.estado_pago = EstadoPagoInforme.PAGADO
            elif objeto.monto_pagado > 0.01:
                objeto.estado_pago = EstadoPagoInforme.PAGO_PARCIAL
            else:
                objeto.estado_pago = EstadoPagoInforme.PENDIENTE
            
            guardar_informe(objeto)
    
    # PASO 4: Calcular deuda final basado en estados reales después de actualizar
    sesiones_actualizadas = obtener_sesiones_paciente(paciente_id)
    informes_actualizados = obtener_informes_paciente(paciente_id)
    
    deuda_sesiones = sum(s.precio for s in sesiones_actualizadas 
                         if s.estado == EstadoSesion.PENDIENTE)
    deuda_informes = sum(i.precio - i.monto_pagado for i in informes_actualizados 
                         if i.estado_pago != EstadoPagoInforme.PAGADO)
    
    deuda_final = deuda_sesiones + deuda_informes
    
    # Si hay saldo restante sin usar, es crédito negativo
    if saldo_restante > 0.01:
        deuda_final = -saldo_restante
    
    # Guardar deuda actualizada
    paciente = obtener_paciente(paciente_id)
    paciente.deuda = deuda_final
    guardar_paciente(paciente)


def obtener_estadisticas_mensuales() -> dict:
    """
    Obtiene estadísticas de facturación del mes actual.
    Retorna un diccionario con:
    - total_cobrado: dinero total cobrado en el mes
    - desglose_cobrado: desglose por tipo de paciente
    - informes_total: monto total de informes cobrables
    - deuda_total: deuda total acumulada
    - deuda_por_tipo: desglose de deuda por tipo de paciente
    """
    from datetime import datetime as dt
    
    ahora = dt.now()
    mes_actual = ahora.month
    año_actual = ahora.year
    
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