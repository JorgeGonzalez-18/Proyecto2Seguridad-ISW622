# Sistema de Reserva de Salas y Laboratorios

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.14-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.1.15-success.svg)](https://www.djangoproject.com/)
[![Security](https://img.shields.io/badge/Security-Argon2id%20%7C%20RBAC%20%7C%20CSP-red.svg)]()
[![Tests](https://img.shields.io/badge/Tests-Pytest%20Django-orange.svg)]()

**Curso:** ISW-622 Pruebas de Software — III Cuatrimestre 2026  
**Proyecto 2:** Construcción, Aseguramiento y Pentest de un Sistema Web Seguro  
**Dominio:** Reserva de Salas y Laboratorios  
**Equipo de Desarrollo:** Blue Team

---

## Descripción del Proyecto

Aplicación web empresarial construida para gestionar el catálogo y la reserva de salas y laboratorios de un campus universitario. El sistema fue diseñado siguiendo el principio de **Defensa en Profundidad (Defense in Depth)**, asegurando la aplicación contra las vulnerabilidades más comunes del **OWASP Top 10** (Inyección SQL, Cross-Site Scripting XSS, Cross-Site Request Forgery CSRF, y Fallos en el Control de Acceso).

### Dominio 4: Reglas y Objetivos

- **Entidad Principal:** `Reserva` (Código alfanumérico, sala, solicitante, fecha, hora inicio, hora fin, estado).
- **Entidad de Soporte:** `Sala / Laboratorio` (Nombre, capacidad, equipo disponible, estado).
- **Rol Operativo:** `Gestor de reservas`.
- **Dato Sensible a Proteger (Objetivo Red Team):** Datos personales de los solicitantes y calendario detallado de ocupación de salas.

---

## Stack Tecnológico Utilizado

- **Lenguaje:** Python (3.11+ / 3.14)
- **Framework Web:** Django 5.1 (Arquitectura MVT con prevención nativa de SQLi y XSS)
- **Hashing de Contraseñas:** `Argon2id` (vía `argon2-cffi`, costo y sal criptográfica de alta seguridad)
- **Base de Datos:** SQLite (desarrollo local) / PostgreSQL (ambiente de producción)
- **Protección Web:** `django-csp` (Content Security Policy estricto), Middlewares de sesión y anti-Clickjacking
- **Suite de Pruebas:** `pytest-django`, `pytest-html` (reportes HTML automatizados)
- **Interfaz de Usuario:** HTML5 semántico, Bootstrap 5.3 (sin scripts inline inseguros)

---

## Instalación y Puesta en Marcha Local

### Prerrequisitos

- **Python:** Versión 3.11, 3.12 o 3.14 instalada.
- **Git:** Para clonar el repositorio.

### Paso 1: Clonar el Repositorio

```bash
git clone https://github.com/JorgeGonzalez-18/Proyecto2Seguridad-ISW622.git
cd Proyecto2Seguridad-ISW622
```

### Paso 2: Crear y Activar el Entorno Virtual (`venv`)

- **En Windows (CMD / PowerShell):**
  ```powershell
  py -m venv venv
  .\venv\Scripts\activate
  ```
- **En Linux / macOS:**
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

### Paso 3: Instalar Dependencias

Con el entorno `(venv)` activo:

```bash
pip install -r requirements.txt
```

### Paso 4: Configurar Variables de Entorno

Copiar la plantilla de configuración `.env.example` a un archivo `.env`:

- **Windows:**
  ```cmd
  copy .env.example .env
  ```
- **Linux / macOS:**
  ```bash
  cp .env.example .env
  ```
  _(El archivo `.env` permite configurar `DEBUG`, `SECRET_KEY`, `ALLOWED_HOSTS` y `DATABASE_URL` de forma aislada sin exponer credenciales)._

### Paso 5: Aplicar Migraciones y Cargar Semillas de Datos

```bash
# Crear las tablas en la base de datos relacional
python manage.py migrate

# Cargar los 3 roles iniciales (SuperAdmin, Auditor, Gestor de reservas) y usuario admin
python manage.py crear_roles
```

### Paso 6: Iniciar el Servidor de Desarrollo

```bash
python manage.py runserver
```

Acceder en el navegador a: `http://127.0.0.1:8000/`
