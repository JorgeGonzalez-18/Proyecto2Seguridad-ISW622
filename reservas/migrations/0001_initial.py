
from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import reservas.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Sala',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100, unique=True, verbose_name='Nombre de la sala/laboratorio')),
                ('capacidad', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(500)], verbose_name='Capacidad (personas)')),
                ('equipo_disponible', models.TextField(verbose_name='Equipo disponible')),
                ('estado', models.CharField(choices=[('DISPONIBLE', 'Disponible'), ('MANTENIMIENTO', 'En Mantenimiento')], default='DISPONIBLE', max_length=20, verbose_name='Estado de la sala')),
                ('creado_en', models.DateTimeField(auto_now_add=True)),
                ('actualizado_en', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Sala / Laboratorio',
                'verbose_name_plural': 'Salas y Laboratorios',
                'ordering': ['nombre'],
            },
        ),
        migrations.CreateModel(
            name='Reserva',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('codigo', models.CharField(default=reservas.models.generar_codigo_reserva, editable=False, max_length=20, unique=True, verbose_name='Código de Reserva')),
                ('solicitante', models.CharField(max_length=150, verbose_name='Nombre del solicitante')),
                ('identificacion_solicitante', models.CharField(max_length=30, verbose_name='Cédula / Identificación')),
                ('correo_solicitante', models.EmailField(max_length=254, verbose_name='Correo institucional del solicitante')),
                ('fecha', models.DateField(verbose_name='Fecha de reserva')),
                ('hora_inicio', models.TimeField(verbose_name='Hora de inicio')),
                ('hora_fin', models.TimeField(verbose_name='Hora de fin')),
                ('motivo', models.TextField(blank=True, verbose_name='Motivo académico / uso')),
                ('estado', models.CharField(choices=[('ACTIVA', 'Activa'), ('CANCELADA', 'Cancelada'), ('FINALIZADA', 'Finalizada')], default='ACTIVA', max_length=20, verbose_name='Estado de la reserva')),
                ('creado_en', models.DateTimeField(auto_now_add=True)),
                ('actualizado_en', models.DateTimeField(auto_now=True)),
                ('creado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reservas_creadas', to=settings.AUTH_USER_MODEL, verbose_name='Registrado por')),
                ('sala', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='reservas', to='reservas.sala', verbose_name='Sala o Laboratorio')),
            ],
            options={
                'verbose_name': 'Reserva',
                'verbose_name_plural': 'Reservas',
                'ordering': ['-fecha', 'hora_inicio'],
            },
        ),
    ]