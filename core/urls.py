from django.urls import path
from . import views

urlpatterns = [
    # Login / Logout
    path('login/', views.login_view, name='login_view'),
    path('logout/', views.logout_view, name='logout_view'),

    # Ruta principal: muestra el login al entrar
    path('', views.login_view, name='home'),

    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),

    # Usuarios
    path('usuarios/', views.usuario_list, name='usuario_list'),
    path('usuarios/crear/', views.usuario_crear, name='usuario_crear'),
    path('usuarios/editar/<str:pk>/', views.usuario_editar, name='usuario_editar'),
    path('usuarios/eliminar/<str:pk>/', views.usuario_eliminar, name='usuario_eliminar'),

    # Artistas
    path('artistas/', views.artista_list, name='artista_list'),

    # Canciones
    path('canciones/', views.cancion_list, name='cancion_list'),

    # Playlists
    path('playlists/', views.playlist_list, name='playlist_list'),
    path('playlists/eliminar/<str:pk>/', views.playlist_eliminar, name='playlist_eliminar'),
    path('playlists/cambiar-estado/<str:pk>/', views.playlist_cambiar_estado, name='playlist_cambiar_estado'),

    # Reproducciones
    path('reproducciones/', views.reproduccion_list, name='reproduccion_list'),

    # Suscripciones
    path('suscripciones/', views.suscripcion_list, name='suscripcion_list'),

    # Pagos
    path('pagos/', views.pago_list, name='pago_list'),

    # Regalías
    path('regalias/', views.regalia_list, name='regalia_list'),

    # Reportes
    path('reportes/', views.reportes, name='reportes'),

    # API interna — detalle JSON para modals/pop-ups
    path('api/detalle/<str:tipo>/<str:id_entidad>/', views.obtener_detalle_json, name='api_detalle_json'),
]
