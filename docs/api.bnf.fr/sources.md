# Sources de vérification

Vérification effectuée le 2 septembre 2026, complétée le 8 septembre 2026.

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


## Mesures du 8 septembre 2026

Relevés effectués par exécution réelle contre `gallica.bnf.fr`, chaque série encadrée par des requêtes témoins.

### Vérification anti-robot sur les adresses du site web

Après treize minutes sans aucune requête, quatre appels espacés de vingt secondes :

| Adresse | Statut | Type | Taille | Page de vérification |
|---|---|---|---|---|
| `/services/Pagination` | 200 | `application/xml` | 59 108 o | non |
| `ark:/12148/…​.texteBrut` | 200 | `text/html` | 50 212 o | **oui** |
| `ark:/12148/…​.pdf` | 200 | `text/html` | 50 212 o | **oui** |
| `RequestDigitalElement` (ALTO) | 200 | `application/xml` | 6 102 o | non |

Les deux témoins écartent l’hypothèse d’une limitation passagère de l’adresse de test.

### Agents utilisateurs refusés

Même URL, même minute, seul l’en-tête `User-Agent` change :

| En-tête envoyé | Statut |
|---|---|
| aucun | 200 |
| chaîne identifiant un projet | 200 |
| agents par défaut de plusieurs bibliothèques HTTP courantes | **403** |

Aucune mention de ce comportement sur `https://api.bnf.fr/fr/node/232` : recherche infructueuse pour « user-agent », « agent », « 403 » et « Forbidden ».

### Encodage des fichiers ALTO

Déclaration du document : `encoding="ISO-8859-1"`. En-tête HTTP : `charset=UTF-8`. Contenu réel : UTF-8. Un analyseur XML conforme suit la déclaration et abîme les caractères accentués — 33 mots sur une seule page de l’exemplaire testé.

### Routes d’extraction du texte

`E=TEXTE_BRUT` et `E=TEXT` sur `RequestDigitalElement` renvoient `403` : `E=ALTO` est la seule valeur donnant le texte océrisé.
