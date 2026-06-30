from datetime import datetime

from bson import ObjectId
from bson.errors import InvalidId
from django.contrib import messages
from django.shortcuts import redirect, render

from .db_config import db


def _parse_datetime(value):
    if not value:
        return datetime.now()
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        value = value.strip()
        for fmt in ['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d']:
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        try:
            return datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            return datetime.now()
    return datetime.now()


def _normalize_document(document, id_field):
    if not isinstance(document, dict):
        return {}
    normalized = dict(document)
    if '_id' in normalized:
        normalized['id_str'] = str(normalized['_id'])
        if id_field and id_field not in normalized:
            original_id = normalized.get('_id')
            normalized[id_field] = str(original_id)
    return normalized


def _load_documents(collection_name, id_field):
    if db is None:
        return []
    documents = list(db[collection_name].find())
    return [_normalize_document(doc, id_field) for doc in documents]


def _coerce_object_id(value):
    if not value:
        return None
    if isinstance(value, ObjectId):
        return value
    try:
        return ObjectId(str(value))
    except InvalidId:
        return None


def _build_top_canciones(limit=5):
    if db is None:
        return []
    pipeline = [
        {'$group': {'_id': '$Cancion_idCancion', 'total': {'$sum': 1}}},
        {'$sort': {'total': -1}},
        {'$limit': limit},
    ]
    resultados = []
    for item in db['reproduccion'].aggregate(pipeline):
        song_id = item.get('_id')
        titulo = 'Sin título'
        if song_id:
            song = None
            object_id = _coerce_object_id(song_id)
            if object_id:
                song = db['cancion'].find_one({'_id': object_id})
            if not song:
                song = db['cancion'].find_one({'idCancion': song_id})
            if song:
                titulo = song.get('tituloCancion', 'Sin título')
        resultados.append({'tituloCancion': titulo, 'total': item.get('total', 0)})
    return resultados


# ============================================================
# LOGIN
# ============================================================
def login_view(request):
    if request.method == 'POST':
        correo = request.POST.get('correoUsuario', '')
        contrasenia = request.POST.get('contraseniaUsuario', '')
        if db is None:
            messages.error(request, 'No hay conexión disponible a MongoDB Atlas.')
            return render(request, 'login.html', {})

        usuario = db['usuario'].find_one({
            'correoUsuario': correo,
            'contraseniaUsuario': contrasenia,
        })
        if usuario:
            request.session['usuario_id'] = str(usuario['_id'])
            request.session['nombreUsuario'] = usuario.get('nombreUsuario', '')
            messages.success(request, 'Inicio de sesión exitoso.')
            return redirect('dashboard')

        messages.error(request, 'Credenciales inválidas.')
    return render(request, 'login.html', {})


# ============================================================
# DASHBOARD
# ============================================================
def dashboard(request):
    if not request.session.get('usuario_id'):
        messages.error(request, 'Debes iniciar sesión para acceder al dashboard.')
        return redirect('login_view')

    if db is None:
        context = {
            'total_usuarios': 0,
            'total_artistas': 0,
            'total_canciones': 0,
            'total_albumes': 0,
            'total_playlists': 0,
            'total_reproducciones': 0,
            'total_suscripciones': 0,
            'total_pagos': 0,
            'ultimas_reproducciones': [],
            'top_canciones': [],
            'reproducciones_por_pais': [],
        }
        return render(request, 'dashboard.html', context)

    context = {
        'total_usuarios': db['usuario'].count_documents({}),
        'total_artistas': db['artista'].count_documents({}),
        'total_canciones': db['cancion'].count_documents({}),
        'total_albumes': db['album'].count_documents({}),
        'total_playlists': db['playlists'].count_documents({}),
        'total_reproducciones': db['reproduccion'].count_documents({}),
        'total_suscripciones': db['suscripcion'].count_documents({}),
        'total_pagos': db['pago'].count_documents({}),
        'ultimas_reproducciones': [
            _normalize_document(doc, 'idReproduccion')
            for doc in list(db['reproduccion'].find().sort('fechaReproduccion', -1).limit(10))
        ],
        'top_canciones': _build_top_canciones(limit=5),
        'reproducciones_por_pais': [
            {'paisReproduccion': item['_id'], 'total': item['total']}
            for item in db['reproduccion'].aggregate([
                {'$group': {'_id': '$paisReproduccion', 'total': {'$sum': 1}}},
                {'$sort': {'total': -1}},
                {'$limit': 10},
            ])
        ],
    }
    return render(request, 'dashboard.html', context)


# ============================================================
# USUARIOS
# ============================================================
def usuario_list(request):
    usuarios = _load_documents('usuario', 'idUsuario')
    return render(request, 'usuarios/list.html', {'usuarios': usuarios})


def usuario_crear(request):
    if request.method == 'POST':
        try:
            documento = {
                'nombreUsuario': request.POST.get('nombreUsuario', ''),
                'apellidoUsuario': request.POST.get('apellidoUsuario', ''),
                'correoUsuario': request.POST.get('correoUsuario', ''),
                'contraseniaUsuario': request.POST.get('contraseniaUsuario', ''),
                'fechaRegistroUsuario': _parse_datetime(request.POST.get('fechaRegistroUsuario')),
                'paisUsuario': request.POST.get('paisUsuario', ''),
                'tipoUsuario': request.POST.get('tipoUsuario', ''),
                'estadoCuentaUsuario': request.POST.get('estadoCuentaUsuario', ''),
            }
            db['usuario'].insert_one(documento)
            messages.success(request, 'Usuario creado exitosamente.')
            return redirect('usuario_list')
        except Exception as e:
            messages.error(request, f'Error: {e}')
    return render(request, 'usuarios/form.html', {'accion': 'Crear'})


