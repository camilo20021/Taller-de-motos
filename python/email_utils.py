from flask_mail import Message

from .extensions import mail


def enviar_correo_moto_terminada(orden):
    """Notifica al cliente que su moto ya esta lista para reclamar.

    Devuelve True si se envio, False si el cliente no tiene correo registrado.
    Si falla el envio (SMTP mal configurado, sin internet, etc.) deja que la
    excepcion suba para que quien llama decida como avisar al usuario.
    """
    cliente = orden.cliente
    if not cliente or not cliente.correo:
        return False

    moto = orden.moto
    asunto = f"Tu moto {moto.marca} (placa {moto.placa}) ya está lista"
    cuerpo = f"""Hola {cliente.nombre},

Te informamos que tu moto {moto.marca} {moto.modelo or ''} (placa {moto.placa}) ya está lista para reclamar en el taller.

Orden de servicio N.º {orden.id}
Diagnóstico: {orden.diagnostico or 'N/A'}

Por favor acércate al taller para recogerla cuando puedas.

¡Gracias por confiar en nosotros!
"""
    mensaje = Message(subject=asunto, recipients=[cliente.correo], body=cuerpo)
    mail.send(mensaje)
    return True
