from datetime import datetime

from bson import ObjectId
from bson.errors import InvalidId
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, render

from .db_config import db


# ============================================================
# HELPERS PRIVADOS
# ============================================================
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
            normalized[id_field] = str(normalized['_id'])
    # Convierte strings ISO fecha a datetime para que el filtro |date de Django funcione.
    # Detecta el patrón AAAA-MM-DD sin tocar campos de texto normales.
    for key, value in list(normalized.items()):
        if isinstance(value, str) and len(value) >= 10 and value[4:5] == '-' and value[7:8] == '-':
            try:
                normalized[key] = _parse_datetime(value)
            except Exception:
                pass
    return normalized


def _load_documents(collection_name, id_field):
    if db is None:
        return []
    return [_normalize_document(doc, id_field) for doc in db[collection_name].find()]


def _coerce_object_id(value):
    if not value:
        return None
    if isinstance(value, ObjectId):
        return value
    try:
        return ObjectId(str(value))
    except InvalidId:
        return None


def _find_by_id(collection_name, id_value, legacy_field=None):
    """Busca un documento probando en orden: ObjectId hex, _id entero, campo heredado."""
    if db is None or id_value is None:
        return None
    doc = None
    # 1. Intentar como ObjectId (documentos creados nativamente en MongoDB)
    oid = _coerce_object_id(id_value)
    if oid:
        doc = db[collection_name].find_one({'_id': oid})
    # 2. Intentar _id como entero (PKs migrados desde SQL Server)
    if not doc:
        try:
            doc = db[collection_name].find_one({'_id': int(id_value)})
        except (ValueError, TypeError):
            pass
    # 3. Intentar campo heredado como string o entero
    if not doc and legacy_field:
        doc = db[collection_name].find_one({legacy_field: id_value})
        if not doc:
            try:
                doc = db[collection_name].find_one({legacy_field: int(id_value)})
            except (ValueError, TypeError):
                pass
    return doc


def _serialize_doc(doc):
    """Convierte ObjectId y datetime a tipos JSON-seguros de forma recursiva."""
    if isinstance(doc, dict):
        return {k: _serialize_doc(v) for k, v in doc.items()}
    if isinstance(doc, list):
        return [_serialize_doc(v) for v in doc]
    if isinstance(doc, ObjectId):
        return str(doc)
    if isinstance(doc, datetime):
        return doc.isoformat()
    return doc


def _require_session(request):
    """Retorna un redirect al login si el usuario no tiene sesión activa."""
    if not request.session.get('usuario_id'):
        messages.error(request, 'Debes iniciar sesión para acceder.')
        return redirect('login_view')
    return None


def _build_top_canciones(limit=5):
    if db is None:
        return []
    # tituloCancion ya está embebido en cada documento de reproduccion;
    # agrupamos por cancionId y tomamos el primer título que aparezca.
    pipeline = [
        {
            '$group': {
                '_id': '$cancionId',
                'total': {'$sum': 1},
                'tituloCancion': {'$first': '$tituloCancion'},
            }
        },
        {'$sort': {'total': -1}},
        {'$limit': limit},
        {
            '$project': {
                'tituloCancion': {'$ifNull': ['$tituloCancion', 'Sin título']},
                'total': 1,
            }
        },
    ]
    return [
        {'tituloCancion': item.get('tituloCancion', 'Sin título'), 'total': item['total']}
        for item in db['reproduccion'].aggregate(pipeline)
    ]


# ============================================================
# LOGIN / LOGOUT
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


def logout_view(request):
    request.session.flush()
    messages.success(request, 'Sesión cerrada exitosamente.')
    return redirect('login_view')


