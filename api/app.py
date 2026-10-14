import os
from flask import Flask, jsonify, request
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

app = Flask(__name__)

url = URL.create(
    "postgresql+psycopg2",
    username=os.environ["POSTGRES_USER"],
    password=os.environ["POSTGRES_PASSWORD"],
    host="db",
    port=5432,
    database=os.environ["POSTGRES_DB"],
)
engine = create_engine(url)

CAMPOS_OBLIGATORIOS = ["edificio", "fecha_hora", "temperatura", "humedad", "co2_ppm"]


@app.get("/health")
def health():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return jsonify({"status": "ok", "database": "connected"}), 200
    except Exception as e:
        return jsonify({"status": "error", "detail": str(e)}), 500


@app.get("/lecturas")
def listar_lecturas():
    consulta = text(
        "SELECT edificio, fecha_hora, temperatura, humedad, co2_ppm "
        "FROM lecturas ORDER BY fecha_hora, edificio"
    )
    with engine.connect() as conn:
        filas = conn.execute(consulta).mappings().all()

    lecturas = []
    for fila in filas:
        lectura = dict(fila)
        lectura["fecha_hora"] = lectura["fecha_hora"].isoformat(sep=" ")
        lecturas.append(lectura)

    return jsonify(lecturas), 200


@app.post("/lecturas")
def crear_lectura():
    datos = request.get_json(silent=True)
    if not isinstance(datos, dict):
        return jsonify({"error": "El cuerpo debe ser un JSON válido"}), 400

    faltan = [c for c in CAMPOS_OBLIGATORIOS if c not in datos or datos[c] is None]
    if faltan:
        return jsonify({
            "error": "Faltan campos obligatorios",
            "campos_faltantes": faltan,
        }), 400

    insercion = text(
        "INSERT INTO lecturas (edificio, fecha_hora, temperatura, humedad, co2_ppm) "
        "VALUES (:edificio, :fecha_hora, :temperatura, :humedad, :co2_ppm)"
    )
    try:
        with engine.begin() as conn:
            conn.execute(insercion, {c: datos[c] for c in CAMPOS_OBLIGATORIOS})
    except Exception as e:
        return jsonify({"error": "No se pudo guardar la lectura", "detalle": str(e)}), 500

    return jsonify({"mensaje": "Lectura guardada", "lectura": datos}), 201


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)