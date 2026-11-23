from django.contrib import admin
from .models import Sala, Reserva


@admin.register(Sala)
class SalaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'capacidad', 'estado', 'creado_en')
    list_filter = ('estado',)
    search_fields = ('nombre', 'equipo_disponible')


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'sala', 'solicitante', 'fecha', 'hora_inicio', 'hora_fin', 'estado')
    list_filter = ('estado', 'fecha', 'sala')
    search_fields = ('codigo', 'solicitante', 'identificacion_solicitante', 'correo_solicitante')
    readonly_fields = ('codigo', 'creado_en', 'actualizado_en')