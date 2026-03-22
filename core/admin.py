from django.contrib import admin
from .models import Usuario, Mototaxi, Viaje, Comision, Tarifa
from django.utils import timezone

admin.site.register(Usuario)
admin.site.register(Mototaxi)
admin.site.register(Viaje)
admin.site.register(Tarifa)

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
