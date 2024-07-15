from flask import Flask, request, render_template, make_response, redirect, url_for
import recomendar
import sys


app = Flask(__name__)

@app.route('/', methods=('GET', 'POST'))
def login():
    # si me mandaron el formulario y tiene id_usuario...
    if request.method == 'POST' and 'id_usuario' in request.form:
        id_usuario = request.form['id_usuario']

        # creo el usuario al insertar el id_usuario en la tabla "usuarios"
        recomendar.crear_usuario(id_usuario)

        # mando al usuario a la página de recomendaciones
        res = make_response(redirect("/recomendaciones"))

        # pongo el id_usuario en una cookie para recordarlo
        res.set_cookie('id_usuario', id_usuario)
        return res

    # si alguien entra a la página principal y conozco el usuario
    if request.method == 'GET' and 'id_usuario' in request.cookies:
        return make_response(redirect("/recomendaciones"))

    # sino, le muestro el formulario de login
    return render_template('login.html')

@app.route('/recomendaciones', methods=('GET', 'POST'))
def recomendaciones():
    id_usuario = request.cookies.get('id_usuario')

    # me envían el formulario
    if request.method == 'POST':
        for id_vino in request.form.keys():
            rating = int(request.form[id_vino])
            recomendar.insertar_interacciones(id_vino, id_usuario, rating)

    # recomendaciones
    vinos, algoritmo = recomendar.recomendar(id_usuario)

    # pongo vinos vistos con rating = 0
    for vino in vinos:
        recomendar.insertar_interacciones(vino["id_vino"], id_usuario, 0)

    cant_valorados = len(recomendar.valorados(id_usuario))
    cant_ignorados = len(recomendar.ignorados(id_usuario))

    return render_template("recomendaciones.html", vinos=vinos, id_usuario=id_usuario, cant_valorados=cant_valorados, cant_ignorados=cant_ignorados, algoritmo=algoritmo)

@app.route('/reset')
def reset():
    id_usuario = request.cookies.get('id_usuario')
    recomendar.reset_usuario(id_usuario)

    return make_response(redirect("/recomendaciones"))


@app.route('/detalle_vino/<id_vino>', methods=['GET', 'POST'])
def vino_detalle(id_vino):
    id_usuario = request.cookies.get('id_usuario')

    # me envían el formulario
    if request.method == 'POST':
        for form_id_vino in request.form.keys():
            rating = int(request.form[form_id_vino])
            recomendar.insertar_interacciones(form_id_vino, id_usuario, rating)

    # recomendaciones
    vinos, algoritmo = recomendar.recomendar(id_usuario, id_vino=id_vino)

    id_vinos, vino, otros_vinos_de_bodega, otros_vinos_de_region, otros_vinos_de_varietal = recomendar.recomendador_asociados(id_vino, id_usuario)

    # pongo vinos vistos con rating = 0 
    for v in vinos: #vinos es el conjunto de vinos bodega, region y varietal
         recomendar.insertar_interacciones(v["id_vino"], id_usuario, 0)

    cant_valorados = len(recomendar.valorados(id_usuario))
    cant_ignorados = len(recomendar.ignorados(id_usuario))

    return render_template("vinos_detalle.html", vino=vino, otros_vinos_de_bodega=otros_vinos_de_bodega, 
                           otros_vinos_de_region=otros_vinos_de_region, otros_vinos_de_varietal=otros_vinos_de_varietal,
                           id_usuario=id_usuario, cant_valorados=cant_valorados, cant_ignorados=cant_ignorados, algoritmo=algoritmo)


if __name__ == "__main__":
    app.run(debug=True)
