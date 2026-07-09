from datetime import datetime

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from .decorators import admin_required
from .extensions import db
from .models import CierreCaja

caja_bp = Blueprint("caja", __name__, url_prefix="/caja")


def _get_caja_abierta():
    return CierreCaja.query.filter_by(
        taller_id=current_user.taller_id, estado="abierta"
    ).first()


@caja_bp.route("/")
@login_required
@admin_required
def index():
    caja_abierta = _get_caja_abierta()
    historial = (
        CierreCaja.query.filter_by(taller_id=current_user.taller_id, estado="cerrada")
        .order_by(CierreCaja.fecha_cierre.desc())
        .limit(30)
        .all()
    )
    return render_template("caja.html", caja_abierta=caja_abierta, historial=historial)


@caja_bp.route("/abrir", methods=["POST"])
@login_required
@admin_required
def abrir():
    if _get_caja_abierta():
        flash("Ya hay una caja abierta. Ciérrala antes de abrir una nueva.", "error")
        return redirect(url_for("caja.index"))

    monto_inicial = request.form.get("monto_inicial", type=float) or 0

    caja = CierreCaja(
        taller_id=current_user.taller_id,
        abierto_por_id=current_user.id,
        monto_inicial=monto_inicial,
        estado="abierta",
    )
    db.session.add(caja)
    db.session.commit()
    flash("Caja abierta correctamente.", "success")
    return redirect(url_for("caja.index"))


@caja_bp.route("/<int:caja_id>/cerrar", methods=["POST"])
@login_required
@admin_required
def cerrar(caja_id):
    caja = CierreCaja.query.filter_by(
        id=caja_id, taller_id=current_user.taller_id, estado="abierta"
    ).first()
    if not caja:
        abort(404)

    monto_contado = request.form.get("monto_contado", type=float)
    if monto_contado is None:
        flash("Ingresa el efectivo contado para cerrar la caja.", "error")
        return redirect(url_for("caja.index"))

    caja.monto_contado = monto_contado
    caja.observaciones = request.form.get("observaciones", "").strip()
    caja.cerrado_por_id = current_user.id
    caja.fecha_cierre = datetime.utcnow()
    caja.estado = "cerrada"
    db.session.commit()

    if caja.diferencia == 0:
        flash("Caja cerrada. ¡Cuadró perfecto!", "success")
    elif caja.diferencia > 0:
        flash(f"Caja cerrada con sobrante de ${caja.diferencia:,.0f}.", "warning")
    else:
        flash(f"Caja cerrada con faltante de ${abs(caja.diferencia):,.0f}.", "warning")

    return redirect(url_for("caja.index"))
