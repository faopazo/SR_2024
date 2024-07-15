import requests
import pandas as pd

# Se corre primero, a partir de los vinos obtengo luego reviews y usuarios,
#  este script lo corrí varias veces para extraer distinta información desde distintas secciones

def get_wines(page):
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0"
    }

    # ir cambiando pais
    #api_url = f'https://www.vivino.com/api/explore/explore?min_rating=1&order_by=ratings_count&order=desc&page={page}'
    api_url = f"https://www.vivino.com/api/explore/explore?country_code=ES&country_codes[]=es&currency_code=ARS&grape_filter=varietal&min_rating=1&page={page}&price_range_max=100000&price_range_min=0&order_by=ratings_count&order=desc&wine_type_ids[]=1"
    
    #api_url = f'https://www.vivino.com/api/explore/explore?country_code=AR&country_codes[]=es&currency_code=ARS&grape_filter=varietal&min_rating=1&order_by=ratings_count&order=desc&price_range_max=49900&price_range_min=0&wine_type_ids%5B%5D=1&wine_type_ids%5B%5D=2&wine_type_ids%5B%5D=3&wine_type_ids%5B%5D=4&wine_type_ids%5B%5D=7&wine_type_ids%5B%5D=24&page={page}&language=es'
 

    response = requests.get(api_url, headers=headers)
    data = response.json()

    wines = []
    for match in data["explore_vintage"]["matches"]:
        winery_name = match["vintage"]["wine"]["winery"]["name"]
        year = match["vintage"]["year"]
        wine_id = match["vintage"]["wine"]["id"]
        wine_name = f'{match["vintage"]["wine"]["name"]} {year}'
        pais = match["vintage"]["wine"]["region"]["country"]["name"]
        region = match["vintage"]["wine"]["region"]["name"]
        price = match['price']['amount']
      
        try:
            varietal_name = match['vintage']['wine']['style'].get('varietal_name')
            description = match['vintage']['wine']['style']['description']
            body_description = match['vintage']['wine']['style']['body_description']
    #maridajes e imágenes 
            food_1 = match['vintage']['wine']['style']['food'][0]['name']
            food_1_img = match['vintage']['wine']['style']['food'][0]['background_image']['variations']['small']
            food_2 = match['vintage']['wine']['style']['food'][1]['name']
            food_2_img = match['vintage']['wine']['style']['food'][1]['background_image']['variations']['small']
            food_3 = match['vintage']['wine']['style']['food'][2]['name']
            food_3_img = match['vintage']['wine']['style']['food'][2]['background_image']['variations']['small']
            food_4 = match['vintage']['wine']['style']['food'][3]['name']
            food_4_img = match['vintage']['wine']['style']['food'][3]['background_image']['variations']['small']
            food_5 = match['vintage']['wine']['style']['food'][4]['name']
            food_5_img = match['vintage']['wine']['style']['food'][4]['background_image']['variations']['small']
            food_6 = match['vintage']['wine']['style']['food'][5]['name']
            food_6_img = match['vintage']['wine']['style']['food'][5]['background_image']['variations']['small']  
    #grupos gustos
            flavor_1 = match['vintage']['wine']['taste']['flavor'][0]['group']           
            flavor_1_count = match['vintage']['wine']['taste']['flavor'][0]['stats']['count'] 
            flavor_2 = match['vintage']['wine']['taste']['flavor'][1]['group']           
            flavor_2_count = match['vintage']['wine']['taste']['flavor'][1]['stats']['count']
            flavor_3 = match['vintage']['wine']['taste']['flavor'][2]['group']           
            flavor_3_count = match['vintage']['wine']['taste']['flavor'][2]['stats']['count']
            flavor_4 = match['vintage']['wine']['taste']['flavor'][3]['group']           
            flavor_4_count = match['vintage']['wine']['taste']['flavor'][3]['stats']['count']           
            flavor_5 = match['vintage']['wine']['taste']['flavor'][4]['group']           
            flavor_5_count = match['vintage']['wine']['taste']['flavor'][4]['stats']['count']
            flavor_6 = match['vintage']['wine']['taste']['flavor'][5]['group']           
            flavor_6_count = match['vintage']['wine']['taste']['flavor'][5]['stats']['count']            
    #estructura
            acidity = match["vintage"]["wine"]["taste"]["structure"]['acidity']
            fizziness = match["vintage"]["wine"]["taste"]["structure"].get("fizziness")
            intensity = match["vintage"]["wine"]["taste"]["structure"].get("intensity")
            sweetness = match["vintage"]["wine"]["taste"]["structure"].get("sweetness")
            tannin = match["vintage"]["wine"]["taste"]["structure"].get("tannin")
        
        except AttributeError:
            varietal_name, description, body_description, food_1, food_2, food_3, food_4, food_5, food_6, flavor_1, flavor_1_count, flavor_2, flavor_2_count, flavor_3, flavor_3_count, flavor_4, flavor_4_count, flavor_5, flavor_5_count, flavor_6, flavor_6_count, acidity, fizziness, intensity, sweetness, tannin, food_1_img, food_2_img, food_3_img, food_4_img, food_5_img, food_6_img = None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None
        
        except IndexError:
            varietal_name, description, body_description, food_1, food_2, food_3, food_4, food_5, food_6, flavor_1, flavor_1_count, flavor_2, flavor_2_count, flavor_3, flavor_3_count, flavor_4, flavor_4_count, flavor_5, flavor_5_count, flavor_6, flavor_6_count, acidity, fizziness, intensity, sweetness, tannin, food_1_img, food_2_img, food_3_img, food_4_img, food_5_img, food_6_img = None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None
            
        rating_average = match["vintage"]["statistics"]["ratings_average"]
        num_reviews = match["vintage"]["statistics"]["ratings_count"]
        image = match["vintage"]["image"]["location"]
        
        wines.append([winery_name, year, wine_id, wine_name, pais, region, price, varietal_name, description,
                      body_description, food_1, food_2, food_3, food_4, food_5, food_6, flavor_1, 
                      flavor_1_count, flavor_2, flavor_2_count, flavor_3, flavor_3_count, flavor_4, 
                      flavor_4_count, flavor_5, flavor_5_count, flavor_6, flavor_6_count,
                      acidity, fizziness, intensity, sweetness, tannin, rating_average, num_reviews, image,
                      food_1_img, food_2_img, food_3_img, food_4_img, food_5_img, food_6_img])
    
    return wines

