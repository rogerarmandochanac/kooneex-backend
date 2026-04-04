from firebase_admin import messaging

def enviar_notificacion_push(token_destino, titulo, cuerpo, datos_extra=None):
    """
    token_destino: El token FCM que guardaste en la DB
    titulo: "¡Nueva Solicitud!"
    cuerpo: "Hay un viaje cerca de ti por $50"
    datos_extra: Diccionario con IDs para que la app sepa qué pantalla abrir
    """
    message = messaging.Message(
        notification=messaging.Notification(
            title=titulo,
            body=cuerpo,
        ),
        data=datos_extra or {}, # Aquí envías {'viaje_id': '25', 'type': 'nueva_solicitud'}
        token=token_destino,
    )
    
    try:
        response = messaging.send(message)
        print('Successfully sent message:', response)
    except Exception as e:
        print('Error sending message:', e)