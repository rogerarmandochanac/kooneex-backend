from rest_framework import serializers
from geopy.distance import geodesic
from .models import (Usuario, 
                     Mototaxi, 
                     Viaje, 
                     Pago, 
                     Oferta,
                     Tarifa,
                     Destino,
                     )
from math import radians, sin, cos, sqrt, atan2
from .utils import calcular_distancia, construir_url_imagen

class UsuarioSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.CharField(read_only=True)
    class Meta:
        model = Usuario
        fields = ['id', 
                  'username', 
                  'first_name', 
                  'last_name',
                  'nombre_completo', 
                  'rol', 
                  'telefono',
                  'foto',
                  ]

class UsuarioRegistroSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = [
            "username",
            "password",
            "first_name",
            "last_name",
            "telefono",
            "rol",
            "foto",
        ]
        extra_kwargs = {
            "password": {"write_only": True}
        }

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = Usuario(**validated_data)
        user.set_password(password)
        user.save()
        return user

class MototaxiSerializer(serializers.ModelSerializer):
    conductor = UsuarioSerializer(read_only=True)

    class Meta:
        model = Mototaxi
        fields = [
            'id', 
            'conductor', 
            'placa', 
            'modelo', 
            'capacidad',
            'disponible', 
            'latitud', 
            'longitud'
        ]

class OfertaSerializer(serializers.ModelSerializer):
    """
    Serializer de ofertas.
    Incluye información del mototaxista optimizada con select_related.
    """

    mototaxista_nombre = serializers.CharField(
        source='mototaxista.nombre_completo',
        read_only=True
    )
    mototaxista_telefono = serializers.CharField(
        source='mototaxista.telefono',
        read_only=True,
        default="No disponible"  # Valor por defecto
    )

    mototaxista_foto = serializers.SerializerMethodField()
    
    class Meta:
        model = Oferta
        fields = [
            'id', 'viaje', 'monto', 'tiempo_estimado', 'aceptada', 'creada_en',
            'mototaxista', 'mototaxista_nombre', 'mototaxista_telefono', 'mototaxista_foto'
        ]
        read_only_fields = ['mototaxista', 'aceptada', 'creada_en']
    
    def get_mototaxista_foto(self, obj):
        return construir_url_imagen(self.context.get("request"), obj.mototaxista.foto)

    def create(self, validated_data):
        # Crear la instancia correctamente
        instance = Oferta(**validated_data)
        instance.full_clean()  # 🔥 dispara clean()
        instance.save()
        return instance

class DestinoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Destino
        fields = ['id', 'nombre', 'latitud', 'longitud']

