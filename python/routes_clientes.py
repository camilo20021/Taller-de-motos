from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from .decorators import admin_required
from .extensions import db
from .models import Cliente, Moto

clientes_bp = Blueprint("clientes", __name__, url_prefix="/clientes")


def _get_cliente_or_404(cliente_id):
    cliente = Cliente.query.filter_by(
        id=cliente_id, taller_id=current_user.taller_id
    ).first()
    if not cliente:
        abort(404)
    return cliente


def _get_moto_or_404(moto_id):
    moto = Moto.query.filter_by(id=moto_id, taller_id=current_user.taller_id).first()
    if not moto:
        abort(404)
    return moto


@clientes_bp.route("/")
@login_required
def listar():
    q = request.args.get("q", "").strip()
    query = Cliente.query.filter_by(taller_id=current_user.taller_id)
    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(
                Cliente.nombre.ilike(like),
                Cliente.cedula.ilike(like),
                Cliente.celular.ilike(like),
            )
        )
    clientes = query.order_by(Cliente.nombre).all()
    return render_template("clientes_listar.html", clientes=clientes, q=q)


@clientes_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
@admin_required
def nuevo():
    if request.method == "POST":
        cedula = request.form.get("cedula", "").strip()
        nombre = request.form.get("nombre", "").strip()
        celular = request.form.get("celular", "").strip()

        if not all([nombre, cedula, celular]):
            flash("Nombre, cédula y celular son obligatorios.", "error")
            return render_template("clientes_form.html", cliente=None)

        existente = Cliente.query.filter_by(
            taller_id=current_user.taller_id, cedula=cedula
        ).first()
        if existente:
            flash("Ya existe un cliente registrado con esa cédula.", "error")
            return render_template("clientes_form.html", cliente=None)

        cliente = Cliente(
            taller_id=current_user.taller_id,
            nombre=nombre,
            cedula=cedula,
            celular=celular,
            correo=request.form.get("correo", "").strip(),
            direccion=request.form.get("direccion", "").strip(),
        )
        db.session.add(cliente)
        db.session.commit()
        flash("Cliente registrado correctamente.", "success")
        return redirect(url_for("clientes.detalle", cliente_id=cliente.id))

    return render_template("clientes_form.html", cliente=None)


@clientes_bp.route("/<int:cliente_id>/editar", methods=["GET", "POST"])
@login_required
@admin_required
def editar(cliente_id):
    cliente = _get_cliente_or_404(cliente_id)

    if request.method == "POST":
        cliente.nombre = request.form.get("nombre", "").strip()
        cliente.cedula = request.form.get("cedula", "").strip()
        cliente.celular = request.form.get("celular", "").strip()
        cliente.correo = request.form.get("correo", "").strip()
        cliente.direccion = request.form.get("direccion", "").strip()
        db.session.commit()
        flash("Datos del cliente actualizados.", "success")
        return redirect(url_for("clientes.detalle", cliente_id=cliente.id))

    return render_template("clientes_form.html", cliente=cliente)


@clientes_bp.route("/<int:cliente_id>")
@login_required
def detalle(cliente_id):
    cliente = _get_cliente_or_404(cliente_id)
    return render_template("cliente_detalle.html", cliente=cliente)


@clientes_bp.route("/<int:cliente_id>/eliminar", methods=["POST"])
@login_required
@admin_required
def eliminar(cliente_id):
    cliente = _get_cliente_or_404(cliente_id)
    if cliente.motos:
        flash("No puedes eliminar un cliente que tiene motos registradas.", "error")
        return redirect(url_for("clientes.detalle", cliente_id=cliente.id))
    db.session.delete(cliente)
    db.session.commit()
    flash("Cliente eliminado.", "success")
    return redirect(url_for("clientes.listar"))


@clientes_bp.route("/<int:cliente_id>/motos/nueva", methods=["GET", "POST"])
@login_required
def nueva_moto(cliente_id):
    cliente = _get_cliente_or_404(cliente_id)

    if request.method == "POST":
        placa = request.form.get("placa", "").strip().upper()
        marca = request.form.get("marca", "").strip()

        if not all([placa, marca]):
            flash("Placa y marca son obligatorias.", "error")
            return render_template("motos_form.html", cliente=cliente, moto=None)

        existente = Moto.query.filter_by(
            taller_id=current_user.taller_id, placa=placa
        ).first()
        if existente:
            flash("Ya existe una moto registrada con esa placa.", "error")
            return render_template("motos_form.html", cliente=cliente, moto=None)

        moto = Moto(
            taller_id=current_user.taller_id,
            cliente_id=cliente.id,
            placa=placa,
            marca=marca,
            modelo=request.form.get("modelo", "").strip(),
            anio=request.form.get("anio", type=int),
            color=request.form.get("color", "").strip(),
            cilindraje=request.form.get("cilindraje", "").strip(),
            kilometraje=request.form.get("kilometraje", type=int),
        )
        db.session.add(moto)
        db.session.commit()
        flash("Moto registrada correctamente.", "success")
        return redirect(url_for("clientes.detalle", cliente_id=cliente.id))

    return render_template("motos_form.html", cliente=cliente, moto=None)


@clientes_bp.route("/motos/<int:moto_id>/editar", methods=["GET", "POST"])
@login_required
def editar_moto(moto_id):
    moto = _get_moto_or_404(moto_id)
    cliente = moto.cliente

    if request.method == "POST":
        moto.placa = request.form.get("placa", "").strip().upper()
        moto.marca = request.form.get("marca", "").strip()
        moto.modelo = request.form.get("modelo", "").strip()
        moto.anio = request.form.get("anio", type=int)
        moto.color = request.form.get("color", "").strip()
        moto.cilindraje = request.form.get("cilindraje", "").strip()
        moto.kilometraje = request.form.get("kilometraje", type=int)
        db.session.commit()
        flash("Datos de la moto actualizados.", "success")
        return redirect(url_for("clientes.detalle", cliente_id=cliente.id))

    return render_template("motos_form.html", cliente=cliente, moto=moto)
