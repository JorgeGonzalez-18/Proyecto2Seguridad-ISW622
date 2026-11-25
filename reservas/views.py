from datetime import datetime
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from usuarios.decorators import requiere_permiso, requiere_rol
from .forms import ReservaForm, SalaForm
from .models import Reserva, Sala
from .reportes import calcular_ocupacion_semanal, inicio_de_semana

# CATÁLOGO DE SALAS Y LABORATORIOS 

@login_required(login_url="login")
def lista_salas_view(request):
    """
    RFD-4.1: Catálogo visual de salas y laboratorios.
    Lectura permitida para todos los roles autenticados (SuperAdmin, Auditor, Gestor).
    """
    busqueda = request.GET.get("q", "").strip()
    estado = request.GET.get("estado", "").strip()

    salas = Sala.objects.all()
    if busqueda:
        salas = salas.filter(
            Q(nombre__icontains=busqueda) | Q(equipo_disponible__icontains=busqueda)
        )
    if estado in dict(Sala.ESTADOS_SALA):
        salas = salas.filter(estado=estado)

    paginator = Paginator(salas, 12)
    pagina = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "reservas/lista_salas.html",
        {
            "pagina": pagina,
            "busqueda": busqueda,
            "estado_filtro": estado,
            "estados": Sala.ESTADOS_SALA,
        },
    )


@login_required(login_url="login")
@requiere_permiso("crear")
def crear_sala_view(request):
    """
    RFD-4.1: Registrar nueva sala en el catálogo.
    Exige permiso granular 'crear' (SuperAdmin o Gestor de reservas).
    """
    if request.method == "POST":
        form = SalaForm(request.POST)
        if form.is_valid():
            sala = form.save()
            messages.success(request, f"Sala '{sala.nombre}' registrada exitosamente.")
            return redirect("reservas:lista_salas")
    else:
        form = SalaForm()

    return render(request, "reservas/form_sala.html", {"form": form, "accion": "Registrar Nueva Sala"})


@login_required(login_url="login")
@requiere_permiso("editar")
def editar_sala_view(request, pk):
    """
    RFD-4.1: Modificar datos de una sala existente.
    """
    sala = get_object_or_404(Sala, pk=pk)
    if request.method == "POST":
        form = SalaForm(request.POST, instance=sala)
        if form.is_valid():
            form.save()
            messages.success(request, f"Sala '{sala.nombre}' actualizada correctamente.")
            return redirect("reservas:lista_salas")
    else:
        form = SalaForm(instance=sala)

    return render(request, "reservas/form_sala.html", {"form": form, "sala": sala, "accion": f"Editar Sala: {sala.nombre}"})



# GESTIÓN DE RESERVAS

@login_required(login_url="login")
def lista_reservas_view(request):
    """
    UTN-03 y RFD-4.2: Listado de reservas con filtros por sala, fecha y estado.
    """
    busqueda = request.GET.get("q", "").strip()
    sala_id = request.GET.get("sala", "").strip()
    estado = request.GET.get("estado", "").strip()
    fecha = request.GET.get("fecha", "").strip()

    reservas = Reserva.objects.select_related("sala", "creado_por").all()

    if busqueda:
        reservas = reservas.filter(
            Q(codigo__icontains=busqueda) |
            Q(solicitante__icontains=busqueda) |
            Q(identificacion_solicitante__icontains=busqueda)
        )
    if sala_id and sala_id.isdigit():
        reservas = reservas.filter(sala_id=int(sala_id))
    else:
        sala_id = ""
    if estado in dict(Reserva.ESTADOS_RESERVA):
        reservas = reservas.filter(estado=estado)
    if fecha:
        try:
            datetime.strptime(fecha, "%Y-%m-%d")
            reservas = reservas.filter(fecha=fecha)
        except ValueError:
            fecha = ""

    paginator = Paginator(reservas, 15)
    pagina = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "reservas/lista_reservas.html",
        {
            "pagina": pagina,
            "salas": Sala.objects.all(),
            "estados": Reserva.ESTADOS_RESERVA,
            "busqueda": busqueda,
            "sala_seleccionada": sala_id,
            "estado_seleccionado": estado,
            "fecha_seleccionada": fecha,
        },
    )


@login_required(login_url="login")
@requiere_permiso("crear")
def crear_reserva_view(request):
    """
    RFD-4.2 y RFD-4.3: Crear nueva reserva aplicando validación de traslapes y reglas de negocio.
    """
    if request.method == "POST":
        form = ReservaForm(request.POST)
        if form.is_valid():
            reserva = form.save(commit=False)
            reserva.creado_por = request.user
            reserva.save()
            messages.success(
                request,
                f"Reserva {reserva.codigo} creada con éxito para {reserva.solicitante} en '{reserva.sala.nombre}'."
            )
            return redirect("reservas:detalle_reserva", codigo=reserva.codigo)
    else:
        sala_id = request.GET.get("sala")
        inicial = {"sala": sala_id} if sala_id else {}
        form = ReservaForm(initial=inicial)

    return render(request, "reservas/crear_reserva.html", {"form": form})


@login_required(login_url="login")
def detalle_reserva_view(request, codigo):
    """
    Comprobante y detalle de una reserva específica.
    """
    reserva = get_object_or_404(Reserva.objects.select_related("sala", "creado_por"), codigo=codigo)
    return render(request, "reservas/detalle_reserva.html", {"reserva": reserva})


@login_required(login_url="login")
@requiere_permiso("borrar")
def cancelar_reserva_view(request, codigo):
    """
    RFD-4.4: Cancelar una reserva activa, liberando la franja horaria inmediatamente.
    Exige permiso 'borrar' o rol Gestor de reservas / SuperAdmin.
    """
    reserva = get_object_or_404(Reserva, codigo=codigo)

    if reserva.estado == Reserva.ESTADO_CANCELADA:
        messages.warning(request, f"La reserva {reserva.codigo} ya se encuentra cancelada.")
        return redirect("reservas:lista_reservas")

    if request.method == "POST":
        reserva.estado = Reserva.ESTADO_CANCELADA
        reserva.save(update_fields=["estado", "actualizado_en"])
        messages.success(
            request, 
            f"Reserva {reserva.codigo} cancelada correctamente. La franja horaria ha quedado liberada."
        )
        return redirect("reservas:lista_reservas")

    return render(request, "reservas/confirmar_cancelar.html", {"reserva": reserva})

# REPORTE DE OCUPACIÓN SEMANAL

@login_required(login_url="login")
@requiere_permiso("ver_reportes")
def reporte_ocupacion_view(request):
    """
    RFD-4.5: Reporte de ocupación por sala y por semana (en horas de uso).
    Exclusivo para usuarios con permiso 'ver_reportes' (SuperAdmin y Auditor).
    El Gestor de reservas no tiene acceso a este reporte analítico (HTTP 403).
    El cálculo vive en reservas/reportes.py.
    """
    hoy = timezone.localdate()
    try:
        fecha_ref = datetime.strptime(request.GET.get("fecha", ""), "%Y-%m-%d").date()
    except ValueError:
        fecha_ref = hoy

    datos = calcular_ocupacion_semanal(fecha_ref)
    datos["fecha_seleccionada"] = fecha_ref.isoformat()
    datos["es_semana_actual"] = datos["inicio_semana"] == inicio_de_semana(hoy)
    return render(request, "reservas/reporte_ocupacion.html", datos)
