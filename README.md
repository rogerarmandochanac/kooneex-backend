#Kooneex Backend 🛺
Backend robusto para una plataforma de mototaxis estilo Uber, desarrollado con Django y Django Channels para comunicación en tiempo real. 
🚀 Características Principales

    Autenticación Dual: Registro y login para Pasajeros y Conductores (Mototaxistas).
    Comunicación en Tiempo Real: Implementación de WebSockets para:
        Seguimiento de ubicación en vivo.
        Envío y recepción de solicitudes de viaje.
        Chat interno entre conductor y pasajero.
    Gestión de Viajes: Lógica de asignación, cálculo de distancias y estados del viaje (Solicitado, En curso, Finalizado).
    API RESTful: Endpoints documentados para la gestión de perfiles, historial y soporte. 

🛠️ Stack Tecnológico

    Framework: Django & Django REST Framework
    Real-time: Django Channels (ASGI)
    Base de Datos: PostgreSQL (con PostGIS opcional para geolocalización)
    Cache/Broker: Redis (necesario para las capas de canales de sockets)
    Servidor ASGI: Daphne o Uvicorn 

📦 Instalación

    Clonar el repositorio:
    bash

    git clone https://github.com
    cd kooneex-backend

    Usa el código con precaución.
    Crear y activar entorno virtual:
    bash

    python -m venv venv
    source venv/bin/activate  # En Windows: venv\Scripts\activate

    Usa el código con precaución.
    Instalar dependencias:
    bash

    pip install -r requirements.txt

    Usa el código con precaución.
    Configurar variables de entorno:
    Crea un archivo .env basado en .env.example y añade tus credenciales de BD y Redis.
    Migraciones y servidor:
    bash

    python manage.py migrate
    python manage.py runserver

    Usa el código con precaución.
     

🔌 WebSockets (Eventos)
El sistema utiliza los siguientes eventos principales de socket:

    pickup.request: El pasajero solicita un viaje.
    location.update: El conductor envía su posición GPS actual.
    trip.status: Notificaciones de cambio de estado (ej. "El mototaxi ha llegado").

📄 Licencia
Este proyecto está bajo la Licencia MIT. Consulta el archivo LICENSE para más detalles.
Desarrollado por Roger Armando Chan
¿Te gustaría que añada una sección específica sobre cómo probar los sockets con alguna herramienta o cómo configurar Redis en Docker?

