import sqlite3
import pandas as pd
import os
import math
import recomendar

# Evaluo los recomendadores en un conjunto "no visto" con las interacciones con fechas más recientes,
# simulando nuevas interacciones

# elimino datos previos
recomendar.sql_execute("DELETE FROM interacciones_train")
recomendar.sql_execute("DELETE FROM interacciones_test")

# filtro usuarios con al menos 20 interacciones
id_usuarios = recomendar.sql_select("SELECT id_usuario FROM interacciones GROUP BY id_usuario HAVING COUNT(*) >= 20")

# procesar interacciones para cada usuario
for row_usuario in id_usuarios:
    # todas las interacciones del usuario ordenadas por fecha
    id_vinos = recomendar.sql_select("SELECT * FROM interacciones WHERE id_usuario = ? ORDER BY fecha", (row_usuario["id_usuario"], ))
    
    # punto de corte para el 80% de las interacciones más antiguas (entrenamiento) y el 20% más recientes (prueba)
    cant_train = int(len(id_vinos) * 0.8)
    print(("cantidad_train:"), cant_train)
    
    print(id_vinos[:cant_train])
    # inserto las interacciones en el conjunto de entrenamiento
    for row in id_vinos[:cant_train]:
        recomendar.sql_execute("INSERT INTO interacciones_train(id_vino, id_usuario, rating, fecha) VALUES (?, ?, ?, ?)", 
                               (row["id_vino"], row["id_usuario"], row["rating"], row["fecha"]))
    
    # inserto las interacciones en el conjunto de prueba
    for row in id_vinos[cant_train:]:
        recomendar.sql_execute("INSERT INTO interacciones_test(id_vino, id_usuario, rating, fecha) VALUES (?, ?, ?, ?)", 
                               (row["id_vino"], row["id_usuario"], row["rating"], row["fecha"]))
        recomendar.sql_execute("DELETE FROM interacciones_train WHERE id_usuario = ? AND id_vino = ?", 
                               (row["id_usuario"], row["id_vino"]))
    print(f"Usuario procesado: {row_usuario['id_usuario']}")

# Funciones de métrica
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

# Evaluar recomendaciones
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
