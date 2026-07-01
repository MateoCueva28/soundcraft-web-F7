# Proyecto Integrador Base de Datos II
## Soundcraft Web — Fase 7

Panel de administración web desarrollado con Django y Python para gestionar la base de datos **Soundcraft**, una plataforma de streaming musical similar a Spotify. Este proyecto corresponde a la **Fase 7** del Proyecto Integrador de la materia **Base de Datos II (ITIZ-2201)** de la Universidad de las Américas (UDLA).

**Grupo 3 — Integrantes:**
- Josué Chiriboga
- Mateo Cueva
- Tatiana Fonseca

---

## Tecnologías

| Tecnología | Versión | Uso |
|---|---|---|
| Python | 3.11 | Lenguaje backend |
| Django | 5.2.15 | Framework web |
| PyMongo | 4.17.0 | Driver de MongoDB |
| dnspython | 2.8.0 | Resolución DNS para conexiones `mongodb+srv://` |
| python-dotenv | 1.2.2 | Carga de variables de entorno desde `.env` |
| MongoDB Atlas | — | Base de datos NoSQL en la nube |
| Chart.js | CDN | Gráficas interactivas |

> **Sin Django ORM, sin SQL Server.** La capa de datos usa PyMongo directamente contra MongoDB Atlas. El archivo `core/models.py` existe únicamente para que Django gestione sus tablas internas (sesiones) en SQLite local, pero toda la lógica de negocio consulta MongoDB vía `core/db_config.py`.

---

## Requisitos Previos

- Python 3.11
- Git
- Acceso a la cadena de conexión de MongoDB Atlas (`MONGO_URI`)
- Visual Studio Code (recomendado)

---

## Instalación y Configuración

### 1. Clonar el repositorio

```bash
git clone https://github.com/MateoCueva28/soundcraft-web-F7.git
cd soundcraft-web-F7
```

### 2. Crear y activar el entorno virtual

```bash
# Crear
python -m venv venv

# Activar — Windows CMD
venv\Scripts\activate

# Activar — Windows PowerShell
venv\Scripts\Activate.ps1
```

> **Gotcha frecuente:** si olvidas activar el entorno virtual antes de arrancar el servidor, la conexión a MongoDB falla silenciosamente (`db = None`) y el panel muestra tablas vacías sin ningún error visible en el navegador. Siempre activa el entorno primero.

### 3. Instalar dependencias

```bash
pip install django pymongo dnspython python-dotenv
```

### 4. Configurar la conexión a MongoDB Atlas

Crea un archivo **`.env`** en la raíz del proyecto (junto a `manage.py`) con el siguiente contenido:

```env
# Cadena de conexión a la base de datos MongoDB Atlas
MONGO_URI=mongodb+srv://<usuario>:<password>@<cluster>.mongodb.net/Soundcraft?retryWrites=true&w=majority
```

El archivo `.env` ya está en `.gitignore`; nunca lo subas al repositorio.

### 5. Verificar la conexión

```bash
python manage.py check
```

Si MongoDB Atlas responde correctamente, la consola mostrará:
```
¡Conexión exitosa a MONGODB ATLAS establecida correctamente!
System check identified N issues (0 silenced).
```
(Los N issues son avisos de Django sobre ForeignKey en modelos internos; no afectan el funcionamiento.)

### 6. Ejecutar el servidor

```bash
python manage.py runserver
```

Abre tu navegador en: **http://127.0.0.1:8000**

---

## Estructura del Proyecto

```
soundcraft-web-F7/
├── venv/                        # Entorno virtual (excluido de git)
├── soundcraft/                  # Configuración principal de Django
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py / asgi.py
├── core/                        # Aplicación principal
│   ├── db_config.py             # Conexión a MongoDB Atlas vía PyMongo
│   ├── views.py                 # Vistas y lógica del backend (sin ORM)
│   └── urls.py                  # Rutas de la app
├── templates/                   # Templates HTML
│   ├── base.html                # Template base con navbar
│   ├── dashboard.html
│   ├── login.html
│   ├── usuarios/                # list, form, confirmar_eliminar
│   ├── artistas/                # list
│   ├── canciones/               # list (track list + modal)
│   ├── playlists/               # list (grid + modal)
│   ├── reproducciones/          # list
│   ├── suscripciones/           # list
│   ├── pagos/                   # list
│   ├── regalias/                # list
│   └── reportes/                # reportes.html
├── static/
│   ├── css/style.css            # Estilos (tema oscuro)
│   └── js/main.js               # Búsqueda, gráficas, modales
├── .env                         # Variables de entorno (excluido de git)
├── .gitignore
├── manage.py
└── README.md
```

---

## Base de Datos

Base de datos **`Soundcraft`** en MongoDB Atlas. No hay esquemas relacionales; los datos usan documentos con campos embebidos donde corresponde.

