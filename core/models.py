import io

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Q, Sum
from PIL import Image
from django.db import models
from django.core.files.base import ContentFile
from django.core.validators import MinValueValidator, MaxValueValidator
from rest_framework.decorators import action

class Comunidad(models.Model):
    nombre = models.CharField(max_length=100, unique=True) # Ej: Pomuch, Tenabo
    activa = models.BooleanField(default=True)
    creada_en = models.DateTimeField(auto_now_add=True)
    

    def __str__(self):
        return self.nombre

# =========================
# USUARIO
# =========================
class Usuario(AbstractUser):
    fcm_token = models.CharField(max_length=255, blank=True, null=True)
    """
    Modelo de usuario personalizado con roles.
    """
    comunidad = models.ForeignKey(
        Comunidad, 
        on_delete=models.PROTECT,
        null=True,
        blank=True, # Protegemos para no borrar comunidades con viajes
        related_name='usuarios_pertenecientes'
    )

    class Roles(models.TextChoices):
        ADMIN = 'admin', 'Administrador'
        MOTOTAXISTA = 'mototaxista', 'Mototaxista'
        PASAJERO = 'pasajero', 'Pasajero'

    rol = models.CharField(
        max_length=20,
        choices=Roles.choices,
        default=Roles.PASAJERO
    )
    telefono = models.CharField(max_length=15, blank=True, null=True)
    foto = models.ImageField(upload_to='usuarios/', blank=True, null=True)

    lat = models.FloatField(null=True, blank=True)
    lon = models.FloatField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['username']),
            models.Index(fields=['rol']),
        ]
    
    def save(self, *args, **kwargs):
        # 1. Verificar si hay una foto nueva o modificada
        if self.foto:
            try:
                # Abrir la imagen con Pillow
                img = Image.open(self.foto)

                # Si es muy pesada o grande, procesamos
                if img.height > 600 or img.width > 600 or self.foto.file.size > 200 * 1024:
                    # Convertir a RGB (necesario para JPEG)
                    if img.mode != 'RGB':
                        img = img.convert('RGB')

                    # Redimensionar manteniendo aspecto proporcional
                    output_size = (600, 600)
                    img.thumbnail(output_size)

                    # Guardar en buffer con compresión
                    buffer = io.BytesIO()
                    img.save(buffer, format='JPEG', quality=60) # Calidad optimizada
                    buffer.seek(0)

                    # Reemplazar el archivo
                    self.foto.save(self.foto.name, ContentFile(buffer.read()), save=False)
            except Exception as e:
                print(f"Error al comprimir imagen: {e}")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.rol})"
    
    

    @property
    def nombre_completo(self):
        """Devuelve nombre completo o username."""
        return f"{self.first_name} {self.last_name}".strip() or self.username
    
    @property
    def deuda_total(self):
        # Suma el monto_comision de todas las comisiones donde pagado=False
        resultado = self.mis_comisiones.filter(pagado=False).aggregate(total=Sum('monto_comision'))
        return resultado['total'] or 0.0


# =========================
# TARIFA
# =========================
class Tarifa(models.Model):
    """
    Configuración de tarifas del sistema.
    """

    tarifa = models.DecimalField(max_digits=10, decimal_places=2, default=10.0)
    comision = models.PositiveIntegerField(default=1)
    activa = models.BooleanField(default=True)
    creada_en = models.DateTimeField(auto_now_add=True)
    limite_deuda = models.DecimalField(max_digits=10, decimal_places=2, default=50.0)

    def __str__(self):
        return f"Tarifa: ${self.tarifa}"
    

