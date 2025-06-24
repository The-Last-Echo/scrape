# Serveur de Scraping Railway

## Déploiement sur Railway (Gratuit)

1. **Créer un compte Railway** : https://railway.app
2. **Connecter votre repo GitHub**
3. **Déployer automatiquement**

## Avantages Railway
- ✅ 500h gratuites/mois
- ✅ Déploiement Git automatique
- ✅ Base de données incluse
- ✅ Logs en temps réel
- ✅ Variables d'environnement

## Variables d'environnement (optionnelles)
- `PORT` : Port du serveur (auto-détecté)
- `FLASK_ENV` : production

## Endpoints
- `GET /` : Documentation de l'API
- `GET /health` : Vérification du statut
- `GET /scrape?url=...` : Scraper un anime
- `POST /scrape` : Scraper un anime (JSON body)