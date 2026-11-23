from datetime import datetime, timedelta
import html
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Sala, Reserva


class SalaForm(forms.ModelForm):
    """
    RFD-4.1: Formulario para el catálogo de salas y laboratorios.
    Valida y sanitiza las entradas de cada espacio físico.
    """
    class Meta:
        model = Sala
        fields = ['nombre', 'capacidad', 'equipo_disponible', 'estado']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Laboratorio de Computación 1'}),
            'capacidad': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Capacidad en personas', 'min': 1, 'max': 500}),
            'equipo_disponible': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Ej: 30 PCs, Proyector, Pizarra interactiva'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean_nombre(self):
        # UTN-03: Sanitización de entradas contra XSS
        nombre = html.escape(self.cleaned_data.get('nombre', '').strip())
        if not nombre:
            raise ValidationError("El nombre de la sala es obligatorio.")
        return nombre

    def clean_equipo_disponible(self):
        return html.escape(self.cleaned_data.get('equipo_disponible', '').strip())


class ReservaForm(forms.ModelForm):
    """
    UTN-03, RFD-4.2 y RFD-4.3: Formulario principal de creación y edición de reservas.
    Implementa la detección automática de conflictos y todas las reglas de negocio (RN-4.1 a RN-4.3).
    """
    class Meta:
        model = Reserva
        fields = [
            'sala', 
            'solicitante', 
            'identificacion_solicitante', 
            'correo_solicitante', 
            'fecha', 
            'hora_inicio', 
            'hora_fin', 
            'motivo'
        ]
        widgets = {
            'sala': forms.Select(attrs={'class': 'form-select'}),
            'solicitante': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre completo del solicitante'}),
            'identificacion_solicitante': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cédula o carné institucional'}),
            'correo_solicitante': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@universidad.ac.cr'}),
            'fecha': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'hora_inicio': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'hora_fin': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'motivo': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Justificación o curso académico'}),
        }

    def clean_solicitante(self):
        # UTN-03: Sanitización estricta del nombre del solicitante (dato sensible)
        return html.escape(self.cleaned_data.get('solicitante', '').strip())

    def clean_motivo(self):
        return html.escape(self.cleaned_data.get('motivo', '').strip())

    def clean(self):
        """
        Validación integral de Reglas de Negocio y Detección de Conflictos.
        """
        cleaned_data = super().clean()
        sala = cleaned_data.get('sala')
        fecha = cleaned_data.get('fecha')
        hora_inicio = cleaned_data.get('hora_inicio')
        hora_fin = cleaned_data.get('hora_fin')

        # Si faltan campos obligatorios, Django ya reportó error individual
        if not (sala and fecha and hora_inicio and hora_fin):
            return cleaned_data

        # Validación de Estado de la Sala
        
        if sala.estado == Sala.ESTADO_MANTENIMIENTO:
            raise ValidationError(
                f"La sala '{sala.nombre}' se encuentra actualmente en mantenimiento y no admite reservas."
            )

        
        # Regla de Negocio RN-4.1: Hora de fin posterior a la de inicio
        
        if hora_fin <= hora_inicio:
            raise ValidationError({
                'hora_fin': "La hora de fin debe ser estrictamente posterior a la hora de inicio (RN-4.1)."
            })

        # Combinar fecha y hora para validar tiempos
        zona_horaria = timezone.get_current_timezone()
        inicio_dt = timezone.make_aware(datetime.combine(fecha, hora_inicio), zona_horaria)
        fin_dt = timezone.make_aware(datetime.combine(fecha, hora_fin), zona_horaria)
        ahora = timezone.now()

        
        # Regla de Negocio RN-4.2: Duración máxima de 3 horas
        
        duracion = fin_dt - inicio_dt
        if duracion > timedelta(hours=3):
            horas_solicitadas = duracion.total_seconds() / 3600
            raise ValidationError(
                f"Una reserva puede durar como máximo 3 horas (RN-4.2). Duración solicitada: {horas_solicitadas:.1f} horas."
            )

        
        # Regla de Negocio RN-4.3: Mínimo 24 horas de anticipación
        
        anticipacion_minima = ahora + timedelta(hours=24)
        if inicio_dt < anticipacion_minima:
            raise ValidationError(
                "Solo se permite reservar con al menos 24 horas de anticipación (RN-4.3)."
            )

    
        # RFD-4.3: Detección de Conflictos / Traslapes de Horario
    
        # Buscamos si existe OTRA reserva ACTIVA en la misma sala y fecha que se traslape
        conflictos = Reserva.objects.filter(
            sala=sala,
            fecha=fecha,
            estado=Reserva.ESTADO_ACTIVA,
            hora_inicio__lt=hora_fin,   # Inicia antes de que la nueva termine
            hora_fin__gt=hora_inicio    # Termina después de que la nueva empiece
        )

        # Si estamos editando una reserva existente, la excluimos de la búsqueda de conflicto
        if self.instance and self.instance.pk:
            conflictos = conflictos.exclude(pk=self.instance.pk)

        if conflictos.exists():
            conflicto = conflictos.first()
            raise ValidationError(
                f"Conflicto de horario (RFD-4.3): La sala '{sala.nombre}' ya está reservada de "
                f"{conflicto.hora_inicio.strftime('%H:%M')} a {conflicto.hora_fin.strftime('%H:%M')} "
                f"(Código: {conflicto.codigo}). Seleccione otra franja horaria o sala."
            )

        return cleaned_data