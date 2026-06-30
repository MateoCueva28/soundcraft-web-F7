import os
from pathlib import Path
from pymongo import MongoClient
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env en la raíz del proyecto
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / '.env')

MONGO_URI = os.getenv('MONGO_URI')


try:
    if not MONGO_URI:
        raise ValueError('La variable de entorno MONGO_URI no está definida.')

    client = MongoClient(MONGO_URI)
    # Usamos los nombres exactos que acabamos de validar en la consola
    db = client['Soundcraft']

    client.admin.command('ping')
    print("¡Conexión exitosa a MONGODB ATLAS establecida correctamente!")
except Exception as e:
    print(f"Error al conectar a MongoDB Atlas: {e}")
    db = None