# =========================
# MOTOTAXI
# =========================
class Mototaxi(models.Model):
    """
    Representa un mototaxi asociado a un conductor.
    """

    conductor = models.OneToOneField(
        'Usuario',
        on_delete=models.CASCADE,
        limit_choices_to={'rol': Usuario.Roles.MOTOTAXISTA}
    )
    placa = models.CharField(max_length=10)
    modelo = models.CharField(max_length=50)
    capacidad = models.PositiveIntegerField(default=4)
    disponible = models.BooleanField(default=True)
    latitud = models.FloatField(null=True, blank=True)
    longitud = models.FloatField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['disponible']),
            models.Index(fields=['conductor']),
            models.Index(fields=['latitud', 'longitud']),
        ]

    def __str__(self):
        return f"{self.placa} - {self.conductor.username}"

    def actualizar_ubicacion(self, lat, lon):
        """
        Actualiza la ubicación del mototaxi.
        """
        self.latitud = lat
        self.longitud = lon
        self.save(update_fields=['latitud', 'longitud'])

# =========================
# DESTINO
# =========================
class Destino(models.Model):
    nombre = models.CharField(max_length=100)
    latitud = models.DecimalField(max_digits=9, decimal_places=6)
    longitud = models.DecimalField(max_digits=9, decimal_places=6)
    comunidad = models.ForeignKey(
        Comunidad, 
        on_delete=models.PROTECT,
        null=True,
        blank=True, # Protegemos para no borrar comunidades con viajes
        related_name='destinos_disponibles'
    )

    def __str__(self):
        return self.nombre

# =========================
# VIAJE
# =========================
class Viaje(models.Model):
    """Representa un viaje solicitado por un pasajero.
    """

    class Estados(models.TextChoices):
        PENDIENTE = 'pendiente', 'Pendiente'
        ACEPTADO = 'aceptado', 'Aceptado'
        EN_CURSO = 'en_curso', 'En curso'
        COMPLETADO = 'completado', 'Completado'
        CANCELADO = 'cancelado', 'Cancelado'
        RECHAZADO = 'rechazado', 'Rechazado'

    pasajero = models.ForeignKey(
        'Usuario',
        on_delete=models.CASCADE,
        related_name='viajes'
    )
    mototaxista = models.ForeignKey(
        'Usuario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='viajes_mototaxista',
        limit_choices_to={'rol': Usuario.Roles.MOTOTAXISTA}
    )
    origen_lat = models.DecimalField(max_digits=9, decimal_places=6)
    origen_lon = models.DecimalField(max_digits=9, decimal_places=6)
    origen = models.ForeignKey(Destino, on_delete=models.CASCADE, related_name="viajes_como_origen")
    destino = models.ForeignKey(Destino, on_delete=models.CASCADE, related_name="viajes")
    cantidad_pasajeros = models.PositiveIntegerField(default=1)
    referencia = models.CharField(max_length=100)
    costo_estimado = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    costo_final = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    estado = models.CharField(max_length=20, choices=Estados.choices, default=Estados.PENDIENTE)
    creado_en = models.DateTimeField(auto_now_add=True)
    comunidad = models.ForeignKey(
        Comunidad, 
        on_delete=models.PROTECT,
        null=True,
        blank=True, # Protegemos para no borrar comunidades con viajes
        related_name='viajes_realizados'
    )

    class Meta:
        ordering = ['-creado_en']
        indexes = [
            models.Index(fields=['pasajero', 'estado']),
            models.Index(fields=['mototaxista', 'estado']),
            models.Index(fields=['estado', 'creado_en']),
        ]

    # =========================
    # LÓGICA DE NEGOCIO
    # =========================

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    

    def aceptar(self, mototaxista):
        """Permite a un mototaxista aceptar un viaje.
        Controla concurrencia y disponibilidad.
        """

        if self.estado != self.Estados.PENDIENTE:
            raise ValidationError("El viaje no está disponible.")

        if mototaxista.rol != Usuario.Roles.MOTOTAXISTA:
            raise ValidationError("Usuario no autorizado.")

        with transaction.atomic():
            viaje = Viaje.objects.select_for_update().get(pk=self.pk)

            if viaje.estado != self.Estados.PENDIENTE:
                raise ValidationError("El viaje ya fue tomado.")

            if Viaje.objects.filter(
                mototaxista=mototaxista,
                estado__in=[self.Estados.ACEPTADO, self.Estados.EN_CURSO]
            ).exists():
                raise ValidationError("El mototaxista ya tiene un viaje activo.")

            viaje.estado = self.Estados.ACEPTADO
            viaje.mototaxista = mototaxista
            viaje.save()

            Mototaxi.objects.filter(conductor=mototaxista).update(disponible=False)

    def puede_eliminarse(self):
        return self.estado in [self.Estados.PENDIENTE, self.Estados.RECHAZADO]

    def iniciar(self):
        if self.estado != "aceptado":
            raise ValidationError("Solo viajes aceptados pueden iniciar.")
        
        self.estado = "en_curso"
        self.save()

    def eliminar(self):
        """
        Elimina el viaje si está permitido.
        """
        if not self.puede_eliminarse():
            raise ValidationError("No se puede eliminar este viaje.")
        self.delete()
    
    def cancelar(self):
        if self.estado not in ["pendiente", "cancelado", "aceptado"]:
            raise ValidationError("No se puede cancelar el viaje")
            
        with transaction.atomic():
            self.estado = "cancelado"
            self.save()
    
    def completar(self, usuario):
        if self.estado not in ["en_curso", "aceptado"]:
            raise ValidationError("Estado inválido.")

        with transaction.atomic():
            self.estado = "completado"
            self.save()

        if usuario.rol == "mototaxista" and self.mototaxista == usuario:
            try:
                mototaxi = Mototaxi.objects.get(conductor=usuario)
                mototaxi.disponible = True
                mototaxi.save()
            except Mototaxi.DoesNotExist:
                pass

        # 🔥 NUEVA LÓGICA DE COMISIÓN
        if self.costo_final and self.mototaxista:
            # Obtenemos la tarifa activa para saber cuánto cobrar de comisión
            tarifa_activa = Tarifa.objects.filter(activa=True).last()
            #porcentaje = tarifa_activa.comision if tarifa_activa else 1 # default 1%
            #monto_comision = (self.costo_final * porcentaje) / 100
            monto_comision = tarifa_activa.comision

            # Creamos el registro de deuda para el mototaxista
            Comision.objects.get_or_create(
                viaje=self,
                defaults={
                    "mototaxista": self.mototaxista,
                    "monto_viaje": self.costo_final,
                    "monto_comision": monto_comision
                }
            )
    
    def clean(self):
        """Validación de negocio:
        - Un pasajero no puede tener múltiples viajes activos
        """

        if self.pasajero:
            tiene_viaje_activo = Viaje.objects.filter(
                pasajero=self.pasajero,
                estado__in=['pendiente', 'aceptado', 'en_curso']
            ).exclude(id=self.id).exists()

            if tiene_viaje_activo:
                raise ValidationError(
                    "Ya tienes un viaje activo. Completa o cancela antes de solicitar otro."
                )
    
    def __str__(self):
        return str(self.id)

