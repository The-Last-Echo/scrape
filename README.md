# Serveur de Scraping Anime-Sama

## Déploiement sur Vercel (Gratuit)

1. **Créer un compte Vercel** : https://vercel.com
2. **Installer Vercel CLI** :
   ```bash
   npm i -g vercel
   ```
3. **Déployer** :
   ```bash
   cd scraper-server
   vercel --prod
   ```

## Utilisation

Une fois déployé, votre API sera disponible à :
```
https://votre-projet.vercel.app/api/scrape?url=https://anime-sama.fr/catalogue/demon-slayer/
```

## Test local

```bash
pip install -r requirements.txt
vercel dev
```

## Avantages Vercel
- ✅ Gratuit (500GB de bande passante/mois)
- ✅ Déploiement automatique
- ✅ HTTPS inclus
- ✅ Pas de configuration serveur
- ✅ Scaling automatique