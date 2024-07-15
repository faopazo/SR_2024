import sqlite3
import pandas as pd
import sys
import os

import lightfm as lfm
from lightfm import data
from lightfm import cross_validation
from lightfm import evaluation
import surprise as sp

import whoosh as wh
from whoosh import fields
from whoosh import index
from whoosh import qparser

import flask_app
from flask import request


THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))

def sql_execute(query, params=None):
    con = sqlite3.connect(os.path.join(THIS_FOLDER, "data/data.db"))
    cur = con.cursor()
    if params:
        res = cur.execute(query, params)
    else:
        res = cur.execute(query)

    con.commit()
    con.close()
    return

def sql_select(query, params=None):
    con = sqlite3.connect(os.path.join(THIS_FOLDER, "data/data.db"))
    con.row_factory = sqlite3.Row # esto es para que devuelva registros en el fetchall
    cur = con.cursor()
    if params:
        res = cur.execute(query, params)
    else:
        res = cur.execute(query)

    ret = res.fetchall()
    con.close()

    return ret

def crear_usuario(id_usuario):
    query = "INSERT INTO usuarios(id_usuario) VALUES (?) ON CONFLICT DO NOTHING;" # si el id_usuario existia, se produce un conflicto y le digo que no haga nada
    sql_execute(query, (id_usuario,))
    return

def insertar_interacciones(id_vino, id_usuario, rating, interacciones="interacciones"):
    query = f"INSERT INTO {interacciones}(id_vino, id_usuario, rating) VALUES (?, ?, ?) ON CONFLICT (id_vino, id_usuario) DO UPDATE SET rating=?;" # si el rating existia lo actualizo
    sql_execute(query, (id_vino, id_usuario, rating, rating))
    return

def reset_usuario(id_usuario, interacciones="interacciones"):
    query = f"DELETE FROM {interacciones} WHERE id_usuario = ?;"
    sql_execute(query, (id_usuario,))
    return

def obtener_vino(id_vino):
    query = "SELECT * FROM vinos WHERE id_vino = ?;"
    vino = sql_select(query, (id_vino,))[0]
    return vino

def valorados(id_usuario, interacciones="interacciones"):
    query = f"SELECT * FROM {interacciones} WHERE id_usuario = ? AND rating > 0"
    valorados = sql_select(query, (id_usuario,))
    return valorados

def ignorados(id_usuario, interacciones="interacciones"):
    query = f"SELECT * FROM {interacciones} WHERE id_usuario = ? AND rating = 0"
    ignorados = sql_select(query, (id_usuario,))
    return ignorados

def datos_vinos(id_vinos):
    query = f"SELECT DISTINCT * FROM vinos WHERE id_vino IN ({','.join(['?']*len(id_vinos))})"
    vinos = sql_select(query, id_vinos)
    return vinos

#Agrego condición de usuarios con usuarios de más de 100 seguidores y es más variado
def recomendar_top_9(id_usuario, interacciones="interacciones"):
    query = f"""
        SELECT id_vino, AVG(rating) as rating, count(*) AS cant
          FROM {interacciones} 
         WHERE id_vino NOT IN (SELECT id_vino FROM {interacciones} WHERE id_usuario = ?)
                     AND id_usuario IN (SELECT id_usuario FROM usuarios WHERE seguidores>100)
           AND rating > 0
         GROUP BY 1
         ORDER BY 3 DESC, 2 DESC
         LIMIT 9
    """
    id_vinos = [r["id_vino"] for r in sql_select(query, (id_usuario,))]
    return id_vinos

# Recomendaciones para la sección vinos_detalle 
def vino_consultado(id_vino):  
    with sqlite3.connect(os.path.join(THIS_FOLDER, "data/data.db")) as con:
        query_vino = "SELECT * FROM vinos WHERE id_vino = ?"
        vino = pd.read_sql_query(query_vino, con, params=(id_vino,))
        vino = vino.to_dict('records')[0]
       
    return vino

