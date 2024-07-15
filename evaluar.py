import sqlite3
import pandas as pd
import os
import math
import recomendar

recomendar.sql_execute("DELETE FROM interacciones_train")
recomendar.sql_execute("INSERT INTO interacciones_train SELECT * FROM interacciones")
recomendar.sql_execute("DELETE FROM interacciones_test")

id_usuarios = recomendar.sql_select("SELECT id_usuario FROM interacciones GROUP BY id_usuario HAVING COUNT(*) >= 20")
for row_usuario in id_usuarios:
    id_vinos = recomendar.sql_select("SELECT * FROM interacciones WHERE id_usuario = ?", (row_usuario["id_usuario"], ))
    cant_train = int(len(id_vinos) * 0.8)

    print(("cantidad_train:"), cant_train)
    
    print(id_vinos[:cant_train])
    for row in id_vinos[:cant_train]:
        recomendar.sql_execute("INSERT INTO interacciones_train(id_vino, id_usuario, rating) VALUES (?, ?, ?)", 
                               (row["id_vino"], row_usuario["id_usuario"], row["rating"]))
    
    for row in id_vinos[cant_train:]:
        recomendar.sql_execute("INSERT INTO interacciones_test(id_vino, id_usuario, rating) VALUES (?, ?, ?)", 
                               (row["id_vino"], row_usuario["id_usuario"], row["rating"]))
        recomendar.sql_execute("DELETE FROM interacciones_train WHERE id_usuario = ? AND id_vino = ?", 
                               (row_usuario["id_usuario"], row["id_vino"]))
    print(row_usuario["id_usuario"])

def ndcg(groud_truth, recommendation):
    dcg = 0
    idcg = 0
    for i, r in enumerate(recommendation):
        rel = int(r in groud_truth)
        dcg += rel / math.log2(i+1+1)
        idcg += 1 / math.log2(i+1+1)

    return dcg / idcg

def precision_at(ground_truth, recommendation, n=9):
    return len(set(ground_truth[:n-1]).intersection(recommendation[:len(ground_truth[:n-1])])) / len(ground_truth[:n-1])

id_usuarios = recomendar.sql_select("SELECT DISTINCT id_usuario FROM interacciones_test")

for row in id_usuarios:
    vinos_probados = [row["id_vino"] for row in recomendar.sql_select("SELECT DISTINCT id_vino FROM interacciones_test WHERE id_usuario = ?", (row["id_usuario"],))]
    #recomendacion = recomendar.recomendar_top_9(row["id_usuario"], interacciones="interacciones_test")
    #recomendacion = recomendar.recomendar_perfil(row["id_usuario"], interacciones="interacciones_test")
    recomendacion = recomendar.recomendar_surprise(row["id_usuario"], interacciones="interacciones_test")
    #recomendacion_asociados = recomendar.recomendador_asociados(row["id_usuario"], interacciones="interacciones_test")
    #recomendacion = recomendacion_asociados[0]
    #recomendacion = recomendar.recomendar_lightfm(row["id_usuario"], interacciones="interacciones_test")
    #recomendacion = recomendar.recomendar_whoosh(row["id_usuario"], interacciones="interacciones_test")
    p = precision_at(vinos_probados, recomendacion)
    n = ndcg(vinos_probados, recomendacion)
    print(f"{row['id_usuario']}\t\tndcg: {n:.5f}\tprecision@9: {p: .5f}")
