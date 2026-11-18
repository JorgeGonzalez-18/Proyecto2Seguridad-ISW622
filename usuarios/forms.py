from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import Usuario, Rol


class LoginForm(AuthenticationForm):
    """Formulario de inicio de sesión con estilos CSS básicos"""

    username = forms.CharField(
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Nombre de usuario"}
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Contraseña"}
        )
    )


class UsuarioCrearForm(forms.ModelForm):
    """Formulario para que el SuperAdmin cree un nuevo usuario con hash Argon2id"""

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"}), label="Contraseña"
    )
    confirmar_password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        label="Confirmar Contraseña",
    )

    class Meta:
        model = Usuario
        fields = [
            "username",
            "nombre_completo",
            "identificacion",
            "email",
            "rol",
            "is_active",
        ]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "nombre_completo": forms.TextInput(attrs={"class": "form-control"}),
            "identificacion": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "rol": forms.Select(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password")
        p2 = cleaned_data.get("confirmar_password")
        if p1 and p2 and p1 != p2:
            self.add_error("confirmar_password", "Las contraseñas no coinciden.")
        return cleaned_data

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.set_password(
            self.cleaned_data["password"]
        )  # Hashea con Argon2id automáticamente
        if commit:
            usuario.save()
        return usuario


class UsuarioEditarForm(forms.ModelForm):
    """Formulario para editar datos de un usuario existente sin requerir contraseña obligatoria"""

    nueva_password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        required=False,
        label="Nueva Contraseña (dejar en blanco para no cambiarla)",
    )

    class Meta:
        model = Usuario
        fields = [
            "username",
            "nombre_completo",
            "identificacion",
            "email",
            "rol",
            "is_active",
        ]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "nombre_completo": forms.TextInput(attrs={"class": "form-control"}),
            "identificacion": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "rol": forms.Select(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def save(self, commit=True):
        usuario = super().save(commit=False)
        nueva_pass = self.cleaned_data.get("nueva_password")
        if nueva_pass:
            usuario.set_password(nueva_pass)
        if commit:
            usuario.save()
        return usuario


class RolForm(forms.ModelForm):
    """UTN-06: Formulario para que el SuperAdmin cree y edite roles con permisos granulares (UTN-05)"""

    class Meta:
        model = Rol
        fields = [
            "nombre",
            "descripcion",
            "puede_crear",
            "puede_editar",
            "puede_borrar",
            "puede_ver_reportes",
        ]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "descripcion": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "puede_crear": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "puede_editar": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "puede_borrar": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "puede_ver_reportes": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        }
