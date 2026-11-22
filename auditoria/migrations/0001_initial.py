import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="LogAuditoria",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("fecha", models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="Fecha y hora")),
                ("tipo_evento", models.CharField(
                    choices=[
                        ("LOGIN_OK", "Inicio de sesión exitoso"),
                        ("LOGIN_FAIL", "Inicio de sesión fallido"),
                        ("ROL_CAMBIO", "Cambio de rol o permisos"),
                        ("ACCESO_403", "Acceso denegado (403)"),
                    ],
                    db_index=True, max_length=20, verbose_name="Tipo de evento")),
                ("username_intentado", models.CharField(blank=True, max_length=150, verbose_name="Username")),
                ("usuario_afectado", models.CharField(blank=True, max_length=150, verbose_name="Usuario afectado")),
                ("ip", models.GenericIPAddressField(blank=True, null=True, verbose_name="IP")),
                ("ruta", models.CharField(blank=True, max_length=500, verbose_name="Ruta")),
                ("detalle", models.TextField(blank=True, verbose_name="Detalle")),
                ("usuario", models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name="logs_auditoria", to=settings.AUTH_USER_MODEL, verbose_name="Usuario")),
            ],
            options={
                "verbose_name": "Registro de auditoría",
                "verbose_name_plural": "Registros de auditoría",
                "ordering": ["-fecha"],
            },
        ),
    ]
