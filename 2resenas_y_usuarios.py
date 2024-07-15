import requests
import pandas as pd
import time

# se corre segundo, a partir de los vinos extraidos en vinos.py

def get_reviews(wine_id, year, page=1, per_page=300):
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0"
    }

    api_url = f"https://www.vivino.com/api/wines/{wine_id}/reviews?per_page={per_page}&year={year}&page={page}&language=es"
    
    response = requests.get(api_url, headers=headers)
    try:
        data = response.json()
        reviews = []
        if "reviews" in data:
            for review in data["reviews"]:
                user_id = review["user"]["id"]
                user_rating = review["rating"]
                note = review["note"]
                language = review["language"]
                created_at = review["created_at"]
                seo_nombre = review["user"]["seo_name"]
                alias = review["user"]["alias"]
                es_premium = review["user"]["is_premium"]
                seguidores = review["user"]["statistics"]["followers_count"]
                seguidos = review["user"]["statistics"]["followings_count"]
                cant_ratings = review["user"]["statistics"]["ratings_count"]
                cant_reviews = review["user"]["statistics"]["reviews_count"]
                idioma_usuario = review["user"]["language"]
                reviews.append([wine_id, year, vino, user_id, user_rating, note, language, created_at, seo_nombre, alias, es_premium, seguidores, seguidos, cant_ratings, cant_reviews, idioma_usuario])
        else:
            print("No se encontraron revisiones para este vino en este año.")
        return reviews
    except ValueError as e:
        print(f"Error al obtener las revisiones del vino con ID {wine_id}. Mensaje de error: {e}")
        return []

# Cargar los vinos desde el archivo CSV
#wines_df = pd.read_csv("todos.csv", dtype={"id": "str", "cosecha_vino": "str", "vino": "str", "precio": "float64", "varietal": "str"})
wines_df = pd.read_csv("Argentina.csv") #, usecols=["id", "vino", "cosecha_vino"])

# Obtener listado de reviews de vinos
reviews = []
for _, wine in wines_df.iterrows():
    wine_id = wine["id"] #id_vino
    year = wine["cosecha_vino"]
    vino = wine['vino']
    wine_reviews = get_reviews(wine_id, year)
    reviews += wine_reviews
    # Duerme durante unos segundos para evitar la sobrecarga del servidor
    time.sleep(2)

# Convertir a DataFrame
reviews_df = pd.DataFrame(reviews, columns=["id_vino", "cosecha", "vino", "id_usuario", "rating", "nota", "idioma_nota", "fecha", "seo_nombre", "alias", "es_premium", "seguidores", "seguidos", "cant_ratings", "cant_reviews", "idioma_usuario"])

# Guardar en CSV
reviews_df.to_csv("interacciones_usuariosarg1.csv", index=False)

print("Listado de revisiones guardado en 'interacciones_usuariosarg1.csv'")
