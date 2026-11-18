from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("usuarios/", views.lista_usuarios, name="lista_usuarios"),
    path("usuarios/crear/", views.crear_usuario, name="crear_usuario"),
    path("usuarios/<int:pk>/editar/", views.editar_usuario, name="editar_usuario"),
    path(
        "usuarios/<int:pk>/eliminar/", views.eliminar_usuario, name="eliminar_usuario"
    ),
    path("roles/", views.lista_roles, name="lista_roles"),
    path("roles/crear/", views.crear_rol, name="crear_rol"),
    path("roles/<int:pk>/editar/", views.editar_rol, name="editar_rol"),
    path("roles/<int:pk>/eliminar/", views.eliminar_rol, name="eliminar_rol"),
]
