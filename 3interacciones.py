import requests
import pandas as pd

# esta fue la "primera" versión para extraer las reviews, 
# después en resenas_y_usuarios (versión final) extraje a la vez la info de usuarios

def get_reviews(wine_id, year, page=3, per_page=300):
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0"
    }

    api_url = f"https://www.vivino.com/api/wines/{wine_id}/reviews?per_page={per_page}&year={year}&page={page}&language=es"
    
    response = requests.get(api_url, headers=headers)
    data = response.json()
    print(data)
    
    reviews = []
    if "reviews" in data:  # Verificar si la clave "reviews" está presente en la respuesta
        for review in data["reviews"]:
            user_id = review["user"]["id"]
            user_rating = review["rating"]
            note = review["note"]
            language = review["language"]
            created_at = review["created_at"]
            reviews.append([wine_id, year, vino, user_id, user_rating, note, language, created_at])
    else:
        print("No se encontraron revisiones para este vino en este año.")
    
    return reviews


# Cargar los vinos desde el archivo CSV
wines_df = pd.read_csv("vinos.csv")

# Obtener listado de revisiones de vinos
reviews = []
for _, wine in wines_df.iterrows():
    wine_id = wine["id_vino"]
    year = wine["cosecha_vino"]
    vino = wine['vino']
    wine_reviews = get_reviews(wine_id, year)
    reviews += wine_reviews

# Convertir a DataFrame
reviews_df = pd.DataFrame(reviews, columns=["id_vino", "cosecha", "vino", "id_usuario", "rating", "nota", "idioma_nota", "fecha"])

# Guardar en CSV
reviews_df.to_csv("interacciones.csv", index=False)

print("Listado de revisiones guardado en 'interacciones.csv'")