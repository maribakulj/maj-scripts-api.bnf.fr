# Sources de vérification

Vérification effectuée le 2 septembre 2026.

## api.bnf.fr

- Wrappers pour les API Gallica : `https://api.bnf.fr/fr/wrapper-python-pour-les-api-gallica`
  - fiche datée de 2021 ;
  - référence PyGallica, Gallipy, fdh-gallica, Pyllica, bnfimage et gargallica ;
  - exemple PyGallica IIIF actuellement publié avec parenthèse fermante manquante.

- Pyllica : `https://api.bnf.fr/fr/extracteur-python-de-corpus-de-periodiques`
  - fiche datée de 2025 ;
  - exemple IIIF en 3000 px ;
  - suggestion explicite de passer à 5000 px ;
  - avertissement historique concernant `gallicalabs.bnf.fr`.

- API IIIF Gallica : `https://api.bnf.fr/fr/api-iiif-de-recuperation-des-images-de-gallica`
  - fiche datée de 2025 ;
  - version affichée : 2 ;
  - exemples Image et Presentation.

- API Gallica / limites d’usage : `https://api.bnf.fr/fr/node/232`
  - IIIF `full/full` ou >1000 px : 5 appels/minute ;
  - `.texteBrut` : 5 appels/minute ;
  - `.PDF` : 4 appels/minute ;
  - `.highres` : 50 appels/minute ;
  - dépassement : HTTP 429.

- API Document Gallica : `https://api.bnf.fr/fr/api-document-de-gallica`
  - service `Issues` ;
  - `OAIRecord`, `Pagination`, `ContentSearch`, ALTO et texte brut.

## Projets tiers

État GitHub vérifié via l’API GitHub le 2 septembre 2026 :

- `ian-nai/PyGallica` : dépôt public archivé ;
- `GeoHistoricalData/gallipy` : dépôt public non archivé ;
- `Dorialexander/Pyllica` : dépôt public non archivé ;
- `Rekyt/bnfimage` : dépôt public non archivé ;
- `GuillaumePressiat/gargallica` : dépôt public non archivé.

Le drapeau GitHub `archived=false` ne constitue pas à lui seul une preuve de maintenance active.

## fdh-gallica

URL actuellement liée par api.bnf.fr :

`https://fdh.epfl.ch/index.php/Gallica_wrapper`

La récupération a expiré lors de la vérification du 2 septembre 2026. Le statut retenu est donc « lien/projet non vérifié », pas « projet définitivement disparu ».
