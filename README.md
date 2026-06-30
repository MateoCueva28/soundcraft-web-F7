# Proyecto Integrador Base de Datos II
## Soundcraft Web - Fase 4
Interfaz web desarrollada con Django y Python para gestionar la base de datos Soundcraft, una plataforma de streaming musical similar a Spotify. Este proyecto corresponde a la Fase 4 del Proyecto Integrador de la materia Base de Datos II (5481) de la Universidad de las Américas (UDLA).

Grupo 3 — Integrantes:
- Josué Chiriboga
- Mateo Cueva
- Tatiana Fonseca

### Requisitos Previos
Antes de ejecutar el proyecto asegúrate de tener instalado:

- Python
- SQL Server con la base de datos Soundcraft cargada
- ODBC Driver 17 for SQL Server
- Git
- Visual Studio Code (recomendado)

### Instalación y Configuración
*1. Clonar el repositorio*
bashgit clone https://github.com/JosueChiriboga/soundcraft-web.git
cd soundcraft-web
*2. Crear y activar el entorno virtual*
- Windows CMD:
python -m venv venv
venv\Scripts\activate
- Windows PowerShell:
python -m venv venv
venv\Scripts\activate
*3. Instalar dependencias*
pip install django pyodbc mssql-django pillow
*4. Configurar la conexión a SQL Server¨*
Abre el archivo ***soundcraft/settings.py*** y ajusta el bloque DATABASES con los datos de tu instancia:

```python
DATABASES = {
    'default': {
        'ENGINE': 'mssql',
        'NAME': 'Soundcraft',
        'HOST': 'TU_SERVIDOR\\TU_INSTANCIA',  # Ej: MSI\\SQLEXPRESS
        'PORT': '',
        'USER': 'TU_USUARIO',                 # Ej: JosueChiriboga
        'PASSWORD': 'TU_PASSWORD',            # Ej: Josue2026
        'OPTIONS': {
            'driver': 'ODBC Driver 17 for SQL Server',
        },
    }
}
```
Nota: Si usas autenticación de Windows reemplaza USER y PASSWORD por 'trusted_connection': 'yes' dentro de OPTIONS.

*5. Verificar la conexión*
python manage.py check
Debe mostrar: System check identified no issues (0 silenced).
*6. Ejecutar el servidor*
python manage.py runserver
Abre tu navegador en: http://127.0.0.1:8000

### Estructura del Proyecto
```python
soundcraft_web/
├── venv/                        # Entorno virtual (no se sube a GitHub)
├── soundcraft/                  # Configuración principal del proyecto
│   ├── settings.py              # Configuración de Django y base de datos
│   ├── urls.py                  # URLs principales
│   ├── wsgi.py
│   └── asgi.py
├── core/                        # Aplicación principal
│   ├── models.py                # Modelos mapeados a SQL Server
│   ├── views.py                 # Vistas y lógica del backend
│   ├── urls.py                  # URLs de la app
│   └── templatetags/
│       ├── __init__.py
│       └── custom_filters.py    # Filtros personalizados de Django
├── templates/                   # Templates HTML
│   ├── base.html                # Template base con navbar
│   ├── dashboard.html           # Dashboard principal
│   ├── usuarios/
│   │   ├── list.html
│   │   ├── form.html
│   │   └── confirmar_eliminar.html
│   ├── artistas/
│   │   └── list.html
│   ├── canciones/
│   │   └── list.html
│   ├── albumes/
│   │   └── list.html
│   ├── playlists/
│   │   └── list.html
│   ├── reproducciones/
│   │   └── list.html
│   ├── suscripciones/
│   │   └── list.html
│   ├── pagos/
│   │   └── list.html
│   ├── regalias/
│   │   └── list.html
│   └── reportes/
│       └── reportes.html
├── static/                      # Archivos estáticos
│   ├── css/
│   │   └── style.css            # Estilos CSS (tema oscuro)
│   └── js/
│       └── main.js              # JavaScript (búsqueda, gráficas, modal)
├── .gitignore
├── README.md
└── manage.py
```
### Base de Datos
La base de datos Soundcraft está organizada en 5 esquemas en SQL Server:
*Esquema - Tablas*
```python
Seguridad: Usuario, UsuarioCancion, UsuarioArtista
Catalogo: Artista, Album, Cancion, Genero, CancionGenero, Discografia
Streaming: Playlist, PlaylistCancion, Reproduccion
Comercial: Suscripcion
Finanzas: Pago, Regalia
```
El script SQL completo de la base de datos se encuentra en la ENTREGA DE LA FASE 4 del proyecto integrador.