# =========================
# OFERTA
# =========================
class Oferta(models.Model):
    """
    Representa una oferta de un mototaxista para un viaje.
    """
     
    viaje = models.ForeignKey(Viaje, related_name='ofertas', 
                              on_delete=models.CASCADE)
    
    mototaxista = models.ForeignKey('Usuario', 
                                    on_delete=models.CASCADE, 
                                   limit_choices_to={'rol':'mototaxista'})
    
    monto = models.DecimalField(max_digits=10, 
                                decimal_places=2)
    
    tiempo_estimado = models.CharField(max_length=50)
    aceptada = models.BooleanField(default=False)
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['mototaxista', 'aceptada']),
            models.Index(fields=['viaje', 'aceptada']),
            models.Index(fields=['creada_en']),
        ]
        ordering = ['-creada_en']
    
    def aceptar(self):
        with transaction.atomic():
            if Oferta.objects.filter(viaje=self.viaje, aceptada=True).exists():
                raise ValidationError("Ya hay una oferta aceptada.")

            self.aceptada = True
            self.save(update_fields=['aceptada'])

            # actualizar viaje
            self.viaje.mototaxista = self.mototaxista
            self.viaje.costo_final = self.monto
            self.viaje.estado = 'aceptado'
            self.viaje.save()

            # rechazar otras
            Oferta.objects.filter(viaje=self.viaje).exclude(pk=self.pk).update(aceptada=False)

            # actualizar disponibilidad
            Mototaxi.objects.filter(conductor=self.mototaxista).update(disponible=False)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
    
    def clean(self):
        """
        Validaciones de negocio para evitar:
        - múltiples ofertas activas
        - mototaxistas ocupados
        - ofertas en viajes no disponibles
        """

        if not self.mototaxista:
            return

        # 🚨 Validar rol
        if self.mototaxista.rol != 'mototaxista':
            raise ValidationError("Solo mototaxistas pueden hacer ofertas.")

        # 🚨 Validar que el viaje esté disponible
        if self.viaje and self.viaje.estado != 'pendiente':
            raise ValidationError("Este viaje ya no está disponible.")

        # 🚨 Validar actividad (tu lógica original)
        tiene_actividad = Viaje.objects.filter(
            Q(mototaxista=self.mototaxista, estado__in=['aceptado', 'en_curso']) |
            Q(ofertas__mototaxista=self.mototaxista, ofertas__viaje__estado='pendiente')
        ).exclude(pk=self.viaje.pk if self.viaje else None).exists()

        if tiene_actividad:
            raise ValidationError("Ya tienes una oferta activa o viaje en curso.")

        if not self.mototaxista.lat or not self.mototaxista.lon:
            raise ValidationError(
                "El mototaxista debe tener ubicación actual"
            )
        
        # 🚨 FRENO DE SEGURIDAD: Validación de Deuda
        if self.mototaxista.rol == 'mototaxista':
            tarifa_activa = Tarifa.objects.filter(activa=True).last()
            limite = tarifa_activa.limite_deuda if tarifa_activa else 50.0
            
            deuda = self.mototaxista.deuda_total
            
            if deuda >= limite:
                raise ValidationError(
                    f"Bloqueo por deuda: Debes ${deuda}. "
                    f"El límite es ${limite}. Paga tus comisiones para seguir ofertando."
                )

    def __str__(self):
        return f"Oferta ${self.monto} por {self.mototaxista.username}"


