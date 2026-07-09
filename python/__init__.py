import os

from flask import Flask, send_from_directory

from .config import BASE_DIR, Config
from .extensions import db, login_manager, mail


def create_app():
    # Las plantillas .html viven sueltas en la raiz del proyecto (fuera de
    # css/js/python), tal como se organizo este proyecto.
    app = Flask(__name__, template_folder=BASE_DIR, static_folder=None)
    app.config.from_object(Config)

    os.makedirs(os.path.join(BASE_DIR, "instance"), exist_ok=True)

    db.init_app(app)
    mail.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Debes iniciar sesión para continuar."
    login_manager.login_message_category = "error"

    from .models import Usuario

    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))

    # Carpetas css/, js/ e img/ servidas cada una por su cuenta (en vez de
    # una unica carpeta "static") para respetar la organizacion pedida.
    @app.route("/css/<path:filename>")
    def css_files(filename):
        return send_from_directory(os.path.join(BASE_DIR, "css"), filename)

    @app.route("/js/<path:filename>")
    def js_files(filename):
        return send_from_directory(os.path.join(BASE_DIR, "js"), filename)

    @app.route("/img/<path:filename>")
    def img_files(filename):
        return send_from_directory(os.path.join(BASE_DIR, "img"), filename)

    from flask import render_template

    @app.errorhandler(403)
    def acceso_restringido(_error):
        return render_template("error_403.html"), 403

    from .routes_auth import auth_bp
    from .routes_caja import caja_bp
    from .routes_clientes import clientes_bp
    from .routes_dashboard import dashboard_bp
    from .routes_documentos import documentos_bp
    from .routes_inventario import inventario_bp
    from .routes_ordenes import ordenes_bp
    from .routes_usuarios import usuarios_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(clientes_bp)
    app.register_blueprint(ordenes_bp)
    app.register_blueprint(inventario_bp)
    app.register_blueprint(documentos_bp)
    app.register_blueprint(caja_bp)
    app.register_blueprint(usuarios_bp)

    with app.app_context():
        db.create_all()
        _sembrar_taller_inicial(app)

    return app


def _sembrar_taller_inicial(app):
    """Este sistema esta pensado para un unico taller. La primera vez que
    arranca con la base de datos vacia, crea ese taller y su cuenta admin
    a partir de las variables de entorno TALLER_* / ADMIN_*. Si ya existe
    un taller, no hace nada (evita duplicar datos en cada arranque)."""
    from .extensions import db
    from .models import Taller, Usuario

    if Taller.query.first():
        return

    taller = Taller(
        nombre=app.config["TALLER_NOMBRE"],
        nit=app.config["TALLER_NIT"],
        direccion=app.config["TALLER_DIRECCION"],
        telefono=app.config["TALLER_TELEFONO"],
        correo=app.config["ADMIN_EMAIL"],
    )
    db.session.add(taller)
    db.session.flush()

    admin = Usuario(
        taller_id=taller.id,
        nombre=app.config["ADMIN_NOMBRE"],
        correo=app.config["ADMIN_EMAIL"].strip().lower(),
        rol="admin",
    )
    admin.set_password(app.config["ADMIN_PASSWORD"])
    db.session.add(admin)
    db.session.commit()

    app.logger.info(
        "Taller '%s' creado con cuenta admin %s (cambia la contraseña luego de entrar).",
        taller.nombre,
        admin.correo,
    )