### Funcionalidades
** Dashboard

- Estadísticas generales en tiempo real (usuarios, artistas, canciones, álbumes, playlists, reproducciones, suscripciones, pagos)
- Gráfica de barras con el Top 5 de canciones más reproducidas
- Gráfica de dona con reproducciones por país
- Tabla de últimas 10 reproducciones

*Módulos de Gestión*
```python
Módulo - Funcionalidades
Usuarios: CRUD completo (Crear, Leer, Editar, Eliminar)
Artistas: Listado con discografía y estado
Canciones: Listado con álbum y estado
Álbumes: Listado con artista y fecha de lanzamiento
Playlists: Listado con usuario propietario
Reproducciones: Historial completo ordenado por fecha
Suscripciones: Listado con plan y estado
Pagos: Listado con monto y método de pago
Regalías: Listado por artista con período y reproducciones
```
### Reportes

- Reproducciones por país (gráfica de barras horizontal)
- Ingresos por método de pago (gráfica de pastel)
- Suscripciones por plan (gráfica de dona)
- Top 10 canciones más reproducidas (tabla)

### JavaScript

- Búsqueda en tiempo real en la tabla de usuarios
- Gráficas interactivas con Chart.js en Dashboard y Reportes
- Modal de confirmación al eliminar usuarios

### Tecnologías Utilizadas
```python
Tecnología - Versión - Uso
Python 3.11.7 Lenguaje backend
Django 5.2.14 Framework web
mssql-django 1.7.2 Conector SQL Server
pyodbc 5.3.0 Driver ODBC
Chart.js Latest CDN Gráficas interactivas
SQL Server 2022 Base de datos
ODBC Driver 17 Conexión ODBC
```
### Dependencias
```python
django==5.2.14
mssql-django==1.7.2
pyodbc==5.3.0
pillow==12.2.0
```
Instalar todas con:
pip install django pyodbc mssql-django pillow

### Variables de Configuración Importantes
En soundcraft/settings.py:
```python
pythonDEBUG = True          # Cambiar a False en producción
ALLOWED_HOSTS = []    # Agregar el host en producción
SECRET_KEY = '...'    # Cambiar en producción
```
### Capturas de Pantalla
```python
**Vista - Descripción
Dashboard: Estadísticas generales y gráficas
Usuarios: CRUD completo con búsqueda y modal
Reportes: 4 gráficas interactivas con Chart.js
```
### Notas para Colaboradores

1. No subas la carpeta venv/ al repositorio
2. No subas el archivo settings.py con credenciales reales — usa variables de entorno en producción
3. Cada colaborador debe configurar su propio settings.py con su instancia de SQL Server
4. Para modificar el frontend, los archivos relevantes son:
```python
static/css/style.css — estilos
static/js/main.js — JavaScript
templates/ — templates HTML
```
Después de clonar, siempre activa el entorno virtual antes de trabajar:

venv\Scripts\activate

### Referencias
```python
Documentación oficial de Django
mssql-django en PyPI
Chart.js
ODBC Driver 17 for SQL Server
```

### Información Académica

- Universidad: Universidad de las Américas (UDLA)
- Materia: Base de Datos II — 5481
- Fase: 4 — Interfaz Web
- Grupo: 3
