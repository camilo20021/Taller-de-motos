from datetime import datetime
from decimal import Decimal

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from .email_utils import enviar_correo_moto_terminada
from .extensions import db
from .models import (
    ESTADOS_ORDEN,
    Cliente,
    Moto,
    MovimientoInventario,
    OrdenRepuesto,
    OrdenServicio,
    OrdenServicioItem,
    Repuesto,
    Usuario,
)

ordenes_bp = Blueprint("ordenes", __name__, url_prefix="/ordenes")


def _get_orden_or_404(orden_id):
    orden = OrdenServicio.query.filter_by(
        id=orden_id, taller_id=current_user.taller_id
    ).first()
    if not orden:
        abort(404)
    return orden


@ordenes_bp.route("/")
@login_required
def listar():
    estado = request.args.get("estado", "")
    query = OrdenServicio.query.filter_by(taller_id=current_user.taller_id)
    if estado:
        query = query.filter_by(estado=estado)
    ordenes = query.order_by(OrdenServicio.fecha_ingreso.desc()).all()
    return render_template(
        "ordenes_listar.html", ordenes=ordenes, estado=estado, estados=ESTADOS_ORDEN
    )


@ordenes_bp.route("/nueva", methods=["GET", "POST"])
@login_required
def nueva():
    tid = current_user.taller_id

    if request.method == "POST":
        moto = Moto.query.filter_by(
            id=request.form.get("moto_id", type=int), taller_id=tid
        ).first()
        if not moto:
            flash("Selecciona una moto válida (busca al cliente primero).", "error")
            return redirect(url_for("ordenes.nueva"))

        fecha_estimada = request.form.get("fecha_entrega_estimada") or None
        if fecha_estimada:
            fecha_estimada = datetime.strptime(fecha_estimada, "%Y-%m-%d").date()

        orden = OrdenServicio(
            taller_id=tid,
            moto_id=moto.id,
            cliente_id=moto.cliente_id,
            mecanico_id=request.form.get("mecanico_id", type=int) or None,
            problema_reportado=request.form.get("problema_reportado", "").strip(),
            kilometraje_ingreso=request.form.get("kilometraje_ingreso", type=int),
            fecha_entrega_estimada=fecha_estimada,
            estado="recibida",
        )
        db.session.add(orden)
        db.session.commit()
        flash("Orden de servicio creada. La moto ha ingresado al taller.", "success")
        return redirect(url_for("ordenes.detalle", orden_id=orden.id))

    cliente_id = request.args.get("cliente_id", type=int)
    cliente = (
        Cliente.query.filter_by(id=cliente_id, taller_id=tid).first()
        if cliente_id
        else None
    )
    mecanicos = Usuario.query.filter_by(taller_id=tid, activo=True).all()
    return render_template("orden_form.html", cliente=cliente, mecanicos=mecanicos)


@ordenes_bp.route("/buscar-cliente")
@login_required
def buscar_cliente():
    cedula = request.args.get("cedula", "").strip()
    cliente = Cliente.query.filter_by(
        taller_id=current_user.taller_id, cedula=cedula
    ).first()
    if not cliente:
        flash(
            "No se encontró ningún cliente con esa cédula. Regístralo primero.",
            "error",
        )
        return redirect(url_for("clientes.nuevo"))
    return redirect(url_for("ordenes.nueva", cliente_id=cliente.id))


@ordenes_bp.route("/<int:orden_id>")
@login_required
def detalle(orden_id):
    orden = _get_orden_or_404(orden_id)
    repuestos_disponibles = (
        Repuesto.query.filter_by(taller_id=current_user.taller_id)
        .order_by(Repuesto.nombre)
        .all()
    )
    subtotal_repuestos = sum((i.subtotal for i in orden.items_repuesto), Decimal("0"))
    subtotal_servicios = sum((i.precio for i in orden.items_servicio), Decimal("0"))
    return render_template(
        "orden_detalle.html",
        orden=orden,
        estados=ESTADOS_ORDEN,
        repuestos_disponibles=repuestos_disponibles,
        subtotal_repuestos=subtotal_repuestos,
        subtotal_servicios=subtotal_servicios,
        subtotal_total=subtotal_repuestos + subtotal_servicios,
    )


