from datetime import datetime
from decimal import Decimal

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db

# Flujo de estados de una orden de servicio (ingreso -> salida de la moto)
ESTADOS_ORDEN = [
    "recibida",
    "diagnostico",
    "en_reparacion",
    "esperando_repuesto",
    "terminado",
    "entregado",
    "cancelado",
]

ESTADOS_LABEL = {
    "recibida": "Recibida",
    "diagnostico": "En diagnóstico",
    "en_reparacion": "En reparación",
    "esperando_repuesto": "Esperando repuesto",
    "terminado": "Terminada (lista para entregar)",
    "entregado": "Entregada al cliente",
    "cancelado": "Cancelada",
}


class Taller(db.Model):
    """Cada fila es un taller/cliente del sistema (multi-tenant)."""

    __tablename__ = "talleres"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    nit = db.Column(db.String(50))
    direccion = db.Column(db.String(200))
    telefono = db.Column(db.String(30))
    correo = db.Column(db.String(120))
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)

    usuarios = db.relationship("Usuario", backref="taller", lazy=True)


class Usuario(UserMixin, db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    taller_id = db.Column(db.Integer, db.ForeignKey("talleres.id"), nullable=False)
    nombre = db.Column(db.String(120), nullable=False)
    correo = db.Column(db.String(120), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(20), default="admin")  # admin, mecanico, recepcionista
    activo = db.Column(db.Boolean, default=True)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def es_admin(self):
        return self.rol == "admin"


class Cliente(db.Model):
    __tablename__ = "clientes"

    id = db.Column(db.Integer, primary_key=True)
    taller_id = db.Column(db.Integer, db.ForeignKey("talleres.id"), nullable=False)
    nombre = db.Column(db.String(150), nullable=False)
    cedula = db.Column(db.String(30), nullable=False)
    celular = db.Column(db.String(30), nullable=False)
    correo = db.Column(db.String(120))
    direccion = db.Column(db.String(200))
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)

    motos = db.relationship(
        "Moto", backref="cliente", lazy=True, cascade="all, delete-orphan"
    )

    __table_args__ = (
        db.UniqueConstraint("taller_id", "cedula", name="uq_cliente_taller_cedula"),
    )


