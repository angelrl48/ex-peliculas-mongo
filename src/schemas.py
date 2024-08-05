from marshmallow import Schema, fields, validate


#Se definen las reglas dentro de la clase esquema para las peliculas

class PeliSchema(Schema):
    nombre = fields.Str(required=True, validate=validate.Length(min=1))
    actores = fields.List(fields.Str(), required=True, validate=validate.Length(min=1))
    director = fields.Str(required=True, validate=validate.Length(min=1))
    género = fields.Str(required=True, validate=validate.Length(min=1))
    calificación = fields.Float(required=True,validate=validate.Range(min=0,max=10))
    año_de_lanzamiento = fields.Int(required=True, validate=validate.Range(min=1800, max=2100))

#Se definen las reglas dentro de la clase esquema para los usuarios

class UserSchema(Schema):
    nombre = fields.Str(required=True, validate=validate.Length(min=1))
    password = fields.Str(required=True, validate=validate.Length(min=6))
