from firebase_admin import messaging

def enviar_notificacion(token, titulo, mensaje):
    message = messaging.Message(
        notification=messaging.Notification(
            title=titulo,
            body=mensaje,
        ),
        token=token,
    )

    response = messaging.send(message)
    return response