# =========================
# PAGO
# =========================
class Pago(models.Model):
    """
    Representa el pago realizado al mototaxista de parte del pasajero
    aun no impletementado.
    """

    viaje = models.OneToOneField(Viaje, on_delete=models.CASCADE)
    monto = models.DecimalField(max_digits=8, decimal_places=2)
    metodo = models.CharField(max_length=50, 
                             choices=[('efectivo', 'Efectivo'), ('tarjeta', 'Tarjeta')], 
                             default='efectivo')
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['viaje']),
        ]

    def __str__(self):
        return f"Pago de ${self.monto} por {self.viaje}"

# =========================
# COMISION (NUEVO)
# =========================
class Comision(models.Model):
    viaje = models.OneToOneField(Viaje, on_delete=models.CASCADE, related_name='comision_detalle')
    mototaxista = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='mis_comisiones')
    monto_viaje = models.DecimalField(max_digits=10, decimal_places=2)
    monto_comision = models.DecimalField(max_digits=10, decimal_places=2)
    
    pagado = models.BooleanField(default=False, help_text="¿El mototaxista ya pagó la comisión a Kooneex?")
    fecha_pago = models.DateTimeField(null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Comisión"
        verbose_name_plural = "Comisiones"
        ordering = ['-creado_en']

    def __str__(self):
        estado = "PAGADO" if self.pagado else "PENDIENTE"
        return f"{self.mototaxista.username} - ${self.monto_comision} ({estado})"

class Calificacion(models.Model):
    viaje = models.OneToOneField('Viaje', on_delete=models.CASCADE, related_name='calificacion')
    pasajero = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='calificaciones_dadas')
    mototaxista = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='calificaciones_recibidas')
    
    puntuacion = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comentario = models.TextField(blank=True, null=True)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.puntuacion} estrellas para {self.mototaxista.username}"
