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
    import json as _json
    redir = _require_session(request)
    if redir:
        return redir
    canciones = _load_documents('cancion', 'idCancion')

    canciones_js = []
    for c in canciones:
        album = c.get('album') or {}
        canciones_js.append({
            'id':                 c.get('id_str', ''),
            'idInt':              c['_id'] if isinstance(c.get('_id'), int) else 0,
            'tituloCancion':      c.get('tituloCancion', ''),
            'duracionCancion':    c.get('duracionCancion', ''),
            'numeroPistaCancion': c.get('numeroPistaCancion', ''),
            'estadoCancion':      c.get('estadoCancion', ''),
            'generos':            [g.get('genero', '') for g in (c.get('generos') or [])],
            'albumTitulo':        album.get('tituloAlbum', ''),
            'albumArtista':       album.get('nombreArtista', ''),
        })

    return render(request, 'canciones/list.html', {
        'canciones':      canciones,
        'canciones_json': _json.dumps(canciones_js, ensure_ascii=False),
    })


# ============================================================
# PLAYLISTS
# ============================================================
def playlist_list(request):
    import json as _json
    redir = _require_session(request)
    if redir:
        return redir
    playlists = _load_documents('playlists', 'idPlaylist')
    if db is not None and playlists:
        ids = list({p.get('usuarioId') for p in playlists if p.get('usuarioId') is not None})
        usuarios = {u['_id']: u.get('nombreUsuario', '') for u in db['usuario'].find({'_id': {'$in': ids}}, {'nombreUsuario': 1})}
        for p in playlists:
            p['nombreUsuario'] = usuarios.get(p.get('usuarioId'), '—')

    # Serializar para window.PLAYLISTS_DATA (modal de detalle + colores)
    playlists_js = []
    for p in playlists:
        playlists_js.append({
            'id':             p.get('id_str', ''),
            'idInt':          p['_id'] if isinstance(p.get('_id'), int) else 0,
            'nombrePlaylist': p.get('nombrePlaylist', ''),
            'estadoPlaylist': p.get('estadoPlaylist', ''),
            'nombreUsuario':  p.get('nombreUsuario', '—'),
            'canciones': [
                {
                    'tituloCancion': c.get('tituloCancion', ''),
                    'fechaAgregada': c.get('fechaAgregada', '') if isinstance(c.get('fechaAgregada'), str) else '',
                }
                for c in (p.get('canciones') or [])
            ],
        })

    return render(request, 'playlists/list.html', {
        'playlists':      playlists,
        'playlists_json': _json.dumps(playlists_js, ensure_ascii=False),
    })


def playlist_eliminar(request, pk):
    redir = _require_session(request)
    if redir:
        return redir
    playlist = _find_by_id('playlists', pk, 'idPlaylist')
    if not playlist:
        messages.error(request, 'Playlist no encontrada.')
        return redirect('playlist_list')
    if request.method == 'POST':
        try:
            db['playlists'].delete_one({'_id': playlist['_id']})
            messages.success(request, 'Playlist eliminada exitosamente.')
        except Exception as e:
            messages.error(request, f'Error al eliminar: {e}')
    return redirect('playlist_list')


def playlist_cambiar_estado(request, pk):
    if not request.session.get('usuario_id'):
        return JsonResponse({'error': 'No autenticado'}, status=401)
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    if db is None:
        return JsonResponse({'error': 'Sin conexión a base de datos'}, status=503)
    playlist = _find_by_id('playlists', pk, 'idPlaylist')
    if not playlist:
        return JsonResponse({'error': 'Playlist no encontrada'}, status=404)
    nuevo_estado = 'Suspendida' if playlist.get('estadoPlaylist') == 'Activa' else 'Activa'
    try:
        db['playlists'].update_one({'_id': playlist['_id']}, {'$set': {'estadoPlaylist': nuevo_estado}})
        return JsonResponse({'estadoPlaylist': nuevo_estado})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


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

    import json as _json

    def _dt_str(v):
        if v is None:
            return ''
        if hasattr(v, 'strftime'):
            return v.strftime('%Y-%m-%dT%H:%M:%S')
        return str(v)

    empty = {'repros': [], 'pagos': [], 'suscripciones': [], 'regalias': []}

    if db is None:
        return render(request, 'reportes/reportes.html',
                      {'reportes_json': _json.dumps(empty, ensure_ascii=False)})

    repros_raw = [
        {'pais': r.get('paisReproduccion') or 'Desconocido',
         'fecha': _dt_str(r.get('fechaReproduccion', ''))}
        for r in db['reproduccion'].find(
            {}, {'paisReproduccion': 1, 'fechaReproduccion': 1, '_id': 0})
    ]

    pagos_raw = [
        {'metodo': p.get('metodoPago') or 'Sin método',
         'monto': float(p.get('montoPago') or 0),
         'fecha': _dt_str(p.get('fechaPago', ''))}
        for p in db['pago'].find(
            {}, {'metodoPago': 1, 'montoPago': 1, 'fechaPago': 1, '_id': 0})
    ]

    suscripciones_raw = [
        {'plan': s.get('tipoPlanSuscripcion') or 'Sin plan',
         'estado': s.get('estadoSuscripcion', ''),
         'fecha': _dt_str(s.get('fechaInicioSuscripcion', ''))}
        for s in db['suscripcion'].find(
            {}, {'tipoPlanSuscripcion': 1, 'estadoSuscripcion': 1,
                 'fechaInicioSuscripcion': 1, '_id': 0})
    ]

    regalias_raw = [
        {'artista': r.get('nombreArtista', ''),
         'periodo': r.get('periodoRegalia', ''),
         'repros': int(r.get('totalReproduccionesRegalia') or 0)}
        for r in db['regalia'].find(
            {}, {'nombreArtista': 1, 'periodoRegalia': 1,
                 'totalReproduccionesRegalia': 1, '_id': 0})
    ]

    payload = {
        'repros': repros_raw,
        'pagos': pagos_raw,
        'suscripciones': suscripciones_raw,
        'regalias': regalias_raw,
    }
    return render(request, 'reportes/reportes.html',
                  {'reportes_json': _json.dumps(payload, ensure_ascii=False)})


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
