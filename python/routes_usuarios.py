from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from .decorators import admin_required
from .extensions import db
from .models import Usuario

usuarios_bp = Blueprint("usuarios", __name__, url_prefix="/usuarios")


def _get_usuario_or_404(usuario_id):
    usuario = Usuario.query.filter_by(
        id=usuario_id, taller_id=current_user.taller_id
    ).first()
    if not usuario:
        abort(404)
    return usuario


@usuarios_bp.route("/")
@login_required
@admin_required
def listar():
    usuarios = (
        Usuario.query.filter_by(taller_id=current_user.taller_id)
        .order_by(Usuario.nombre)
        .all()
    )
    return render_template("usuarios_listar.html", usuarios=usuarios)


@usuarios_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
@admin_required
def nuevo():
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        correo = request.form.get("correo", "").strip().lower()
        password = request.form.get("password", "")
        rol = request.form.get("rol", "mecanico")

        if not all([nombre, correo, password]):
            flash("Nombre, correo y contraseña son obligatorios.", "error")
            return render_template("usuario_form.html", usuario=None)

        if len(password) < 6:
            flash("La contraseña debe tener al menos 6 caracteres.", "error")
            return render_template("usuario_form.html", usuario=None)

        if rol not in ("admin", "mecanico"):
            rol = "mecanico"

        if Usuario.query.filter_by(correo=correo).first():
            flash("Ya existe una cuenta con ese correo.", "error")
            return render_template("usuario_form.html", usuario=None)

        usuario = Usuario(
            taller_id=current_user.taller_id, nombre=nombre, correo=correo, rol=rol
        )
        usuario.set_password(password)
        db.session.add(usuario)
        db.session.commit()
        flash(f"Cuenta creada para {nombre}.", "success")
        return redirect(url_for("usuarios.listar"))

    return render_template("usuario_form.html", usuario=None)


@usuarios_bp.route("/<int:usuario_id>/estado", methods=["POST"])
@login_required
@admin_required
def cambiar_estado(usuario_id):
    usuario = _get_usuario_or_404(usuario_id)

    if usuario.id == current_user.id:
        flash("No puedes desactivar tu propia cuenta.", "error")
        return redirect(url_for("usuarios.listar"))

    usuario.activo = not usuario.activo
    db.session.commit()
    estado = "activada" if usuario.activo else "desactivada"
    flash(f"Cuenta de {usuario.nombre} {estado}.", "success")
    return redirect(url_for("usuarios.listar"))
