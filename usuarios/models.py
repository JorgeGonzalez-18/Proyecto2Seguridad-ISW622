from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.


class Rol(models.Model):
    """
    UTN-06: Modelo para la gestión dinámica de Roles en el sistema.
    Roles base esperados: SuperAdmin, Auditor, Gestor de reservas.
    """
    nombre = models.CharField(max_length=50, unique=True, verbose_name="Nombre del Rol")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    
    # UTN-05: Permisos granulares asignados al rol (no directamente al usuario)
    puede_crear = models.BooleanField(default=False, verbose_name="Permiso Crear")
    puede_editar = models.BooleanField(default=False, verbose_name="Permiso Editar")
    puede_borrar = models.BooleanField(default=False, verbose_name="Permiso Borrar")
    puede_ver_reportes = models.BooleanField(default=False, verbose_name="Permiso Ver Reportes")
    
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name = "Rol"
        verbose_name_plural = "Roles"
        ordering = ['nombre']
    def __str__(self):
        return self.nombre
class Usuario(AbstractUser):
    """
    UTN-04: Modelo de Usuario con auditoría y RBAC.
    Hereda de AbstractUser (username, password hasheada, email, is_active, last_login).
    """
    identificacion = models.CharField(
        max_length=20, 
        unique=True, 
        verbose_name="Identificación / Cédula"
    )
    nombre_completo = models.CharField(
        max_length=150, 
        verbose_name="Nombre Completo"
    )
    rol = models.ForeignKey(
        Rol, 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True, 
        related_name="usuarios",
        verbose_name="Rol Asignado"
    )
    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ['username']
    def __str__(self):
        return f"{self.username} - {self.nombre_completo} ({self.rol.nombre if self.rol else 'Sin Rol'})"