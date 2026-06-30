from django.db import models

class Usuario(models.Model):
    idUsuario = models.IntegerField(primary_key=True)
    nombreUsuario = models.CharField(max_length=30)
    apellidoUsuario = models.CharField(max_length=30)
    correoUsuario = models.CharField(max_length=50)
    contraseniaUsuario = models.CharField(max_length=25)
    fechaRegistroUsuario = models.DateTimeField()
    paisUsuario = models.CharField(max_length=25)
    tipoUsuario = models.CharField(max_length=25)
    estadoCuentaUsuario = models.CharField(max_length=30)
    class Meta:
        managed = False
        db_table = '[Seguridad].[Usuario]'

class Discografia(models.Model):
    idDiscografia = models.IntegerField(primary_key=True)
    nombreDiscografia = models.CharField(max_length=25)
    paisDiscografia = models.CharField(max_length=25)
    correoDiscografia = models.CharField(max_length=30)
    class Meta:
        managed = False
        db_table = '[Catalogo].[Discografia]'

class Artista(models.Model):
    idArtista = models.IntegerField(primary_key=True)
    nombreArtisticoArtista = models.CharField(max_length=30)
    paisOrigenArtista = models.CharField(max_length=25)
    fechaRegistroArtista = models.DateTimeField()
    estadoArtista = models.CharField(max_length=25)
    Discografia_idDiscografia = models.ForeignKey(Discografia, on_delete=models.DO_NOTHING, db_column='Discografia_idDiscografia')
    class Meta:
        managed = False
        db_table = '[Catalogo].[Artista]'

class Album(models.Model):
    idAlbum = models.IntegerField(primary_key=True)
    tituloAlbum = models.CharField(max_length=30)
    fechaLanzamiento = models.DateTimeField()
    estadoAlbum = models.CharField(max_length=25)
    Artista_idArtista = models.ForeignKey(Artista, on_delete=models.DO_NOTHING, db_column='Artista_idArtista')
    class Meta:
        managed = False
        db_table = '[Catalogo].[Album]'

class Genero(models.Model):
    idGenero = models.IntegerField(primary_key=True)
    nombreGenero = models.CharField(max_length=25)
    descripcionGenero = models.CharField(max_length=100)
    class Meta:
        managed = False
        db_table = '[Catalogo].[Genero]'

class Cancion(models.Model):
    idCancion = models.IntegerField(primary_key=True)
    tituloCancion = models.CharField(max_length=30)
    duracionCancion = models.TimeField()
    numeroPistaCancion = models.IntegerField()
    estadoCancion = models.CharField(max_length=25)
    Album_idAlbum = models.ForeignKey(Album, on_delete=models.DO_NOTHING, db_column='Album_idAlbum')
    class Meta:
        managed = False
        db_table = '[Catalogo].[Cancion]'

class CancionGenero(models.Model):
    Cancion_idCancion = models.ForeignKey(Cancion, on_delete=models.DO_NOTHING, db_column='Cancion_idCancion', primary_key=True)
    Genero_idGenero = models.ForeignKey(Genero, on_delete=models.DO_NOTHING, db_column='Genero_idGenero')
    class Meta:
        managed = False
        db_table = '[Catalogo].[CancionGenero]'
        unique_together = (('Cancion_idCancion', 'Genero_idGenero'),)

class Suscripcion(models.Model):
    idSuscripcion = models.IntegerField(primary_key=True)
    tipoPlanSuscripcion = models.CharField(max_length=30)
    fechaInicioSuscripcion = models.DateTimeField()
    estadoSuscripcion = models.CharField(max_length=30)
    fechaFinSuscripcion = models.DateTimeField()
    Usuario_idUsuario = models.ForeignKey(Usuario, on_delete=models.DO_NOTHING, db_column='Usuario_idUsuario')
    class Meta:
        managed = False
        db_table = '[Comercial].[Suscripcion]'