# Obtener listado de vinos
wines = []
for page in range(400):  # Cantidad de páginas a explorar
    wines += get_wines(page)

# Convertir a DataFrame
wines_df = pd.DataFrame(wines, columns=["bodega", "cosecha_vino", "id_vino", "vino", "pais", "region", "precio",
                                        "varietal", "descripcion", "descripcion_cuerpo", "maridaje_1", 
                                        "maridaje_2", "maridaje_3", "maridaje_4", "maridaje_5", "maridaje_6", 
                                        "gusto_1", "menciones_gusto_1", "gusto_2", "menciones_gusto_2",
                                        "gusto_3", "menciones_gusto_3", "gusto_4", "menciones_gusto_4",
                                        "gusto_5", "menciones_gusto_5", "gusto_6", "menciones_gusto_6",
                                        "acidez", "efervecencia", "intensidad", "dulzura", "tanino",
                                        "rating_vino", "cant_reviews", "imagen", "maridaje_1_viv", 
                                        "maridaje_2_viv", "maridaje_3_viv", "maridaje_4_viv", 
                                        "maridaje_5_viv", "maridaje_6_viv"])

print(wines_df.head())

# Eliminar duplicados
unique_wines_df = wines_df.drop_duplicates(subset=["cosecha_vino", "id_vino", "vino"])

# Guardar en CSV
unique_wines_df.to_csv("vinosmas.csv", index=False)

print("Listado de vinos guardado en 'vinosmas.csv'")