def recomendador_asociados(id_vino, id_usuario, interacciones="interacciones"):
    with sqlite3.connect(os.path.join(THIS_FOLDER, "data/data.db")) as con:
        query_vino = "SELECT * FROM vinos WHERE id_vino = ?"
        vino = pd.read_sql_query(query_vino, con, params=(id_vino,))
        vino = vino.to_dict('records')[0]

        query_bodega = """SELECT * FROM vinos WHERE bodega = ? AND id_vino != ? AND vino != ?
                          ORDER BY cant_reviews DESC, rating_vino DESC LIMIT 9"""
        otros_vinos_de_bodega = pd.read_sql_query(query_bodega, con, params=(vino['bodega'], id_vino, vino['vino']))
        
        query_region = """SELECT * FROM vinos WHERE region = ? AND id_vino != ? AND bodega != ? 
                          ORDER BY cant_reviews DESC, rating_vino DESC LIMIT 9"""
        otros_vinos_de_region = pd.read_sql_query(query_region, con, params=(vino['region'], id_vino, vino['bodega']))
        
        query_varietal = """SELECT * FROM vinos WHERE varietal = ? AND id_vino != ? AND region != ?
                            ORDER BY cant_reviews DESC, rating_vino DESC LIMIT 9"""
        otros_vinos_de_varietal = pd.read_sql_query(query_varietal, con, params=(vino['varietal'], id_vino, vino['region']))
    
        df_int = pd.read_sql_query(f"SELECT * FROM {interacciones}", con)
        vinos_probados_o_vistos = df_int.loc[df_int["id_usuario"] == id_usuario, "id_vino"].tolist()
        
        # Filtro vinos que no haya visto o puntuado previamente
        dict_vinos_de_bodega = [vino for vino in otros_vinos_de_bodega.to_dict('records') if vino['id_vino'] not in vinos_probados_o_vistos]
        dict_vinos_de_region = [vino for vino in otros_vinos_de_region.to_dict('records') if vino['id_vino'] not in vinos_probados_o_vistos]
        dict_vinos_de_varietal = [vino for vino in otros_vinos_de_varietal.to_dict('records') if vino['id_vino'] not in vinos_probados_o_vistos]
        
        # Obtengo los IDs de los vinos filtrados  
        # retorno id_vinos en forma de lista para luego aplicar funcion datos_vinos() 
        # dentro de la función recomendar de abajo, el resto los aplico acá y luego los llamo en 
        #la sección detalle_vinos de mi flask app
        id_vinos = [vino['id_vino'] for vino in dict_vinos_de_bodega + dict_vinos_de_region + dict_vinos_de_varietal]
        id_vinos_bodega = [vino['id_vino'] for vino in dict_vinos_de_bodega]
        id_vinos_region = [vino['id_vino'] for vino in dict_vinos_de_region]
        id_vinos_varietal = [vino['id_vino'] for vino in dict_vinos_de_varietal]

        otros_vinos_de_bodega = datos_vinos(id_vinos_bodega)
        otros_vinos_de_region = datos_vinos(id_vinos_region)
        otros_vinos_de_varietal = datos_vinos(id_vinos_varietal)

    return id_vinos, vino, otros_vinos_de_bodega, otros_vinos_de_region, otros_vinos_de_varietal
    

# Agrego más variables de perfil vino: id_vino", "region", "varietal", "bodega", "cosecha_vino
# y de perfil usuario: "idioma_usuario", "es_premium", "seguidores", "seguidos", "cant_ratings", "cant_reviews"
# desempato los scores de perfil iguales por cantidad de interacciones de usuario