class Pago(models.Model):
    idPago = models.IntegerField(primary_key=True)
    fechaPago = models.DateTimeField()
    montoPago = models.IntegerField()
    metodoPago = models.CharField(max_length=25)
    estadoPago = models.CharField(max_length=25)
    Suscripcion_idSuscripcion = models.ForeignKey(Suscripcion, on_delete=models.DO_NOTHING, db_column='Suscripcion_idSuscripcion')
    class Meta:
        managed = False
        db_table = '[Finanzas].[Pago]'

class Regalia(models.Model):
    idRegalia = models.IntegerField(primary_key=True)
    periodoRegalia = models.CharField(max_length=25)
    totalReproduccionesRegalia = models.IntegerField()
    fechaCalculoRegalia = models.DateTimeField()
    Artista_idArtista = models.ForeignKey(Artista, on_delete=models.DO_NOTHING, db_column='Artista_idArtista')
    class Meta:
        managed = False
        db_table = '[Finanzas].[Regalia]'

class Playlist(models.Model):
    idPlaylist = models.IntegerField(primary_key=True)
    nombrePlaylist = models.CharField(max_length=30)
    fechaCreacionPlaylist = models.DateTimeField()
    estadoPlaylist = models.CharField(max_length=25)
    Usuario_idUsuario = models.ForeignKey(Usuario, on_delete=models.DO_NOTHING, db_column='Usuario_idUsuario')
    class Meta:
        managed = False
        db_table = '[Streaming].[Playlist]'

class PlaylistCancion(models.Model):
    Playlist_idPlaylist = models.ForeignKey(Playlist, on_delete=models.DO_NOTHING, db_column='Playlist_idPlaylist', primary_key=True)
    Cancion_idCancion = models.ForeignKey(Cancion, on_delete=models.DO_NOTHING, db_column='Cancion_idCancion')
    fechaAgregada = models.DateTimeField()
    ordenCancion = models.IntegerField()
    class Meta:
        managed = False
        db_table = '[Streaming].[PlaylistCancion]'
        unique_together = (('Playlist_idPlaylist', 'Cancion_idCancion'),)

class Reproduccion(models.Model):
    idReproduccion = models.IntegerField(primary_key=True)
    fechaReproduccion = models.DateTimeField()
    paisReproduccion = models.CharField(max_length=25)
    duracionReproduccion = models.TimeField()
    Usuario_idUsuario = models.ForeignKey(Usuario, on_delete=models.DO_NOTHING, db_column='Usuario_idUsuario')
    Cancion_idCancion = models.ForeignKey(Cancion, on_delete=models.DO_NOTHING, db_column='Cancion_idCancion')
    class Meta:
        managed = False
        db_table = '[Streaming].[Reproduccion]'

class UsuarioArtista(models.Model):
    Usuario_idUsuario = models.ForeignKey(Usuario, on_delete=models.DO_NOTHING, db_column='Usuario_idUsuario', primary_key=True)
    Artista_idArtista = models.ForeignKey(Artista, on_delete=models.DO_NOTHING, db_column='Artista_idArtista')
    fechaSeguimiento = models.DateTimeField()
    class Meta:
        managed = False
        db_table = '[Seguridad].[UsuarioArtista]'
        unique_together = (('Usuario_idUsuario', 'Artista_idArtista'),)

class UsuarioCancion(models.Model):
    Usuario_idUsuario = models.ForeignKey(Usuario, on_delete=models.DO_NOTHING, db_column='Usuario_idUsuario', primary_key=True)
    Cancion_idCancion = models.ForeignKey(Cancion, on_delete=models.DO_NOTHING, db_column='Cancion_idCancion')
    fechaLike = models.DateTimeField()
    class Meta:
        managed = False
        db_table = '[Seguridad].[UsuarioCancion]'
        unique_together = (('Usuario_idUsuario', 'Cancion_idCancion'),)