| Colección | Campos relevantes / Estructura |
|---|---|
| `usuario` | `nombreUsuario`, `correoUsuario`, `contraseniaUsuario`, `tipoUsuario`, ... |
| `artista` | `nombreArtistica`, `estadoArtista`; objeto `discografia` embebido: `nombreDiscografia`, `paisOrigen`, `correoArtista` |
| `cancion` | `tituloCancion`, `duracionCancion`, `numeroPistaCancion`, `estadoCancion`; array `generos` de strings; objeto `album` embebido: `tituloAlbum`, `nombreArtista`, `fechaLanzamiento` |
| `album` | `tituloAlbum`, `fechaLanzamiento`, `artistaId` — colección existente en Atlas; los datos de álbum se acceden principalmente vía el objeto embebido en `cancion`, no como módulo independiente |
| `playlists` | `nombrePlaylist`, `estadoPlaylist`, `usuarioId`; array `canciones` embebido con los tracks de la playlist |
| `reproduccion` | `cancionId`, `tituloCancion` (embebido), `nombreUsuario` (embebido), `paisReproduccion`, `fechaReproduccion` |
| `suscripcion` | `tipoPlanSuscripcion`, `estadoSuscripcion`, `fechaInicioSuscripcion`, `nombreUsuario` (embebido) |
| `pago` | `metodoPago`, `montoPago`, `fechaPago`, `nombreUsuario` (embebido), `tipoPlan` (embebido) |
| `regalia` | `nombreArtista` (embebido), `periodoRegalia` (ej. `"2026-01"`), `totalReproduccionesRegalia`, `artistaId` |

---

## Funcionalidades

### Dashboard
- Contadores en tiempo real: usuarios, artistas, canciones, álbumes, playlists, reproducciones, suscripciones, pagos
- Gráfica de barras con el Top 5 de canciones más reproducidas
- Gráfica de dona con reproducciones por país (top 10)
- Tabla de últimas 10 reproducciones con fecha, usuario y canción

### Módulos de Gestión

| Módulo | Funcionalidades |
|---|---|
| **Login / Logout** | Autenticación contra la colección `usuario` de MongoDB; sesión gestionada por Django |
| **Usuarios** | CRUD completo (crear, leer, editar, eliminar con confirmación) y búsqueda en tiempo real |
| **Artistas** | Listado de solo lectura con discografía embebida (nombre, país, correo) y búsqueda |
| **Canciones** | Track list estilo Spotify (no tabla); clic en cualquier fila abre un modal de detalle con álbum, pista, duración, géneros y estado; búsqueda por título o artista |
| **Playlists** | Cuadrícula de tarjetas estilo Spotify; clic abre modal de detalle con lista de tracks; acciones de moderación: suspender/activar y eliminar (la edición de contenido corresponde al usuario final, no al administrador) |
| **Reproducciones** | Historial completo con búsqueda |
| **Suscripciones** | Listado con plan, estado y fecha de inicio; búsqueda |
| **Pagos** | Listado con usuario, método, monto y estado; búsqueda |
| **Regalías** | Listado por artista con período y reproducciones; búsqueda |

### Reportes

Módulo que cubre los cuatro reportes del Caso de Uso 12 del proyecto. Los datos se cargan una vez desde MongoDB y el filtrado ocurre en el cliente (JavaScript), sin recargar la página.

| Reporte | Gráfica | Filtros disponibles |
|---|---|---|
| Reproducciones por País | Barras horizontal | Rango de fechas (`fechaReproduccion`) |
| Ingresos por Método de Pago | Pastel | Rango de fechas (`fechaPago`) |
| Suscripciones por Plan | Dona | Rango de fechas (`fechaInicioSuscripcion`) + estado (Activa / Cancelada / ...) |
| Regalías por Artista | Barras horizontal | Período (`periodoRegalia`) + artista |

Cada gráfica muestra "No hay datos para este filtro." si el filtro no produce resultados.

---

## JavaScript (`static/js/main.js`)

- Búsqueda en tiempo real: disponible en todos los módulos de listado
- `initDashboardCharts()`: gráficas del dashboard (barras Top 5 + dona por país)
- `initReportesCharts()`: motor de filtrado y redibujado de las 4 gráficas de reportes con Chart.js
- `initPlaylistGrid()`: cuadrícula de playlists, apertura de modal, toggle de estado vía fetch, eliminación con texto de moderación personalizado
- `initCancionesTrackList()`: track list de canciones con colores por id, formateo de duración y apertura de modal
- `initDeleteModal()`: confirmación genérica de eliminación (usado en usuarios)

---

## Notas para Colaboradores

1. **No subas `venv/`** al repositorio — está en `.gitignore`
2. **No subas `.env`** — contiene la cadena de conexión a MongoDB Atlas; está en `.gitignore`
3. Cada colaborador configura su propio `.env` con su `MONGO_URI`
4. **Activa el entorno virtual antes de trabajar:**
   ```bash
   venv\Scripts\activate
   ```
5. Para modificar el frontend, los archivos relevantes son:
   - `static/css/style.css` — estilos
   - `static/js/main.js` — JavaScript
   - `templates/` — templates HTML

---

## Variables de Configuración Importantes

En `soundcraft/settings.py`:

```python
DEBUG = True          # Cambiar a False en producción
ALLOWED_HOSTS = []    # Agregar el host en producción
SECRET_KEY = '...'    # Cambiar en producción
```

---

## Información Académica

- **Universidad:** Universidad de las Américas (UDLA)
- **Materia:** Base de Datos II — ITIZ-2201
- **Fase:** 7 — Panel de Administración Web (MongoDB)
- **Grupo:** 3