# ============================================================
# DASHBOARD
# ============================================================
def dashboard(request):
    redir = _require_session(request)
    if redir:
        return redir

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

    # Los documentos de reproduccion ya tienen nombreUsuario y tituloCancion
    # embebidos desde la migración; $ifNull cubre cualquier registro incompleto.
    ultimas_pipeline = [
        {'$sort': {'fechaReproduccion': -1}},
        {'$limit': 10},
        {
            '$addFields': {
                'nombreUsuario': {'$ifNull': ['$nombreUsuario', 'Desconocido']},
                'tituloCancion': {'$ifNull': ['$tituloCancion', 'Sin título']},
            }
        },
    ]

    ultimas_reproducciones = []
    for doc in db['reproduccion'].aggregate(ultimas_pipeline):
        doc['id_str'] = str(doc.get('_id', ''))
        if isinstance(doc.get('fechaReproduccion'), str):
            doc['fechaReproduccion'] = _parse_datetime(doc['fechaReproduccion'])
        ultimas_reproducciones.append(doc)

    context = {
        'total_usuarios': db['usuario'].count_documents({}),
        'total_artistas': db['artista'].count_documents({}),
        'total_canciones': db['cancion'].count_documents({}),
        'total_albumes': db['album'].count_documents({}),
        'total_playlists': db['playlists'].count_documents({}),
        'total_reproducciones': db['reproduccion'].count_documents({}),
        'total_suscripciones': db['suscripcion'].count_documents({}),
        'total_pagos': db['pago'].count_documents({}),
        'ultimas_reproducciones': ultimas_reproducciones,
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
    redir = _require_session(request)
    if redir:
        return redir
    usuarios = _load_documents('usuario', 'idUsuario')
    return render(request, 'usuarios/list.html', {'usuarios': usuarios})


def usuario_crear(request):
    redir = _require_session(request)
    if redir:
        return redir
    if request.method == 'POST':
        try:
            ultimo = db['usuario'].find_one(
                {'_id': {'$type': ['int', 'long']}},
                sort=[('_id', -1)],
            )
            next_id = (ultimo['_id'] + 1) if ultimo else 1
            documento = {
                '_id': next_id,
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
    redir = _require_session(request)
    if redir:
        return redir
    usuario = _find_by_id('usuario', pk, 'idUsuario')
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
            db['usuario'].update_one({'_id': usuario['_id']}, {'$set': cambios})
            messages.success(request, 'Usuario actualizado exitosamente.')
            return redirect('usuario_list')
        except Exception as e:
            messages.error(request, f'Error: {e}')
    return render(request, 'usuarios/form.html', {
        'accion': 'Editar',
        'usuario': _normalize_document(usuario, 'idUsuario'),
    })


def usuario_eliminar(request, pk):
    redir = _require_session(request)
    if redir:
        return redir
    usuario = _find_by_id('usuario', pk, 'idUsuario')
    if not usuario:
        messages.error(request, 'Usuario no encontrado.')
        return redirect('usuario_list')

    if request.method == 'POST':
        try:
            db['usuario'].delete_one({'_id': usuario['_id']})
            messages.success(request, 'Usuario eliminado exitosamente.')
            return redirect('usuario_list')
        except Exception as e:
            messages.error(request, f'Error al eliminar: {e}')
    return render(request, 'usuarios/confirmar_eliminar.html', {
        'usuario': _normalize_document(usuario, 'idUsuario'),
    })


# ============================================================
# ARTISTAS
# ============================================================
def artista_list(request):
    redir = _require_session(request)
    if redir:
        return redir
    artistas = _load_documents('artista', 'idArtista')
    return render(request, 'artistas/list.html', {'artistas': artistas})


# ============================================================
# CANCIONES
# ============================================================
def cancion_list(request):
    redir = _require_session(request)
    if redir:
        return redir
    canciones = _load_documents('cancion', 'idCancion')
    return render(request, 'canciones/list.html', {'canciones': canciones})


# ============================================================
# PLAYLISTS
# ============================================================
def playlist_list(request):
    redir = _require_session(request)
    if redir:
        return redir
    playlists = _load_documents('playlists', 'idPlaylist')
    # Enriquecer con nombreUsuario buscando los usuarios únicos en una sola consulta
    if db is not None and playlists:
        ids = list({p.get('usuarioId') for p in playlists if p.get('usuarioId') is not None})
        usuarios = {u['_id']: u.get('nombreUsuario', '') for u in db['usuario'].find({'_id': {'$in': ids}}, {'nombreUsuario': 1})}
        for p in playlists:
            p['nombreUsuario'] = usuarios.get(p.get('usuarioId'), '—')
    return render(request, 'playlists/list.html', {'playlists': playlists})


# ============================================================
# REPRODUCCIONES
# ============================================================
def reproduccion_list(request):
    redir = _require_session(request)
    if redir:
        return redir
    reproducciones = _load_documents('reproduccion', 'idReproduccion')
    return render(request, 'reproducciones/list.html', {'reproducciones': reproducciones})


# ============================================================
# SUSCRIPCIONES
# ============================================================
def suscripcion_list(request):
    redir = _require_session(request)
    if redir:
        return redir
    suscripciones = _load_documents('suscripcion', 'idSuscripcion')
    return render(request, 'suscripciones/list.html', {'suscripciones': suscripciones})


# ============================================================
# PAGOS
# ============================================================
def pago_list(request):
    redir = _require_session(request)
    if redir:
        return redir
    pagos = _load_documents('pago', 'idPago')
    return render(request, 'pagos/list.html', {'pagos': pagos})


# ============================================================
# REGALÍAS
# ============================================================
def regalia_list(request):
    redir = _require_session(request)
    if redir:
        return redir
    regalias = _load_documents('regalia', 'idRegalia')
    return render(request, 'regalias/list.html', {'regalias': regalias})


# ============================================================
# REPORTES
# ============================================================
def reportes(request):
    redir = _require_session(request)
    if redir:
        return redir

    if db is None:
        context = {
            'reproducciones_por_pais': [],
            'top_canciones': [],
            'ingresos_por_metodo': [],
            'suscripciones_por_plan': [],
        }
        return render(request, 'reportes/reportes.html', context)

    reproducciones_por_pais = [
        {'paisReproduccion': item['_id'] or 'Desconocido', 'total': item['total']}
        for item in db['reproduccion'].aggregate([
            {'$group': {'_id': '$paisReproduccion', 'total': {'$sum': 1}}},
            {'$sort': {'total': -1}},
        ])
    ]
    ingresos_por_metodo = [
        {'metodoPago': item['_id'] or 'Sin método', 'total': round(item['total'], 2)}
        for item in db['pago'].aggregate([
            {'$group': {'_id': '$metodoPago', 'total': {'$sum': '$montoPago'}}},
            {'$sort': {'total': -1}},
        ])
    ]
    suscripciones_por_plan = [
        {'tipoPlanSuscripcion': item['_id'] or 'Sin plan', 'total': item['total']}
        for item in db['suscripcion'].aggregate([
            {'$group': {'_id': '$tipoPlanSuscripcion', 'total': {'$sum': 1}}},
            {'$sort': {'total': -1}},
        ])
    ]
    context = {
        'reproducciones_por_pais': reproducciones_por_pais,
        'top_canciones': _build_top_canciones(limit=10),
        'ingresos_por_metodo': ingresos_por_metodo,
        'suscripciones_por_plan': suscripciones_por_plan,
    }
    return render(request, 'reportes/reportes.html', context)


# ============================================================
# API INTERNA — DETALLE JSON
# ============================================================
_COLECCIONES_VALIDAS = {
    'cancion': ('cancion', 'idCancion'),
    'artista': ('artista', 'idArtista'),
    'album': ('album', 'idAlbum'),
    'playlist': ('playlists', 'idPlaylist'),
}


def obtener_detalle_json(request, tipo, id_entidad):
    if db is None:
        return JsonResponse({'error': 'Sin conexión a la base de datos.'}, status=503)
    if tipo not in _COLECCIONES_VALIDAS:
        return JsonResponse({'error': f'Tipo "{tipo}" no válido.'}, status=400)

    collection_name, legacy_field = _COLECCIONES_VALIDAS[tipo]
    doc = _find_by_id(collection_name, id_entidad, legacy_field)
    if not doc:
        return JsonResponse({'error': 'Documento no encontrado.'}, status=404)

    result = _serialize_doc(doc)

    if tipo == 'cancion':
        artista = _find_by_id('artista', doc.get('Artista_idArtista'), 'idArtista')
        if artista:
            result['artista'] = _serialize_doc(artista)
        album = _find_by_id('album', doc.get('Album_idAlbum'), 'idAlbum')
        if album:
            result['album'] = _serialize_doc(album)

    return JsonResponse(result)
