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
