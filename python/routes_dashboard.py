from flask import Blueprint, render_template
from flask_login import current_user, login_required

from .models import Cliente, Moto, OrdenServicio, Repuesto

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@login_required
def index():
    tid = current_user.taller_id

    total_clientes = Cliente.query.filter_by(taller_id=tid).count()
    total_motos = Moto.query.filter_by(taller_id=tid).count()
    ordenes_activas = OrdenServicio.query.filter(
        OrdenServicio.taller_id == tid,
        OrdenServicio.estado.notin_(["entregado", "cancelado"]),
    ).count()

    repuestos_bajos = []
    if current_user.es_admin:
        repuestos = Repuesto.query.filter_by(taller_id=tid).all()
        repuestos_bajos = [r for r in repuestos if r.stock_bajo]

    ultimas_ordenes = (
        OrdenServicio.query.filter_by(taller_id=tid)
        .order_by(OrdenServicio.fecha_ingreso.desc())
        .limit(8)
        .all()
    )

    return render_template(
        "dashboard.html",
        total_clientes=total_clientes,
        total_motos=total_motos,
        ordenes_activas=ordenes_activas,
        repuestos_bajos=repuestos_bajos,
        ultimas_ordenes=ultimas_ordenes,
    )
