from fastapi import FastAPI, HTTPException, UploadFile, Query
from psycopg2 import connect, OperationalError, Error
from psycopg2.extras import RealDictCursor
import pandas as pd
import json
from fastapi.middleware.cors import CORSMiddleware

#inicializa el API y da permisos de conexion
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
"""
    Funcion que contiene parámetros de conexion a la base de datos
    pide como parámetros unas credenciales, usuario y constraseña, 
    asignados desde pgadmin
"""
def get_db_connection(user: str, password: str):
    """
    conexión a la base de datos.
    """
    DATABASE_CONFIG = {
        "host": 'localhost',
        "port": 5432,
        "user": user,
        "password": password,
        "database": "CI",
    }
    try:
        conn = connect(**DATABASE_CONFIG)
        return conn
    except OperationalError:
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos.")
    except Error as e:
        raise HTTPException(status_code=500, detail=f"No se pudo conectar a la base de datos: {e}")

""" 
declada un puerto con metodo GET para cargar de manera asincrona
los objetos espaciales cuando se inicialice el visor web
"""
@app.get("/")
def get_geojson_data(data: str = Query(..., description="Tipo de datos a consultar")):
    """
    Sirve datos espaciales en formato GeoJSON.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        query = """
                SELECT jsonb_build_object(
                    'type', 'FeatureCollection',
                    'nombreinfr',
                    'features', jsonb_agg(ST_AsGeoJSON(t.*)::jsonb)
                ) AS geojson
                FROM infraestructuralinea AS t;
                """

        
        # Ejecuta la consulta
        cursor.execute(query, (data,) if data != "all" else None)
        result = cursor.fetchone()
        conn.close()

        if result and result["geojson"]:
            return json.loads(result["geojson"])  # Retorna el GeoJSON como un diccionario
        else:
            raise HTTPException(status_code=404, detail="No se encontraron datos.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar la solicitud: {e}")

""" 
Crea un puerto de motodo post para logearse con las credenciales
asignadas en desde pgadmin
"""
@app.post("/login")
def login(credentials: dict):
    user = credentials.get("user")
    password = credentials.get("password")
    """
    Valida las credenciales y prueba la conexión.
    """
    conn = get_db_connection(user, password)
    conn.close()
    return {"message": "Conexión exitosa"}


""" 
Crea un puerto de motodo post para cargar registros a la base
"""
@app.post("/upload")
def upload_file(user: str, password: str, file: UploadFile):
    """
    Lee un archivo de excel y lo carga como registros a la base
    """
    try:
        # Leer el archivo Excel
        data = pd.read_excel(file.file)

        # Validar que el archivo tiene las columnas necesarias
        required_columns = {"nombre_predio", "numero_proceso", "area_servidumbre", "valor_deposito", "codigo"}
        if not required_columns.issubset(data.columns):
            raise HTTPException(status_code=400, detail=f"El archivo debe contener las columnas: {required_columns}")

        # Conectar a la base de datos
        conn = get_db_connection(user, password)
        cursor = conn.cursor()

        # Insertar datos en la base de datos
        for _, row in data.iterrows():
            query = """
            INSERT INTO depositos_judiciales (nombre_predio, numero_proceso, area_servidumbre, valor_deposito, codigo)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (codigo) DO NOTHING;
            """
            cursor.execute(query, (
                row["nombre_predio"],
                row["numero_proceso"],
                row["area_servidumbre"],
                row["valor_deposito"],
                row["codigo"]
            ))

        # Confirmar y cerrar la conexión
        conn.commit()
        cursor.close()
        conn.close()

        return {"message": "Cargado correctamente"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando el archivo: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("API:app", host="127.0.0.1", port=8000, reload=True)