@ordenes_bp.route("/<int:orden_id>/estado", methods=["POST"])
@login_required
def cambiar_estado(orden_id):
    orden = _get_orden_or_404(orden_id)
    nuevo_estado = request.form.get("estado")

    if nuevo_estado not in ESTADOS_ORDEN:
        flash("Estado no válido.", "error")
        return redirect(url_for("ordenes.detalle", orden_id=orden.id))

    estado_anterior = orden.estado
    orden.estado = nuevo_estado
    orden.diagnostico = request.form.get("diagnostico", orden.diagnostico)
    orden.observaciones = request.form.get("observaciones", orden.observaciones)

    if nuevo_estado == "entregado" and not orden.fecha_salida:
        orden.fecha_salida = datetime.utcnow()

    db.session.commit()

    if nuevo_estado == "terminado" and estado_anterior != "terminado" and not orden.notificado:
        try:
            enviado = enviar_correo_moto_terminada(orden)
            if enviado:
                orden.notificado = True
                db.session.commit()
                flash("Estado actualizado y correo enviado al cliente.", "success")
            else:
                flash(
                    "Estado actualizado. El cliente no tiene correo registrado, "
                    "no se envió notificación.",
                    "warning",
                )
        except Exception as exc:  # SMTP mal configurado, sin internet, etc.
            flash(f"Estado actualizado, pero no se pudo enviar el correo: {exc}", "warning")
    else:
        flash("Estado de la orden actualizado.", "success")

    return redirect(url_for("ordenes.detalle", orden_id=orden.id))


@ordenes_bp.route("/<int:orden_id>/repuestos", methods=["POST"])
@login_required
def agregar_repuesto(orden_id):
    orden = _get_orden_or_404(orden_id)
    repuesto = Repuesto.query.filter_by(
        id=request.form.get("repuesto_id", type=int), taller_id=current_user.taller_id
    ).first()
    cantidad = request.form.get("cantidad", type=int) or 0

    if not repuesto or cantidad <= 0:
        flash("Selecciona un repuesto y una cantidad válida.", "error")
        return redirect(url_for("ordenes.detalle", orden_id=orden.id))

    if repuesto.stock < cantidad:
        flash(
            f"Stock insuficiente de {repuesto.nombre} (disponible: {repuesto.stock}).",
            "error",
        )
        return redirect(url_for("ordenes.detalle", orden_id=orden.id))

    item = OrdenRepuesto(
        orden_id=orden.id,
        repuesto_id=repuesto.id,
        cantidad=cantidad,
        precio_unitario=repuesto.precio_venta,
    )
    repuesto.stock -= cantidad
    movimiento = MovimientoInventario(
        taller_id=current_user.taller_id,
        repuesto_id=repuesto.id,
        tipo="salida",
        cantidad=cantidad,
        motivo=f"Usado en orden #{orden.id}",
        orden_id=orden.id,
        usuario_id=current_user.id,
    )
    db.session.add(item)
    db.session.add(movimiento)
    db.session.commit()
    flash(f"{cantidad} x {repuesto.nombre} agregado a la orden.", "success")
    return redirect(url_for("ordenes.detalle", orden_id=orden.id))


@ordenes_bp.route("/<int:orden_id>/servicios", methods=["POST"])
@login_required
def agregar_servicio(orden_id):
    orden = _get_orden_or_404(orden_id)
    descripcion = request.form.get("descripcion", "").strip()
    precio = request.form.get("precio", type=float) or 0

    if not descripcion or precio <= 0:
        flash("Describe el servicio y su precio.", "error")
        return redirect(url_for("ordenes.detalle", orden_id=orden.id))

    item = OrdenServicioItem(
        orden_id=orden.id, descripcion=descripcion, precio=Decimal(str(precio))
    )
    db.session.add(item)
    db.session.commit()
    flash("Servicio agregado a la orden.", "success")
    return redirect(url_for("ordenes.detalle", orden_id=orden.id))
