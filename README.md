# Tech-actu

Convertisseur **ACSM → ePub/PDF** côté navigateur (sans serveur).

## Fonctionnement

- Charge un fichier `.acsm` en local
- Extrait les métadonnées principales (titre, auteur, éditeur, langue, date)
- Tente de récupérer le fichier final (`.epub`/`.pdf`) depuis l’URL trouvée dans l’ACSM
- Permet d’exporter les informations extraites en JSON

## Limites

- Un fichier ACSM n’est pas un eBook: c’est un ticket de téléchargement
- La plupart des ACSM Adobe DRM demandent une authentification/licence externe
- En conséquence, la récupération directe peut échouer dans un navigateur pur
