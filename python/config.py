import os

from dotenv import load_dotenv

# BASE_DIR = carpeta raiz del proyecto (un nivel arriba de /python)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(BASE_DIR, ".env"))


def _bool_env(nombre, por_defecto=False):
    valor = os.environ.get(nombre)
    if valor is None:
        return por_defecto
    return valor.strip().lower() in ("1", "true", "si", "sí", "yes")


def _normalizar_database_url(url):
    """Reescribe 'postgres://' / 'postgresql://' para que usen el driver
    psycopg (v3), que es el que instala este proyecto. Supabase entrega la
    cadena de conexion con el prefijo generico 'postgresql://', que por
    defecto SQLAlchemy intenta abrir con psycopg2 (no instalado aqui)."""
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-cambiar-en-produccion")

    SQLALCHEMY_DATABASE_URI = _normalizar_database_url(
        os.environ.get(
            "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'taller.db')}"
        )
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = _bool_env("MAIL_USE_TLS", True)
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", MAIL_USERNAME)
    MAIL_SUPPRESS_SEND = _bool_env("MAIL_SUPPRESS_SEND", False)

    NOMBRE_APP = "TallerPro"

    # Este proyecto quedo configurado para un unico taller (single-tenant).
    # Estos datos se usan una sola vez, la primera vez que se arranca la app
    # con la base de datos vacia, para crear el taller y su cuenta admin.
    TALLER_NOMBRE = os.environ.get("TALLER_NOMBRE", "Motos JL Racing")
    TALLER_NIT = os.environ.get("TALLER_NIT", "")
    TALLER_DIRECCION = os.environ.get("TALLER_DIRECCION", "")
    TALLER_TELEFONO = os.environ.get("TALLER_TELEFONO", "")

    ADMIN_NOMBRE = os.environ.get("ADMIN_NOMBRE", "Administrador")
    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@motosjlracing.com")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "cambiar123")
