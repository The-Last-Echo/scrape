import requests
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import unquote
import time

def handler(request):
    # Headers CORS
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Content-Type': 'application/json'
    }
    
    # Gérer les requêtes OPTIONS (preflight)
    if request.method == 'OPTIONS':
        return ('', 200, headers)
    
    try:
        # Récupérer l'URL depuis les paramètres
        url = request.args.get('url')
        if not url:
            return (json.dumps({'error': 'URL manquante'}), 400, headers)
        
        # Décoder l'URL
        url = unquote(url)
        
        # Valider l'URL
        if not url.startswith('https://anime-sama.fr/catalogue/'):
            return (json.dumps({'error': 'URL invalide'}), 400, headers)
        
        # Headers pour simuler un navigateur
        request_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # Faire la requête avec timeout
        response = requests.get(url, headers=request_headers, timeout=10)
        response.raise_for_status()
        
        # Parser le HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extraire les données
        data = extract_anime_data(soup, url)
        
        return (json.dumps(data, ensure_ascii=False), 200, headers)
        
    except requests.exceptions.RequestException as e:
        return (json.dumps({'error': f'Erreur réseau: {str(e)}'}), 500, headers)
    except Exception as e:
        return (json.dumps({'error': f'Erreur serveur: {str(e)}'}), 500, headers)

def extract_anime_data(soup, url):
    """Extraire les données de l'anime depuis le HTML"""
    
    # Extraire le nom depuis l'URL
    anime_name = url.split('/')[-2] if url.endswith('/') else url.split('/')[-1]
    
    # Titre
    title = ""
    title_element = soup.find('title')
    if title_element:
        title = title_element.get_text().strip()
        title = re.sub(r'\s*-\s*Anime[- ]Sama.*$', '', title, flags=re.IGNORECASE)
    
    if not title:
        h1 = soup.find('h1')
        if h1:
            title = h1.get_text().strip()
    
    if not title:
        title = anime_name.replace('-', ' ').title()
    
    # Synopsis
    synopsis = ""
    synopsis_selectors = [
        'section#synopsis p',
        '.synopsis p',
        'div.description p',
        'p:contains("Synopsis")'
    ]
    
    for selector in synopsis_selectors:
        if ':contains(' in selector:
            # Recherche manuelle pour :contains
            for p in soup.find_all('p'):
                if 'synopsis' in p.get_text().lower():
                    next_p = p.find_next_sibling('p')
                    if next_p:
                        synopsis = next_p.get_text().strip()
                        break
        else:
            element = soup.select_one(selector)
            if element:
                synopsis = element.get_text().strip()
                break
        if synopsis:
            break
    
    # Genres
    genres = []
    genre_elements = soup.select('a[href*="genre"], .genre a, .genres a')
    for element in genre_elements:
        genre_text = element.get_text().strip()
        if genre_text:
            genres.append(genre_text.lower())
    
    # Mapper les genres français
    genre_mapping = {
        'action': 'action',
        'aventure': 'aventure',
        'comédie': 'comedie',
        'drame': 'drame',
        'fantastique': 'fantastique',
        'horreur': 'horreur',
        'mystère': 'mystere',
        'romance': 'romance',
        'science-fiction': 'science-fiction',
        'thriller': 'thriller',
        'slice of life': 'slice-of-life',
        'sport': 'sport',
        'surnaturel': 'surnaturel',
        'historique': 'historique',
        'musical': 'musical'
    }
    
    mapped_genres = []
    for genre in genres:
        for key, value in genre_mapping.items():
            if key in genre:
                if value not in mapped_genres:
                    mapped_genres.append(value)
    
    if not mapped_genres:
        mapped_genres = ['action']
    
    # Année
    year = 2024
    year_match = re.search(r'\b(19|20)\d{2}\b', str(soup))
    if year_match:
        year = int(year_match.group())
    
    # Saisons et épisodes
    season_links = soup.select('a[href*="saison"]')
    seasons = max(len(season_links), 1)
    episodes = seasons * 12  # Estimation
    
    # Studio
    studio = "Anime-Sama"
    studio_selectors = ['.studio', '.production', 'span:contains("Studio")']
    for selector in studio_selectors:
        if ':contains(' in selector:
            for span in soup.find_all('span'):
                if 'studio' in span.get_text().lower():
                    studio = span.get_text().strip()
                    break
        else:
            element = soup.select_one(selector)
            if element:
                studio = element.get_text().strip()
                break
        if studio != "Anime-Sama":
            break
    
    # Générer l'URL de l'image
    image_url = f"https://cdn.statically.io/gh/Anime-Sama/IMG/img/contenu/{anime_name}.jpg"
    
    return {
        'title': title,
        'synopsis': synopsis or f"Découvrez {title}, un anime captivant qui vous emmènera dans une aventure extraordinaire.",
        'imageUrl': image_url,
        'backdropUrl': image_url,
        'genre': mapped_genres,
        'rating': 0,
        'year': year,
        'episodes': episodes,
        'seasons': seasons,
        'duration': '24 min',
        'studio': studio,
        'tags': [anime_name, 'anime', 'japonais'] + mapped_genres
    }