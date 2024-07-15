import requests
import pandas as pd

# esta fue la "primera" versión para extraer info de usuarios, 
# después en resenas_y_usuarios (versión final) extraje a la vez las reviews y la info de usuarios

def get_user_data(user_id):
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
    }

    api_url = f"https://www.vivino.com/api/users/{user_id}"

    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()  # Verificar si hay errores en la respuesta HTTP
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener datos del usuario {user_id}: {e}")
        return None

# Cargar el archivo de interacciones.csv que contiene las revisiones de los vinos
interacciones_df = pd.read_csv("interacciones.csv")

# Extraer los IDs únicos de usuario de las reviews
user_ids = interacciones_df["id_usuario"].unique()

# Obtener información única de usuarios
unique_users = []
processed_user_ids = set()  # Mantener un registro de los IDs de usuario procesados

for user_id in user_ids:
    if user_id in processed_user_ids:
        continue  # Si el usuario ya ha sido procesado, continuar con el siguiente
    user_data = get_user_data(user_id)
    print(user_data)
    if user_data:
        user_info = user_data["user"]
        unique_users.append({
            "id_usuario": user_id,
            "seo_nombre": user_info["seo_name"],
            "alias": user_info.get("alias", ""),
            "es_premium": user_info["is_premium"],
            "seguidores": user_info["statistics"]["followers_count"],
            "seguidos": user_info["statistics"]["followings_count"],
            "cant_ratings": user_info["statistics"]["ratings_count"],
            "cant_reviews": user_info["statistics"]["reviews_count"],
            "idioma_usuario": user_info["language"]
        })
        processed_user_ids.add(user_id)  # Agregar el ID de usuario a los procesados

# Convertir a DataFrame
unique_users_df = pd.DataFrame(unique_users)

# Guardar en CSV
unique_users_df.to_csv("usuarios.csv", index=False)

print("Listado de usuarios únicos guardado en 'usuarios.csv'")
