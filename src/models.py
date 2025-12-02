from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


# Enums para los tipos (como en Java)
class TipoPaciente(Enum):
    ESTANDAR = "Estándar"
    MENSUAL = "Mensual"
    DIAGNOSTICO = "Diagnóstico"


class TipoSesion(Enum):
    ESTANDAR = "Estándar"
    TRAUMA = "Tratamiento de trauma"
    PAREJA = "Pareja"
    FAMILIAR = "Familiar"
    DIAGNOSTICO = "Diagnóstico"


class EstadoSesion(Enum):
    PAGA = "Paga"
    PENDIENTE = "Pendiente"


class ConceptoPago(Enum):
    SESION = "Sesión"
    MENSUAL = "Mensual"
    DIAGNOSTICO = "Diagnóstico"
    INFORME = "Informe"


class TipoInforme(Enum):
    CARTA = "Carta - Instituciones, psiquiatras, trabajo, etc."
    COMPROBANTE = "Comprobante de tratamiento"
    PSICODIAGNOSTICO = "Psicodiagnóstico"
    REUNION = "Reunión (colegios, etc.)"


class EstadoInforme(Enum):
    PENDIENTE = "Pendiente"
    FALTA_PRUEBAS = "Falta aplicar pruebas"
    TERMINADO = "Terminado"
    ENTREGADO = "Entregado"


class EstadoPagoInforme(Enum):
    PENDIENTE = "Pendiente"
    PAGO_PARCIAL = "Pago parcial"
    PAGADO = "Pagado"


# Clases de datos con @dataclass
@dataclass
class Paciente:
    id: Optional[int]  # None cuando es nuevo, se asigna al guardar en BD
    nombre: str
    tipo: TipoPaciente
    costo_sesion: float
    deuda: float  # Puede ser negativo si tiene saldo a favor
    arancel_social: bool
    notas: str
    fecha_creacion: datetime
    
    def __str__(self):
        return f"{self.nombre} ({self.tipo.value})"


@dataclass
class Sesion:
    id: Optional[int]
    paciente_id: int
    fecha: datetime
    precio: float
    estado: EstadoSesion
    tipo: TipoSesion
    notas: str
    
    def __str__(self):
        return f"Sesión {self.tipo.value} - {self.fecha.strftime('%d/%m/%Y')}"


@dataclass
class Pago:
    id: Optional[int]
    paciente_id: int
    fecha: datetime
    monto: float
    concepto: ConceptoPago
    notas: str
    
    def __str__(self):
        return f"Pago ${self.monto} - {self.concepto.value}"


@dataclass
class Informe:
    id: Optional[int]
    paciente_id: int
    tipo: TipoInforme
    estado: EstadoInforme
    estado_pago: EstadoPagoInforme
    precio: float
    monto_pagado: float  # Para tracking de pagos parciales
    notas: str
    fecha_creacion: datetime
    
    def __str__(self):
        return f"Informe {self.tipo.value} - {self.estado.value}"