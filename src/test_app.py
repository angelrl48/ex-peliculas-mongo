import pytest
import json
from app import app, usuarios_bd, peliculas_bd

# Configuración inicial para las pruebas

@pytest.fixture
def client():
    app.config['TESTING'] = True
    client = app.test_client()

    # Borrar datos en la base de datos antes de cada prueba

    usuarios_bd.delete_many({})
    peliculas_bd.delete_many({})

    yield client

    
# Prueba para el registro de un nuevo usuario
def test_registro(client):
    response = client.post('/registro', json ={
        'nombre':'usuario',
        'password':'contraseña'
    })                           
    assert response.status_code == 201
    assert response.get_json()['message'] == "Usuario registrado correctamente"

# Prueba para el inicio de sesión y generación del token de autenticación
def test_login(client):
    # Primero se registra al usuario
    client.post('/registro', json ={
        'nombre' : 'usuario2',
        'password': '123456' 
    })
    # Luego, iniciar sesión
    response = client.post('/login', json={
        'nombre': 'usuario2',
        'password': '123456'
    })
    assert response.status_code == 200
    assert 'token' in response.get_json()

# Prueba para crear una nueva película en la base de datos
def test_add_pelicula(client):
    # Registrar usuario
    client.post('/registro', json={
        'nombre':'usuario3',
        'password': 'contraseña'
    })
    # Iniciar sesión
    login_response = client.post('/login', json = {
        'nombre': 'usuario3',
        'password': 'contraseña'
    })
    token = login_response.get_json()['token']

    # Crear una nueva película en la base de datos, se usa el token creado
    response = client.post('/peliculas', headers={'x-access-token': token}, json={
        'nombre': 'Inception',
        'actores': ['Leonardo DiCaprio', 'Joseph Gordon-Levitt'],
        'director': 'Christopher Nolan',
        'género': 'Ciencia ficción',
        'calificación' : 9,
        'año_de_lanzamiento': 2010
    })
    assert response.status_code == 201
    assert '_id' in response.get_json()

# Prueba para obtener todas las peliculas
def test_get_peliculas(client):
    # Registrar nuevo usuario
    client.post('/registro', json={
            'nombre':'usuario4',
            'password': 'testcontraseña'
    })
    # Iniciar sesión
    login_response = client.post('/login', json={
            'nombre': 'usuario4',
            'password': 'testcontraseña'
        })
    token = login_response.get_json()['token']

    #Agregar una película
    client.post('/peliculas', headers={'x-access-token': token}, json={
            'nombre':'La mosca',
            'actores':['Jeff Goldblum', 'David Cronenberg', 'Geena Davis', 'John Getz'],
            'director':'David Cronenberg',
            'género':'Terror',
            'calificación':'8',
            'año_de_lanzamiento': '1986'

        })

    # Obtener todas las películas
    response = client.get('/peliculas', headers={'x-access-token': token})
    assert response.status_code == 200
    assert len(response.get_json()) == 1

# Prueba para actualizar una película
def test_update_pelicula(client):
    # Registrar un usuario
    client.post('/registro', json ={
        'nombre':'usuario5',
        'password':'contraseña2'
    })
    #Iniciar sesión y generar token
    login_response = client.post('/login', json = {
        'nombre': 'usuario5',
        'password': 'contraseña2'
    })
    token = login_response.get_json()['token']

    # Agregar una película
    pelicula_response = client.post('/peliculas', headers={'x-access-token': token}, json={
            'nombre':'El protegido',
            'actores':['Bruce Willis', 'Samuel L. Jackson'],
            'director':'Shyamalan',
            'género':'Thriller',
            'calificación':'9',
            'año_de_lanzamiento': '2000'
    })
    pelicula_id = pelicula_response.get_json()['_id']

    #Actualizar la película
    response =  client.put(f'/peliculas/{pelicula_id}', headers = {'x-access-token': token}, json={
            'nombre':'Unbreakable',
            'actores':['Bruce Willis', 'Samuel L. Jackson'],
            'director':'M. Night Shyamalan',
            'género':'Suspenso',
            'calificación':'8',
            'año_de_lanzamiento': '2000'
    })
    assert response.status_code == 200
    assert response.get_json()['message'] == 'Pelicula actualizada correctamente'

# Prueba para eliminar una película
def test_delete_pelicula(client):
    #Registrar usuario
    client.post('/registro', json = {
        'nombre':'usuario6',
        'password': 'contraseñaa'
    })
    login_response = client.post('/login', json ={
        'nombre':'usuario6',
        'password': 'contraseñaa'
    })
    token = login_response.get_json()['token']

    # Agregar una película
    pelicula_response = client.post('/peliculas', headers ={'x-access-token': token}, json={
        'nombre':'Depredador',
        'actores':['Kevin Peter Hall','Arnold Schwarzenegger'],
        'director':'Shane Black',
        'género':'Acción',
        'calificación':'10',
        'año_de_lanzamiento':'1987'
    })
    pelicula_id = pelicula_response.get_json()['_id']

    #Eliminar la película
    response = client.delete(f'/peliculas/{pelicula_id}', headers = {'x-access-token':token})
    assert response.status_code == 200
    assert response.get_json()['message'] == 'Pelicula eliminada'



