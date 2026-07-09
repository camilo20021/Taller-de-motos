from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from .decorators import admin_required
from .extensions import db
from .models import MovimientoInventario, Repuesto

inventario_bp = Blueprint("inventario", __name__, url_prefix="/inventario")


def _get_repuesto_or_404(repuesto_id):
    repuesto = Repuesto.query.filter_by(
        id=repuesto_id, taller_id=current_user.taller_id
    ).first()
    if not repuesto:
        abort(404)
    return repuesto


@inventario_bp.route("/")
@login_required
@admin_required
def listar():
    q = request.args.get("q", "").strip()
    query = Repuesto.query.filter_by(taller_id=current_user.taller_id)
    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(Repuesto.nombre.ilike(like), Repuesto.codigo.ilike(like))
        )
    repuestos = query.order_by(Repuesto.nombre).all()
    return render_template("inventario_listar.html", repuestos=repuestos, q=q)


@inventario_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
@admin_required
def nuevo():
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        if not nombre:
            flash("El nombre del repuesto es obligatorio.", "error")
            return render_template("inventario_form.html", repuesto=None)

        stock_inicial = request.form.get("stock", type=int) or 0
        repuesto = Repuesto(
            taller_id=current_user.taller_id,
            codigo=request.form.get("codigo", "").strip(),
            nombre=nombre,
            categoria=request.form.get("categoria", "").strip(),
            stock=stock_inicial,
            stock_minimo=request.form.get("stock_minimo", type=int) or 0,
            precio_compra=request.form.get("precio_compra", type=float) or 0,
            precio_venta=request.form.get("precio_venta", type=float) or 0,
            proveedor=request.form.get("proveedor", "").strip(),
        )
        db.session.add(repuesto)
        db.session.commit()

        if stock_inicial > 0:
            db.session.add(
                MovimientoInventario(
                    taller_id=current_user.taller_id,
                    repuesto_id=repuesto.id,
                    tipo="entrada",
                    cantidad=stock_inicial,
                    motivo="Registro inicial de inventario",
                    usuario_id=current_user.id,
                )
            )
            db.session.commit()

        flash("Repuesto agregado al inventario.", "success")
        return redirect(url_for("inventario.listar"))

    return render_template("inventario_form.html", repuesto=None)


@inventario_bp.route("/<int:repuesto_id>/editar", methods=["GET", "POST"])
@login_required
@admin_required
def editar(repuesto_id):
    repuesto = _get_repuesto_or_404(repuesto_id)

    if request.method == "POST":
        repuesto.codigo = request.form.get("codigo", "").strip()
        repuesto.nombre = request.form.get("nombre", "").strip()
        repuesto.categoria = request.form.get("categoria", "").strip()
        repuesto.stock_minimo = request.form.get("stock_minimo", type=int) or 0
        repuesto.precio_compra = request.form.get("precio_compra", type=float) or 0
        repuesto.precio_venta = request.form.get("precio_venta", type=float) or 0
        repuesto.proveedor = request.form.get("proveedor", "").strip()
        db.session.commit()
        flash("Repuesto actualizado.", "success")
        return redirect(url_for("inventario.listar"))

    return render_template("inventario_form.html", repuesto=repuesto)


@inventario_bp.route("/<int:repuesto_id>/movimiento", methods=["POST"])
@login_required
@admin_required
def registrar_movimiento(repuesto_id):
    repuesto = _get_repuesto_or_404(repuesto_id)
    tipo = request.form.get("tipo")
    cantidad = request.form.get("cantidad", type=int) or 0
    motivo = request.form.get("motivo", "").strip()

    if tipo not in ("entrada", "salida") or cantidad <= 0:
        flash("Datos de movimiento inválidos.", "error")
        return redirect(url_for("inventario.listar"))

    if tipo == "salida" and repuesto.stock < cantidad:
        flash("No hay suficiente stock para esa salida.", "error")
        return redirect(url_for("inventario.listar"))

    repuesto.stock += cantidad if tipo == "entrada" else -cantidad
    db.session.add(
        MovimientoInventario(
            taller_id=current_user.taller_id,
            repuesto_id=repuesto.id,
            tipo=tipo,
            cantidad=cantidad,
            motivo=motivo
            or ("Entrada manual" if tipo == "entrada" else "Salida manual"),
            usuario_id=current_user.id,
        )
    )
    db.session.commit()
    flash("Movimiento de inventario registrado.", "success")
    return redirect(url_for("inventario.listar"))