def recomendar_perfil(id_usuario, interacciones="interacciones"):
    # Conexión a la base de datos
    con = sqlite3.connect(os.path.join(THIS_FOLDER, "data/data.db"))

    # Cargar datos relevantes
    df_int = pd.read_sql_query(f"SELECT * FROM {interacciones}", con)
    df_items = pd.read_sql_query("SELECT * FROM vinos", con)
    df_usuarios = pd.read_sql_query("SELECT * FROM usuarios", con)

    con.close()

    # Filtrar interacciones por usuario
    df_user_interactions = df_int[df_int["id_usuario"] == id_usuario]

    # Contar interacciones por usuario para desempate
    user_interaction_counts = df_int.groupby('id_usuario').size()
    user_interaction_count = user_interaction_counts.loc[id_usuario] if id_usuario in user_interaction_counts else 1

    # perfiles de ítems y usuarios
    perf_items = pd.get_dummies(df_items[["id_vino", "region", "varietal", "bodega", "cosecha_vino"]], columns=["region", "varietal", "bodega", "cosecha_vino"]).set_index("id_vino")
    perf_usuario = df_user_interactions.merge(perf_items, on="id_vino")

    # agrego más datos del usuario al perfil de usuario
    user_data = df_usuarios[df_usuarios["id_usuario"] == id_usuario][["idioma_usuario", "es_premium", "seguidores", "seguidos", "cant_ratings", "cant_reviews"]]
    for col in user_data.columns:
        perf_usuario[col] = user_data[col].iloc[0]

    # Ponderación por características relevantes (region, varietal, bodega)
    for c in perf_usuario.columns:
        if c.startswith("region_") or c.startswith("varietal_") or c.startswith("bodega_") or c.startswith("cosecha_vino_"):
            perf_usuario[c] = perf_usuario[c] * perf_usuario["rating"]

    # Calcular perfil promedio del usuario y normalizar
    perf_usuario = perf_usuario.drop(columns=["id_vino", "rating"]).groupby("id_usuario").mean()
    perf_usuario = perf_usuario / perf_usuario.sum(axis=1).values[0]  # Normalización

    # Ponderar perfiles de ítems por perfil de usuario
    for g in perf_items.columns:
        perf_items[g] = perf_items[g] * perf_usuario[g].values[0]

    # Obtener vinos ignorados por el usuario
    ignorados_usuario = df_int[(df_int["id_usuario"] == id_usuario) & (df_int["rating"] == 0)]["id_vino"].tolist()

    # Obtener vinos probados o vistos por el usuario
    vinos_probados_o_vistos = df_int[df_int["id_usuario"] == id_usuario]["id_vino"].tolist()

    # Ordenar y seleccionar las recomendaciones basadas en el perfil del usuario
    recomendaciones = [l for l in perf_items.sum(axis=1).sort_values(ascending=False).index if l not in vinos_probados_o_vistos and l not in ignorados_usuario][:9]

    return recomendaciones


def recomendar_lightfm(id_usuario, interacciones="interacciones"):
    con = sqlite3.connect(os.path.join(THIS_FOLDER, "data/data.db"))
    df_int = pd.read_sql_query(f"SELECT * FROM {interacciones} WHERE rating > 0", con)
    df_items = pd.read_sql_query("SELECT * FROM vinos", con)
    con.close()

    # Crear y ajustar el dataset
    ds = lfm.data.Dataset()
    ds.fit(users=df_int["id_usuario"].unique(), items=df_items["id_vino"].unique())

    # Obtener los mapeos
    user_id_map, user_feature_map, item_id_map, item_feature_map = ds.mapping()
    (interactions, weights) = ds.build_interactions(df_int[["id_usuario", "id_vino", "rating"]].itertuples(index=False))

    # Entrenar el modelo LightFM
    model = lfm.LightFM(no_components=30, learning_rate=0.05, loss='warp', random_state=42)
    model.fit(interactions, sample_weight=weights, epochs=10)

    # Obtener vinos probados y no probados por el usuario
    vinos_probados = df_int.loc[df_int["id_usuario"] == id_usuario, "id_vino"].tolist()
    todos_los_vinos = df_items["id_vino"].tolist()
    vinos_no_probados = set(todos_los_vinos).difference(vinos_probados)

    # Verificar que el usuario esté en el mapeo
    if id_usuario not in user_id_map:
        print(f"Error: id_usuario {id_usuario} no se encuentra en el mapeo de usuarios")
        return []

    # Verificar que todos los vinos no probados estén en el mapeo de ítems
    item_ids_no_probados = [item_id_map.get(l) for l in vinos_no_probados if l in item_id_map]
    if len(item_ids_no_probados) != len(vinos_no_probados):
        print("Algunos vinos no se encuentran en el mapeo de ítems")

    # Realizar predicciones
    predicciones = model.predict(user_id_map[id_usuario], item_ids_no_probados)

    # Obtener las recomendaciones
    recomendaciones = sorted([(p, l) for (p, l) in zip(predicciones, vinos_no_probados)], reverse=True)[:9]
    recomendaciones = [vino[1] for vino in recomendaciones]
    
    return recomendaciones


