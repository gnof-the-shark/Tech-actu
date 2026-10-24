# Tech-actu

Convertisseur **ACSM → ePub/PDF** côté navigateur (sans serveur).

## Fonctionnement

- Charge un fichier `.acsm` en local
- Extrait les métadonnées principales (titre, auteur, éditeur, langue, date)
- Permet de saisir un identifiant/mot de passe Adobe avant tentative de récupération
- Tente de récupérer le fichier final (`.epub`/`.pdf`) depuis l’URL trouvée dans l’ACSM
- Permet d’exporter les informations extraites en JSON

## Limites

- Un fichier ACSM n’est pas un eBook: c’est un ticket de téléchargement
- La plupart des ACSM Adobe DRM demandent une authentification/licence externe
- Le formulaire d’identifiants n’implémente pas toute la chaîne d’autorisation ADE (appareil/DRM Adobe)
- En conséquence, la récupération directe peut échouer dans un navigateur pur
