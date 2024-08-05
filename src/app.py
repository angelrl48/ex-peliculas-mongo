from flask import Flask, request, jsonify, make_response
from marshmallow import ValidationError
from pymongo import MongoClient
from bson import ObjectId
import jwt
import datetime
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
#Se importan los esquemas de validación
from schemas import UserSchema, PeliSchema
import logging

import sys

sys.stdout.reconfigure(encoding='utf-8')

# Crear una instancia de la aplicación Flask
app = Flask(__name__)

# Configuración de la clave secreta para JWT
app.config['SECRET_KEY'] = 'your_secret_key'

#Conectar a la base de datos MongoDB
client = MongoClient('localhost',27017)
db = client['examen_db'] # Nombre de la base de datos
peliculas_bd = db['peliculas'] # Nombre de la colección de peliculas
usuarios_bd = db['usuarios']# Nombre de la colección de usuarios



# Se instancian los esquemas
usuario_schema = UserSchema()
peli_schema = PeliSchema()

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s', handlers=[logging.FileHandler("app.log"), logging.StreamHandler()])


# Decorador para verificar el token JWT

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('x-access-token')
        if not token:
            #Se añade logging
            logging.warning('Token no encontrado!')
            return jsonify({'message': 'Token no encontrado!'}), 401
        #En caso de que si se encuentre el token
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = usuarios_bd.find_one({'_id': ObjectId(data['usuario_id'])})
        except jwt.ExpiredSignatureError:
            #Se añade logging para token expirado
            logging.warning('El token ha expirado')
            return jsonify({'message': 'El token ha expirado'}), 401
        except jwt.jwt.InvalidTokenError:
            #Se añade logging para token inválido
            logging.warning('El token es inválido')
            return jsonify({'message': 'El token es inválido'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

# Ruta para registrar un nuevo usuario en la base de datos
@app.route('/registro', methods = ['POST'])
def registro():
    data = request.get_json()
    #try añadido únicamente para la validación de los datos ingresados
    try:
        # Se validan los datos ingresados usando el esquema
        usuario_schema.load(data)

    except ValidationError as err:
        #Se añade logging para error de validación usando esquema
        logging.error(f"Error de validación durante registro: {err.messages}")
        return jsonify(err.messages), 400
    
    # Verificar sí el nombre de usuario ya existe
    if usuarios_bd.find_one({'nombre': data['nombre']}):
        #Se añade logging de advertencia
        logging.warning(f"El registro ha fallado: El nombre de usuario {data['nombre']} ya existe en la base de datos")
        return jsonify({'message': 'El nombre de usuario ya existe, ingresa otro'}), 400

    
    # Se encripta la contraseña
    hashed_password = generate_password_hash(data['password'], method='scrypt')
    # Una vez que se validaron los datos y se encriptó la contraseña, se asignan los valores a una estructura json
    usuario = {
        'nombre': data['nombre'],
        'password': hashed_password
    }
    # Se añade try para declarar un codigo que podria generar una excepción, en este caso confirmar que el nombre sea único
    # Se registran los datos en la BD
    usuarios_bd.insert_one(usuario)
    #Se añade logging para registrar que el usuario se registró correctamente
    logging.info(f"usuario {data['nombre']} registrado correctamente")
    return jsonify({'message': 'Usuario registrado correctamente'}), 201
    


# Ruta para iniciar sesión y obtener un token JWT
@app.route('/login', methods = ['POST'])
def login():
    data = request.get_json()
    #Try añadido para las validaciones del esquema
    try:
        # Se validan los datos de entrada
        usuario_schema.load(data)
    except ValidationError as err:
        #Se añade logging para error de validación durante login
        logging.error(f"Error de validación durante login: {err.messages}")
        return jsonify(err.messages),400
    

    usuario = usuarios_bd.find_one({'nombre': data['nombre']})
    # En caso de que no se encuentre el usuario ó contraseña en la base de datos, manda error
    if not usuario or not check_password_hash(usuario['password'], data['password']):
        #Se añade loggging para registrar advertencia al iniciar sesión
        logging.warning(f"Error al iniciar sesión para el usuario {data['nombre']}")
        return make_response('Error al iniciar sesión', 401, {'WWW-Authenticate' : 'Basic realm= "Inténtalo de nuevo!"'})
    # Si todo está correcto, se crea el jwt y se asigna un tiempo de expiración de una hora
    token = jwt.encode({'usuario_id': str(usuario['_id']), 'exp': datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=1)}, app.config['SECRET_KEY'], algorithm='HS256')
    #Se añade logging de información para registrar inicio de sesión éxitoso
    logging.info(f"usuario {data['nombre']} inició sesión correctamente")
    return jsonify({'token': token})

# Ruta principal y de prueba para verificar que la api res está funcionando
# @app.route('/')
# def index():
#     return "Hola mundo"


# Ruta para obtener todas las películas (Read)
@app.route('/peliculas', methods =['GET'])
@token_required # Aqui se define que necesario un token para visualizar los datos de peliculas
def get_pelis(current_user):
    # Obtener todas las peliculas ingresadas en la bd
    peliculas = list(peliculas_bd.find())
    if not peliculas:
        #Si no se encuentra ninguna pelicula, devolver error 404
        return jsonify({'error': 'PELICULAS NO ENCONTRADAS'}), 404
    #Listar las peliculas y convertirlas en valores string para que puedan ser JSON
    for pelicula in peliculas:
        pelicula['_id'] = str(pelicula['_id'])
    #Se añade logging para registrar que un usuario consultó todas las peliculas
    logging.info(f"usuario {current_user['nombre']} consultó todas las peliculas")
    #Devolver lista de peliculas
    return jsonify(peliculas), 200 


# Ruta para obtener una pelicula por ID (Read)
@app.route('/peliculas/<id>', methods=['GET'])
@token_required # Token del usuario es necesario para visualizar las peliculas por ID
def get_peli(current_user,id):
    # Buscar la pelicula por su ID
    pelicula = peliculas_bd.find_one({'_id': ObjectId(id)})
    #Si no se encuentra la pelicula, devolver error 404
    if not pelicula:
        return jsonify({'error': 'Pelicula no encontrada'}), 404
    #Se convierte el objectID a valor string para que pueda ser JSON
    pelicula['_id'] = str(pelicula['_id'])
    #Se añade logging de información
    logging.info(f"usuario {current_user['nombre']} consultó la pelicula {pelicula['nombre']}")
    #Devolver los datos de la pelicula
    return jsonify(pelicula), 200


# Ruta para insertar una pelicula en la base de datos (Create)
@app.route('/peliculas', methods = ['POST'])
@token_required # Token del usuario es necesario para añadir peliculas
def add_peli(current_user):
    # Almacenar en una variable una solicitud a la base de datos
    data = request.get_json()
    # Se usa un try para validar los datos de entrada usando el esquema
    try:
        # Validar datos de entrada
        peli_schema.load(data)
    except ValidationError as err:
        #Se añade logging para registrar error de validación al intentar ingresar datos de película
        logging.error(f"Errror de validación al intentar añadir película: {err.messages}")
        return jsonify(err.messages), 400
    # Definir variable para insertar los datos de la pelicula
    result = peliculas_bd.insert_one(data)
    #Se añade logging para registrar ingreso éxitoso de pelicula
    logging.info(f"pelicula {data['nombre']} añadida éxitosamente por el usuario {current_user['nombre']}")
    # Devolver una confirmación, retornando el ID de la pelicula que se ingresó
    return jsonify({'_id': str(result.inserted_id)}), 201


# Ruta para actualizar una pelicula por su ID (Update)
@app.route('/peliculas/<id>', methods = ['PUT'])
@token_required # Token necesario para actualizar alguna pelicula
def update_peli(current_user, id):
    # Almacenar en una variable una solicitud a la base de datos
    data = request.get_json()
    #Se usa un try para validar los datos de entrada usando el esquema
    try:
        peli_schema.load(data)
    except ValidationError as err:
        #Se añade logging para registrar error de validacion
        logging.error(f"Error de validación al actualizar pelicula: {err.messages}")
        return jsonify(err.messages), 400
    # Definir variable para actualizar los datos de la pelicula
    result = peliculas_bd.update_one({'_id': ObjectId(id)}, {'$set': data})
    # Si no se actualiza ningún documento, devolver un error 404
    if result.matched_count == 0:
        #Se añade logging para registrar advertencia al no encontrar la pelicula
        logging.warning(f"pelicula con id {id} no encontrada para actualización")
        return jsonify({'error': 'Pelicula no encontrada'}), 404
    #Se añade logging para registrar actualización éxitosa de pelicula
    logging.info(f"pelicula con id {id} actualizada correctamente por el usuario {current_user['nombre']}")
    # Devolver una confirmación de se actualizó correctamente la pelicula
    return jsonify({'message':'Pelicula actualizada correctamente'}), 200


#Ruta para eliminar una pelicula por su ID (DELETE)
@app.route('/peliculas/<id>', methods = ['DELETE'])
@token_required # Token del usuario necesario para borrar peliculas
def delete_peli(current_user, id):
    #Definir variable para eliminar la pelicula
    result = peliculas_bd.delete_one({'_id': ObjectId(id)})
    #Si no se elimina ninguna pelicula, devolver un error 404
    if result.deleted_count == 0:
        #se añade logging de advertencia
        logging.warning(f"pelicula con id {id} no encontrada")
        return jsonify({'error': 'Pelicula no encontrada'}), 404
    #se añade logging para registrar eliminación éxitosa
    logging.info(f"pelicula con id {id} eliminada correctamente por el usuario {current_user['nombre']}")
    #Devolver una confirmación de que la pelicula fue eliminada
    return jsonify({'message': 'Pelicula eliminada'}), 200


# Iniciar la aplicación Flask
if __name__ == '__main__':
    #Aquí se inicia el modo depurador para que la api se actualice automáticamente cada vez que se guarda.
    app.run(debug=True)