class ViajeSerializer(serializers.ModelSerializer):

    pasajero_nombre = serializers.SerializerMethodField()
    mototaxista_nombre = serializers.SerializerMethodField()
    ofertas_count = serializers.SerializerMethodField()
    ofertas = OfertaSerializer(many=True, read_only=True)
    pasajero_foto = serializers.SerializerMethodField()
    pasajero_telefono = serializers.SerializerMethodField()
    conductor_lat = serializers.ReadOnlyField(source='mototaxista.lat')
    conductor_lon = serializers.ReadOnlyField(source='mototaxista.lon')
    pasajero_lat = serializers.ReadOnlyField(source='pasajero.lat')
    pasajero_lon = serializers.ReadOnlyField(source='pasajero.lon')
    destino_id = serializers.PrimaryKeyRelatedField(queryset=Destino.objects.all(),source='destino',write_only=True)
    destino = DestinoSerializer(read_only=True)
    distancia_total_km = serializers.SerializerMethodField()

    class Meta:
        model = Viaje
        fields = [
            'id', 'origen_lat', 'origen_lon', 'destino', 'destino_id',
            'cantidad_pasajeros', 'costo_estimado', 'costo_final', 'estado', 
            'pasajero_nombre', 'mototaxista_nombre', 'ofertas_count', 'ofertas',
            'referencia', 'pasajero_foto', 'pasajero_telefono', 
            'conductor_lat', 'conductor_lon', 'pasajero_lat', 'pasajero_lon', 'distancia_total_km',
        ]
        read_only_fields = ['pasajero']
    
    def get_distancia_total_km(self, obj):
        try:
            # 1. ¿Quién está consultando? 
            request = self.context.get('request')
            user = request.user if request else None

            # 2. Identificar al conductor
            # Si el viaje ya tiene conductor, usamos ese. Si no, usamos al que consulta.
            conductor = obj.mototaxista if obj.mototaxista else user
            
            # Validamos que el conductor tenga coordenadas en su perfil
            if not conductor or not getattr(conductor, 'lat', None) or not getattr(conductor, 'lon', None):
                return 0.0
            
            pos_moto = (float(conductor.lat), float(conductor.lon))
            pos_origen = (float(obj.origen_lat), float(obj.origen_lon))
            
            # Tramo A: Moto -> Pasajero
            distancia_recogida = geodesic(pos_moto, pos_origen).km
            
            # Tramo B: Pasajero -> Destino
            distancia_viaje = 0.0
            if obj.destino:
                pos_destino = (float(obj.destino.latitud), float(obj.destino.longitud))
                distancia_viaje = geodesic(pos_origen, pos_destino).km

            return round(distancia_recogida + distancia_viaje, 2)
        except Exception as e:
            print(f"Error en calculo: {e}") # Para que lo veas en consola
            return 0.0
    
    
    def create(self, validated_data):
        """Crea un viaje calculando automáticamente:
        - distancia (Haversine)
        - costo estimado basado en tarifa activa
        """
        user = self.context['request'].user
        cantidad = validated_data.get('cantidad_pasajeros', 1)
        origen_lat = validated_data['origen_lat']
        origen_lon = validated_data['origen_lon']
        destino_obj = validated_data.get('destino')
        

        # Obtener tarifa activa
        tarifa = Tarifa.objects.filter(activa=True).first()
        if not tarifa:
            raise serializers.ValidationError(
                "No hay tarifa activa configurada."
            )

        # Cálculo del costo
        costo_estimado = (tarifa.tarifa * cantidad) + tarifa.comision
        
        return Viaje.objects.create(
            pasajero=user,
            costo_estimado=costo_estimado,
            **validated_data
        )
    
    def get_pasajero_foto(self, obj):
        request = self.context.get("request")
        
        # 1. Extraer el pasajero con seguridad
        if isinstance(obj, dict):
            pasajero = obj.get('pasajero')
        else:
            pasajero = obj.pasajero
        
        # 2. Verificar existencia y foto
        if not pasajero or not getattr(pasajero, 'foto', None):
            return construir_url_imagen(request, "default.png")
            
        return construir_url_imagen(request, pasajero.foto)

    def get_pasajero_telefono(self, obj):
        # 1. Extraer el pasajero
        if isinstance(obj, dict):
            pasajero = obj.get('pasajero')
        else:
            pasajero = obj.pasajero
            
        # 2. Verificar el campo teléfono
        if pasajero and getattr(pasajero, 'telefono', None):
            return pasajero.telefono
            
        return "No disponible"
    
    def get_pasajero_nombre(self, obj):
        # Si obj es un diccionario (datos validados), usamos .get()
        if isinstance(obj, dict):
            pasajero = obj.get('pasajero')
            return pasajero.username if pasajero else None
        
        # Si obj es una instancia del modelo Viaje
        return obj.pasajero.username if obj.pasajero else None

    def get_mototaxista_nombre(self, obj):
        if isinstance(obj, dict):
            moto = obj.get('mototaxista')
            return moto.username if moto else None
        
        return obj.mototaxista.username if obj.mototaxista else None
    
    def get_ofertas_count(self, obj):
        """Contar ofertas de manera eficiente"""
        # Si ya se hizo prefetch, podemos usar all()
        if hasattr(obj, '_prefetched_objects_cache') and 'ofertas' in obj._prefetched_objects_cache:
            return len(obj._prefetched_objects_cache['ofertas'])
        
        if isinstance(obj, dict):
            return 0
        # Si no, usar count() que es optimizado por Django
        return obj.ofertas.count()

class PagoSerializer(serializers.ModelSerializer):
    viaje = ViajeSerializer(read_only=True)

    class Meta:
        model = Pago
        fields = ['id', 
                  'viaje', 
                  'monto', 
                  'metodo', 
                  'fecha']

