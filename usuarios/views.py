from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from .models import Usuario, Rol
from .forms import LoginForm, UsuarioCrearForm, UsuarioEditarForm, RolForm
from .decorators import requiere_rol


def error_403(request, exception=None):
    """UTN-06: Manejador seguro de error HTTP 403 Forbidden"""
    return render(request, "403.html", status=403)


def login_view(request):
    """Inicio de sesión seguro"""
    if request.user.is_authenticated:
        return redirect("inicio")

    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            usuario = form.get_user()
            login(request, usuario)
            messages.success(
                request, f"Bienvenido, {usuario.nombre_completo or usuario.username}!"
            )
            next_url = request.GET.get("next")
            return redirect(next_url if next_url else "inicio")
        else:
            messages.error(request, "Usuario o contraseña incorrectos.")
    else:
        form = LoginForm()

    return render(request, "usuarios/login.html", {"form": form})


def logout_view(request):
    """Cierre de sesión seguro"""
    logout(request)
    messages.info(request, "Ha cerrado sesión correctamente.")
    return redirect("login")


@login_required(login_url="login")
def inicio_view(request):
    """Panel de inicio principal del sistema"""
    return render(request, "inicio.html")


#
# UTN-04: GESTIÓN DE USUARIOS
#
@login_required(login_url="login")
def lista_usuarios(request):
    """
    UTN-04: Lista de usuarios con auditoría.
    Visible para SuperAdmin, Auditor y Gestor de reservas (solo lectura de usuarios).
    """
    usuarios = Usuario.objects.select_related("rol").all()
    es_superadmin = request.user.is_superuser or (
        request.user.rol and request.user.rol.nombre == "SuperAdmin"
    )
    return render(
        request,
        "usuarios/lista_usuarios.html",
        {"usuarios": usuarios, "es_superadmin": es_superadmin},
    )


@login_required(login_url="login")
@requiere_rol(["SuperAdmin"])
def crear_usuario(request):
    """Solo el SuperAdmin puede crear nuevos usuarios"""
    if request.method == "POST":
        form = UsuarioCrearForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            messages.success(request, f"Usuario '{usuario.username}' creado con éxito.")
            return redirect("lista_usuarios")
    else:
        form = UsuarioCrearForm()
    return render(
        request, "usuarios/form_usuarios.html", {"form": form, "titulo": "Crear Usuario"}
    )


@login_required(login_url="login")
@requiere_rol(["SuperAdmin"])
def editar_usuario(request, pk):
    """Solo el SuperAdmin puede editar usuarios"""
    usuario = get_object_or_404(Usuario, pk=pk)
    if request.method == "POST":
        form = UsuarioEditarForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, f"Usuario '{usuario.username}' actualizado.")
            return redirect("lista_usuarios")
    else:
        form = UsuarioEditarForm(instance=usuario)
    return render(
        request,
        "usuarios/form_usuarios.html",
        {"form": form, "titulo": f"Editar Usuario: {usuario.username}"},
    )


@login_required(login_url="login")
@requiere_rol(["SuperAdmin"])
def eliminar_usuario(request, pk):
    """Solo el SuperAdmin puede eliminar usuarios"""
    usuario = get_object_or_404(Usuario, pk=pk)
    if usuario == request.user:
        messages.error(request, "No puede eliminar su propia cuenta de SuperAdmin.")
        return redirect("lista_usuarios")

    if request.method == "POST":
        nombre = usuario.username
        usuario.delete()
        messages.success(request, f"Usuario '{nombre}' eliminado.")
        return redirect("lista_usuarios")
    return render(
        request,
        "usuarios/confirmar_eliminar.html",
        {"objeto": usuario, "tipo": "Usuario"},
    )


#
# UTN-06: GESTIÓN DE ROLES solo SUPERADMIN
#
@login_required(login_url="login")
@requiere_rol(["SuperAdmin"])
def lista_roles(request):
    """Solo el SuperAdmin accede a la lista y gestión de roles"""
    roles = Rol.objects.all()
    return render(request, "usuarios/lista_roles.html", {"roles": roles})


@login_required(login_url="login")
@requiere_rol(["SuperAdmin"])
def crear_rol(request):
    if request.method == "POST":
        form = RolForm(request.POST)
        if form.is_valid():
            rol = form.save()
            messages.success(request, f"Rol '{rol.nombre}' creado.")
            return redirect("lista_roles")
    else:
        form = RolForm()
    return render(
        request, "usuarios/form_rol.html", {"form": form, "titulo": "Crear Rol"}
    )


@login_required(login_url="login")
@requiere_rol(["SuperAdmin"])
def editar_rol(request, pk):
    rol = get_object_or_404(Rol, pk=pk)
    if request.method == "POST":
        form = RolForm(request.POST, instance=rol)
        if form.is_valid():
            form.save()
            messages.success(request, f"Rol '{rol.nombre}' actualizado.")
            return redirect("lista_roles")
    else:
        form = RolForm(instance=rol)
    return render(
        request,
        "usuarios/form_rol.html",
        {"form": form, "titulo": f"Editar Rol: {rol.nombre}"},
    )


@login_required(login_url="login")
@requiere_rol(["SuperAdmin"])
def eliminar_rol(request, pk):
    rol = get_object_or_404(Rol, pk=pk)
    if rol.nombre in ["SuperAdmin", "Auditor", "Gestor de reservas"]:
        messages.error(request, "No se pueden eliminar los roles base del sistema.")
        return redirect("lista_roles")

    if request.method == "POST":
        nombre = rol.nombre
        rol.delete()
        messages.success(request, f"Rol '{nombre}' eliminado.")
        return redirect("lista_roles")
    return render(
        request, "usuarios/confirmar_eliminar.html", {"objeto": rol, "tipo": "Rol"}
    )
