from datetime import datetime
from decimal import Decimal

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from .decorators import admin_required
from .extensions import db
from .models import CierreCaja, Documento, OrdenServicio

documentos_bp = Blueprint("documentos", __name__, url_prefix="/documentos")

IVA_PORCENTAJE = Decimal("0.19")


def _get_orden_or_404(orden_id):
    orden = OrdenServicio.query.filter_by(
        id=orden_id, taller_id=current_user.taller_id
    ).first()
    if not orden:
        abort(404)
    return orden


def _get_documento_or_404(documento_id):
    documento = Documento.query.filter_by(
        id=documento_id, taller_id=current_user.taller_id
    ).first()
    if not documento:
        abort(404)
    return documento


def _calcular_totales(orden):
    subtotal_repuestos = sum(
        (i.subtotal for i in orden.items_repuesto), Decimal("0")
    )
    subtotal_servicios = sum((i.precio for i in orden.items_servicio), Decimal("0"))
    subtotal = subtotal_repuestos + subtotal_servicios
    iva = (subtotal * IVA_PORCENTAJE).quantize(Decimal("0.01"))
    total = subtotal + iva
    return subtotal, iva, total


@documentos_bp.route("/")
@login_required
@admin_required
def listar():
    documentos = (
        Documento.query.filter_by(taller_id=current_user.taller_id)
        .order_by(Documento.fecha.desc())
        .all()
    )
    return render_template("facturacion_listar.html", documentos=documentos)


@documentos_bp.route("/orden/<int:orden_id>/generar", methods=["POST"])
@login_required
@admin_required
def generar(orden_id):
    orden = _get_orden_or_404(orden_id)
    tipo = request.form.get("tipo")

    if tipo not in ("cotizacion", "factura"):
        flash("Tipo de documento no válido.", "error")
        return redirect(url_for("ordenes.detalle", orden_id=orden.id))

    if not orden.items_repuesto and not orden.items_servicio:
        flash("Agrega al menos un repuesto o servicio antes de generar el documento.", "error")
        return redirect(url_for("ordenes.detalle", orden_id=orden.id))

    subtotal, iva, total = _calcular_totales(orden)
    prefijo = "COT" if tipo == "cotizacion" else "FAC"
    consecutivo = (
        Documento.query.filter_by(taller_id=current_user.taller_id, tipo=tipo).count()
        + 1
    )
    numero = f"{prefijo}-{consecutivo:05d}"

    documento = Documento(
        taller_id=current_user.taller_id,
        orden_id=orden.id,
        tipo=tipo,
        numero=numero,
        subtotal=subtotal,
        iva=iva,
        total=total,
        estado="pendiente",
    )
    db.session.add(documento)
    db.session.commit()

    etiqueta = "Cotización" if tipo == "cotizacion" else "Factura"
    flash(f"{etiqueta} {numero} generada.", "success")
    return redirect(url_for("documentos.detalle", documento_id=documento.id))


@documentos_bp.route("/<int:documento_id>")
@login_required
@admin_required
def detalle(documento_id):
    documento = _get_documento_or_404(documento_id)
    return render_template("factura_detalle.html", documento=documento)


@documentos_bp.route("/<int:documento_id>/pagar", methods=["POST"])
@login_required
@admin_required
def marcar_pagada(documento_id):
    documento = _get_documento_or_404(documento_id)
    documento.estado = "pagada"
    documento.fecha_pago = datetime.utcnow()

    caja_abierta = CierreCaja.query.filter_by(
        taller_id=current_user.taller_id, estado="abierta"
    ).first()
    if caja_abierta:
        documento.cierre_caja_id = caja_abierta.id
    else:
        flash(
            "Documento marcado como pagado, pero no hay una caja abierta: "
            "esta venta no se contará en ningún cierre de caja.",
            "warning",
        )

    db.session.commit()
    flash("Documento marcado como pagado.", "success")
    return redirect(url_for("documentos.detalle", documento_id=documento.id))
