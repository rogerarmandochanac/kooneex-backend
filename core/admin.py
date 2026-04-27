from django.contrib import admin
from .models import Usuario, Mototaxi, Viaje, Comision, Tarifa, Destino, Oferta, Comunidad, Calificacion
from django.utils import timezone
from django.db.models import Count

admin.site.register(Mototaxi)
admin.site.register(Tarifa)
admin.site.register(Destino)
admin.site.register(Oferta)
admin.site.register(Comunidad)
admin.site.register(Calificacion)

@admin.register(Viaje)
class ViajeAdmin(admin.ModelAdmin):
    list_display = ('id', 'pasajero__username', 'mototaxista__username','referencia', 'destino')
    list_filter = ('pasajero__username', 'mototaxista__username')
    search_fields = ('pasajero__username', 'mototaxista__username', 'destino__nombre')

@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('username', 'first_name', 'last_name', 'telefono', 'rol')
    list_filter = ('rol',)
    search_fields = ('username', 'first_name', 'last_name', 'email')

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}

        conteo_roles = Usuario.objects.values('rol').annotate(total=Count('rol'))

        resumen = {
            'Mototaxista': 0,
            'Pasajero': 0
        }

        for item in conteo_roles:
            if item['rol'] == 'Mototaxista':
                resumen['Mototaxista'] = item['total']
            elif item['rol'] == 'Pasajero':
                resumen['Pasajero'] = item['total']

        extra_context['resumen_roles'] = resumen

        return super().changelist_view(request, extra_context=extra_context)

@admin.register(Comision)
class ComisionAdmin(admin.ModelAdmin):
    list_display = ('mototaxista', 'monto_viaje', 'monto_comision', 'pagado', 'creado_en')
    list_filter = ('pagado', 'creado_en', 'mototaxista')
    search_fields = ('mototaxista__username', 'mototaxista__first_name')
    
    # Acción para cobrar en lote
    actions = ['marcar_como_pagado']

    @admin.action(description='💰 Marcar comisiones como PAGADAS')
    def marcar_como_pagado(self, request, queryset):
        queryset.update(pagado=True, fecha_pago=timezone.now())
        self.message_user(request, "Las comisiones seleccionadas han sido liquidadas.")