class Moto(db.Model):
    __tablename__ = "motos"

    id = db.Column(db.Integer, primary_key=True)
    taller_id = db.Column(db.Integer, db.ForeignKey("talleres.id"), nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id"), nullable=False)
    placa = db.Column(db.String(20), nullable=False)
    marca = db.Column(db.String(60), nullable=False)
    modelo = db.Column(db.String(60))
    anio = db.Column(db.Integer)
    color = db.Column(db.String(40))
    cilindraje = db.Column(db.String(20))
    kilometraje = db.Column(db.Integer)

    __table_args__ = (
        db.UniqueConstraint("taller_id", "placa", name="uq_moto_taller_placa"),
    )


class OrdenServicio(db.Model):
    __tablename__ = "ordenes_servicio"

    id = db.Column(db.Integer, primary_key=True)
    taller_id = db.Column(db.Integer, db.ForeignKey("talleres.id"), nullable=False)
    moto_id = db.Column(db.Integer, db.ForeignKey("motos.id"), nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id"), nullable=False)
    mecanico_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"))

    fecha_ingreso = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_entrega_estimada = db.Column(db.Date)
    fecha_salida = db.Column(db.DateTime)

    kilometraje_ingreso = db.Column(db.Integer)
    problema_reportado = db.Column(db.Text)
    diagnostico = db.Column(db.Text)
    observaciones = db.Column(db.Text)

    estado = db.Column(db.String(30), default="recibida")
    notificado = db.Column(db.Boolean, default=False)

    moto = db.relationship("Moto")
    cliente = db.relationship("Cliente")
    mecanico = db.relationship("Usuario")

    items_repuesto = db.relationship(
        "OrdenRepuesto", backref="orden", cascade="all, delete-orphan"
    )
    items_servicio = db.relationship(
        "OrdenServicioItem", backref="orden", cascade="all, delete-orphan"
    )

    @property
    def estado_label(self):
        return ESTADOS_LABEL.get(self.estado, self.estado)


class Repuesto(db.Model):
    __tablename__ = "repuestos"

    id = db.Column(db.Integer, primary_key=True)
    taller_id = db.Column(db.Integer, db.ForeignKey("talleres.id"), nullable=False)
    codigo = db.Column(db.String(50))
    nombre = db.Column(db.String(150), nullable=False)
    categoria = db.Column(db.String(80))
    stock = db.Column(db.Integer, default=0)
    stock_minimo = db.Column(db.Integer, default=0)
    precio_compra = db.Column(db.Numeric(10, 2), default=0)
    precio_venta = db.Column(db.Numeric(10, 2), default=0)
    proveedor = db.Column(db.String(120))

    @property
    def stock_bajo(self):
        return self.stock <= self.stock_minimo


class MovimientoInventario(db.Model):
    __tablename__ = "movimientos_inventario"

    id = db.Column(db.Integer, primary_key=True)
    taller_id = db.Column(db.Integer, db.ForeignKey("talleres.id"), nullable=False)
    repuesto_id = db.Column(db.Integer, db.ForeignKey("repuestos.id"), nullable=False)
    tipo = db.Column(db.String(10))  # entrada / salida
    cantidad = db.Column(db.Integer, nullable=False)
    motivo = db.Column(db.String(200))
    orden_id = db.Column(db.Integer, db.ForeignKey("ordenes_servicio.id"), nullable=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"))
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

    repuesto = db.relationship("Repuesto")


class OrdenRepuesto(db.Model):
    """Repuestos usados dentro de una orden de servicio."""

    __tablename__ = "orden_repuestos"

    id = db.Column(db.Integer, primary_key=True)
    orden_id = db.Column(db.Integer, db.ForeignKey("ordenes_servicio.id"), nullable=False)
    repuesto_id = db.Column(db.Integer, db.ForeignKey("repuestos.id"), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Numeric(10, 2), nullable=False)

    repuesto = db.relationship("Repuesto")

    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario


class OrdenServicioItem(db.Model):
    """Mano de obra / servicios cobrados dentro de una orden."""

    __tablename__ = "orden_servicios_items"

    id = db.Column(db.Integer, primary_key=True)
    orden_id = db.Column(db.Integer, db.ForeignKey("ordenes_servicio.id"), nullable=False)
    descripcion = db.Column(db.String(200), nullable=False)
    precio = db.Column(db.Numeric(10, 2), nullable=False)


class Documento(db.Model):
    """Cotizacion o factura generada a partir de una orden de servicio."""

    __tablename__ = "documentos"

    id = db.Column(db.Integer, primary_key=True)
    taller_id = db.Column(db.Integer, db.ForeignKey("talleres.id"), nullable=False)
    orden_id = db.Column(db.Integer, db.ForeignKey("ordenes_servicio.id"), nullable=False)
    cierre_caja_id = db.Column(db.Integer, db.ForeignKey("cierres_caja.id"), nullable=True)
    tipo = db.Column(db.String(15))  # cotizacion / factura
    numero = db.Column(db.String(30))
    subtotal = db.Column(db.Numeric(10, 2))
    iva = db.Column(db.Numeric(10, 2))
    total = db.Column(db.Numeric(10, 2))
    estado = db.Column(db.String(20), default="pendiente")  # pendiente / pagada / anulada
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_pago = db.Column(db.DateTime)

    orden = db.relationship("OrdenServicio")


class CierreCaja(db.Model):
    """Turno de caja: se abre con una base inicial y se cierra contando el
    efectivo real, para detectar sobrantes/faltantes frente a lo esperado."""

    __tablename__ = "cierres_caja"

    id = db.Column(db.Integer, primary_key=True)
    taller_id = db.Column(db.Integer, db.ForeignKey("talleres.id"), nullable=False)
    abierto_por_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    cerrado_por_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"))

    fecha_apertura = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_cierre = db.Column(db.DateTime)

    monto_inicial = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    monto_contado = db.Column(db.Numeric(10, 2))
    observaciones = db.Column(db.Text)

    estado = db.Column(db.String(15), default="abierta")  # abierta / cerrada

    abierto_por = db.relationship("Usuario", foreign_keys=[abierto_por_id])
    cerrado_por = db.relationship("Usuario", foreign_keys=[cerrado_por_id])
    documentos = db.relationship("Documento", backref="cierre_caja")

    @property
    def total_ventas(self):
        return sum((d.total for d in self.documentos if d.estado == "pagada"), Decimal("0"))

    @property
    def monto_esperado(self):
        return self.monto_inicial + self.total_ventas

    @property
    def diferencia(self):
        if self.monto_contado is None:
            return None
        return self.monto_contado - self.monto_esperado
