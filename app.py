from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import re
import os

app = Flask(__name__)
CORS(app)  # Activer CORS pour toutes les routes

@app.route('/scrape', methods=['GET', 'POST'])
def scrape_anime():
    try:
        # Récupérer l'URL
        if request.method == 'GET':
            url = request.args.get('url')
        else:
            data = request.get_json()
            url = data.get('url') if data else None
        
        if not url:
            return jsonify({'error': 'URL manquante'}), 400
        
        # Valider l'URL
        if not url.startswith('https://anime-sama.fr/catalogue/'):
            return jsonify({'error': 'URL invalide'}), 400
        
        # Headers pour simuler un navigateur
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # Faire la requête
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Vérifier si c'est une page 404
        if '404' in response.text or 'not found' in response.text.lower():
            return jsonify({'error': 'Anime non trouvé (404)'}), 404
        
        # Parser le HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extraire les données
        data = extract_anime_data(soup, url)
        
        return jsonify(data)
        
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Timeout - Le site met trop de temps à répondre'}), 408
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Erreur réseau: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Erreur serveur: {str(e)}'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'OK', 'message': 'Serveur de scraping opérationnel'})

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'message': 'API de scraping Anime-Sama',
        'endpoints': {
            '/scrape': 'GET/POST - Scraper un anime (param: url)',
            '/health': 'GET - Vérifier le statut du serveur'
        },
        'example': '/scrape?url=https://anime-sama.fr/catalogue/demon-slayer/'
    })

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
    
    # Chercher "Synopsis" dans les h2
    for h2 in soup.find_all('h2'):
        if 'synopsis' in h2.get_text().lower():
            next_element = h2.find_next_sibling()
            while next_element:
                if next_element.name == 'p' and next_element.get_text().strip():
                    synopsis = next_element.get_text().strip()
                    break
                next_element = next_element.find_next_sibling()
            break
    
    # Fallback pour le synopsis
    if not synopsis:
        synopsis_selectors = ['section#synopsis p', '.synopsis p', 'div.description p']
        for selector in synopsis_selectors:
            element = soup.select_one(selector)
            if element:
                synopsis = element.get_text().strip()
                break
    
    # Genres
    genres = []
    
    # Chercher "Genres" dans les h2
    for h2 in soup.find_all('h2'):
        if 'genre' in h2.get_text().lower():
            next_element = h2.find_next_sibling()
            while next_element and next_element.name != 'h2':
                genre_links = next_element.find_all('a') if hasattr(next_element, 'find_all') else []
                for link in genre_links:
                    genre_text = link.get_text().strip()
                    if genre_text:
                        genres.append(genre_text.lower())
                next_element = next_element.find_next_sibling()
            break
    
    # Fallback pour les genres
    if not genres:
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
        'comedy': 'comedie',
        'drame': 'drame',
        'drama': 'drame',
        'fantastique': 'fantastique',
        'fantasy': 'fantastique',
        'horreur': 'horreur',
        'horror': 'horreur',
        'mystère': 'mystere',
        'mystery': 'mystere',
        'romance': 'romance',
        'science-fiction': 'science-fiction',
        'sci-fi': 'science-fiction',
        'thriller': 'thriller',
        'slice of life': 'slice-of-life',
        'sport': 'sport',
        'surnaturel': 'surnaturel',
        'supernatural': 'surnaturel',
        'historique': 'historique',
        'historical': 'historique',
        'musical': 'musical',
        'music': 'musical'
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
    
    # Analyser les saisons depuis les liens panneauAnime
    seasons = 1
    episodes = 12
    
    # Chercher les appels panneauAnime dans le JavaScript
    script_tags = soup.find_all('script')
    for script in script_tags:
        if script.string:
            panneau_matches = re.findall(r'panneauAnime\s*\(\s*["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']\s*\)', script.string)
            if panneau_matches:
                season_count = 0
                for nom, url_part in panneau_matches:
                    if re.match(r'^saison\d+/vostfr$', url_part):
                        season_count += 1
                
                if season_count > 0:
                    seasons = season_count
                    episodes = seasons * 12  # Estimation
                break
    
    # Studio
    studio = "Anime-Sama"
    
    # Générer l'URL de l'image
    clean_name = re.sub(r'[^a-z0-9-]', '-', anime_name.lower())
    clean_name = re.sub(r'-+', '-', clean_name).strip('-')
    image_url = f"https://cdn.statically.io/gh/Anime-Sama/IMG/img/contenu/{clean_name}.jpg"
    
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)