def usuario_editar(request, pk):
    object_id = _coerce_object_id(pk)
    usuario = db['usuario'].find_one({'_id': object_id}) if object_id else None
    if not usuario:
        messages.error(request, 'Usuario no encontrado.')
        return redirect('usuario_list')

    if request.method == 'POST':
        try:
            cambios = {
                'nombreUsuario': request.POST.get('nombreUsuario', ''),
                'apellidoUsuario': request.POST.get('apellidoUsuario', ''),
                'correoUsuario': request.POST.get('correoUsuario', ''),
                'contraseniaUsuario': request.POST.get('contraseniaUsuario', ''),
                'fechaRegistroUsuario': _parse_datetime(request.POST.get('fechaRegistroUsuario')),
                'paisUsuario': request.POST.get('paisUsuario', ''),
                'tipoUsuario': request.POST.get('tipoUsuario', ''),
                'estadoCuentaUsuario': request.POST.get('estadoCuentaUsuario', ''),
            }
            db['usuario'].update_one({'_id': object_id}, {'$set': cambios})
            messages.success(request, 'Usuario actualizado exitosamente.')
            return redirect('usuario_list')
        except Exception as e:
            messages.error(request, f'Error: {e}')
    return render(request, 'usuarios/form.html', {'accion': 'Editar', 'usuario': _normalize_document(usuario, 'idUsuario')})


def usuario_eliminar(request, pk):
    object_id = _coerce_object_id(pk)
    usuario = db['usuario'].find_one({'_id': object_id}) if object_id else None
    if not usuario:
        messages.error(request, 'Usuario no encontrado.')
        return redirect('usuario_list')

    if request.method == 'POST':
        try:
            db['usuario'].delete_one({'_id': object_id})
            messages.success(request, 'Usuario eliminado exitosamente.')
            return redirect('usuario_list')
        except Exception as e:
            messages.error(request, f'Error al eliminar: {e}')
    return render(request, 'usuarios/confirmar_eliminar.html', {'usuario': _normalize_document(usuario, 'idUsuario')})


# ============================================================
# ARTISTAS
# ============================================================
def artista_list(request):
    artistas = _load_documents('artista', 'idArtista')
    return render(request, 'artistas/list.html', {'artistas': artistas})


# ============================================================
# CANCIONES
# ============================================================
def cancion_list(request):
    canciones = _load_documents('cancion', 'idCancion')
    return render(request, 'canciones/list.html', {'canciones': canciones})


# ============================================================
# ÁLBUMES
# ============================================================
def album_list(request):
    albumes = _load_documents('album', 'idAlbum')
    return render(request, 'albumes/list.html', {'albumes': albumes})


# ============================================================
# PLAYLISTS
# ============================================================
def playlist_list(request):
    playlists = _load_documents('playlists', 'idPlaylist')
    return render(request, 'playlists/list.html', {'playlists': playlists})


# ============================================================
# REPRODUCCIONES
# ============================================================
def reproduccion_list(request):
    reproducciones = _load_documents('reproduccion', 'idReproduccion')
    return render(request, 'reproducciones/list.html', {'reproducciones': reproducciones})


# ============================================================
# SUSCRIPCIONES
# ============================================================
def suscripcion_list(request):
    suscripciones = _load_documents('suscripcion', 'idSuscripcion')
    return render(request, 'suscripciones/list.html', {'suscripciones': suscripciones})


# ============================================================
# PAGOS
# ============================================================
def pago_list(request):
    pagos = _load_documents('pago', 'idPago')
    return render(request, 'pagos/list.html', {'pagos': pagos})


# ============================================================
# REGALÍAS
# ============================================================
def regalia_list(request):
    regalias = _load_documents('regalia', 'idRegalia')
    return render(request, 'regalias/list.html', {'regalias': regalias})


# ============================================================
# REPORTES
# ============================================================
def reportes(request):
    if db is None:
        context = {
            'reproducciones_por_pais': [],
            'top_canciones': [],
            'ingresos_por_metodo': [],
            'suscripciones_por_plan': [],
        }
        return render(request, 'reportes/reportes.html', context)

    reproducciones_por_pais = [
        {'paisReproduccion': item['_id'], 'total': item['total']}
        for item in db['reproduccion'].aggregate([
            {'$group': {'_id': '$paisReproduccion', 'total': {'$sum': 1}}},
            {'$sort': {'total': -1}},
        ])
    ]
    top_canciones = _build_top_canciones(limit=10)
    ingresos_por_metodo = [
        {'metodoPago': item['_id'], 'total': item['total']}
        for item in db['pago'].aggregate([
            {'$group': {'_id': '$metodoPago', 'total': {'$sum': '$montoPago'}}},
            {'$sort': {'total': -1}},
        ])
    ]
    suscripciones_por_plan = [
        {'tipoPlanSuscripcion': item['_id'], 'total': item['total']}
        for item in db['suscripcion'].aggregate([
            {'$group': {'_id': '$tipoPlanSuscripcion', 'total': {'$sum': 1}}},
            {'$sort': {'total': -1}},
        ])
    ]
    context = {
        'reproducciones_por_pais': reproducciones_por_pais,
        'top_canciones': top_canciones,
        'ingresos_por_metodo': ingresos_por_metodo,
        'suscripciones_por_plan': suscripciones_por_plan,
    }
    return render(request, 'reportes/reportes.html', context)