def recomendar_surprise(id_usuario, interacciones="interacciones"):
    con = sqlite3.connect(os.path.join(THIS_FOLDER, "data/data.db"))
    df_int = pd.read_sql_query(f"SELECT * FROM {interacciones}", con)
    df_items = pd.read_sql_query("SELECT * FROM vinos", con)
    con.close()

    reader = sp.reader.Reader(rating_scale=(1, 10))

    data = sp.dataset.Dataset.load_from_df(df_int.loc[df_int["rating"] > 0, ['id_usuario', 'id_vino', 'rating']], reader)
    trainset = data.build_full_trainset()
    model = sp.prediction_algorithms.matrix_factorization.SVD(n_factors=500, n_epochs=20, random_state=42)
    model.fit(trainset)

    vinos_probados_o_vistos = df_int.loc[df_int["id_usuario"] == id_usuario, "id_vino"].tolist()
    todos_los_vinos = df_items["id_vino"].tolist()
    vinos_no_probados_ni_vistos = set(todos_los_vinos).difference(vinos_probados_o_vistos)

    predicciones = [model.predict(id_usuario, l).est for l in vinos_no_probados_ni_vistos]
    recomendaciones = sorted([(p, l) for (p, l) in zip(predicciones, vinos_no_probados_ni_vistos)], reverse=True)[:9]

    recomendaciones = [vino[1] for vino in recomendaciones]
    return recomendaciones


def recomendar_whoosh(id_usuario, interacciones="interacciones"):
    con = sqlite3.connect(os.path.join(THIS_FOLDER, "data/data.db"))
    df_int = pd.read_sql_query(f"SELECT * FROM {interacciones}", con)
    df_items = pd.read_sql_query("SELECT * FROM vinos", con)
    con.close()

    # TODO: usar cant
    terminos = []
    for campo in ["varietal", "bodega", "region"]:
        query = f"""
            SELECT {campo} AS valor, count(*) AS cant
            FROM interacciones AS i JOIN vinos AS v ON i.id_vino = v.id_vino
            WHERE id_usuario = ?
            AND rating > 0
            GROUP BY {campo}
            HAVING cant > 1
            ORDER BY cant DESC
            LIMIT 3
        """
        rows = sql_select(query, (id_usuario,))

        for row in rows:
            terminos.append(wh.query.Term(campo, row["valor"]))

    query = wh.query.Or(terminos)

    vinos_probados_o_vistos = df_int.loc[df_int["id_usuario"] == id_usuario, "id_vino"].tolist()

    ix = wh.index.open_dir("indexdir")
    with ix.searcher() as searcher:
        results = searcher.search(query, terms=True, scored=True, limit=1000)
        recomendaciones = [r["id_vino"] for r in results if r not in vinos_probados_o_vistos][:9]

    return recomendaciones


def recomendar(id_usuario, interacciones="interacciones", id_vino=None):
    # Obtener cantidad de vinos valorados por el usuario
    cant_valorados = len(valorados(id_usuario, interacciones))
    algoritmo = ""

    # Si el usuario está en la ruta detalle_vino, usar recomendador_asociados
    if flask_app.request.path.startswith('/detalle_vino'):     
        algoritmo = "vinos relacionados"
        print("recomendador: vinos relacionados", file=sys.stdout)
        resultados = recomendador_asociados(id_vino, id_usuario)
        id_vinos = resultados[0]

    # Si el usuario ha valorado menos de 5 vinos, usar top9
    elif cant_valorados <= 5:       
        algoritmo = "top9"
        print("recomendador: top9", file=sys.stdout)
        id_vinos = recomendar_top_9(id_usuario, interacciones)

    # Si el usuario ha valorado entre 6 y 13 vinos, usar perfil
    elif cant_valorados <= 13:        
        algoritmo = "perfil"
        print("recomendador: perfil", file=sys.stdout)
        id_vinos = recomendar_perfil(id_usuario, interacciones)

    # Si el usuario ha valorado más de 10 vinos, usar surprise
    else:       
        algoritmo = "surprise"
        print("recomendador: surprise", file=sys.stdout)
        id_vinos = recomendar_surprise(id_usuario, interacciones)
        #algoritmo = "lightfm"
        #print("recomendador: lightfm", file=sys.stdout)
        #id_vinos = recomendar_lightfm(id_usuario, interacciones)
        #algoritmo = "whoosh"
        #print("recomendador: whoosh", file=sys.stdout)
        #id_vinos = recomendar_whoosh(id_usuario, interacciones)

    # Obtener los datos de los vinos recomendados
    recomendaciones = datos_vinos(id_vinos)

    return recomendaciones, algoritmo

