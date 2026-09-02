# Wrappers pour les API Gallica

Les API Gallica peuvent être appelées directement en HTTP. Plusieurs projets tiers proposent également des fonctions Python ou R facilitant certains usages. Ces projets ne sont pas des API BnF et leur présence dans cette page ne vaut ni garantie de maintenance ni support institutionnel.

## Avant d’utiliser un wrapper

Pour un nouveau projet, vérifier en priorité :

- la date de dernière mise à jour du projet ;
- les versions de Python ou R prises en charge ;
- la compatibilité avec les endpoints Gallica actuellement documentés ;
- la gestion des réponses HTTP, notamment `429 Too Many Requests` ;
- les limites d’usage publiées sur la page « API Gallica ».

Les exemples et correctifs de compatibilité audités en 2026 sont maintenus dans le dépôt `maribakulj/maj-scripts-api.bnf.fr` afin de rendre les écarts avec les projets historiques vérifiables et testables.

## Python

### PyGallica

PyGallica est un wrapper historique couvrant notamment la recherche SRU, l’API Document et IIIF. Le dépôt d’origine est archivé. Pour reproduire des scripts existants, utiliser la couche de compatibilité testée du dépôt de maintenance plutôt que de considérer le code historique comme un client de référence actuel.

Exemples compatibles :

```python
from search_api import Search

Search.search("Verdun")
```

```python
from document_api import Document

Document.oai("btv1b53066668g")
```

```python
from iiif_api import IIIF

IIIF.iiif("12148/btv1b53066668g/f1", "full", "1000", "0", "native", "jpg")
IIIF.metadata("12148/btv1b53066668g/f1")
```

L’exemple image utilise volontairement une largeur de 1000 pixels. Les requêtes `full/full` ou demandant plus de 1000 pixels relèvent actuellement d’une classe de requêtes IIIF limitée à 5 appels par minute.

### Gallipy

Gallipy est un projet tiers historique. L’audit 2026 a identifié des incompatibilités dans certaines fonctions asynchrones et dans le script historique de reconstruction PDF. Des correctifs de compatibilité et une implémentation `pypdf` moderne sont disponibles dans le dépôt de maintenance.

### fdh-gallica

La ressource historique EPFL liée depuis api.bnf.fr n’a pas pu être récupérée lors de la vérification du 2 septembre 2026. Tant que le lien et l’état du projet n’ont pas été confirmés, le présenter comme **ressource historique à vérifier**, et non comme wrapper recommandé.

### Pyllica

Pyllica est consacré à l’extraction de corpus de périodiques. La documentation détaillée doit être lue avec les limites d’usage Gallica actuelles. Le dépôt de maintenance fournit une couche compatible qui utilise notamment le service `Issues` pour résoudre les fascicules plutôt que de dépendre d’une redirection de page de dates.

## R

### bnfimage

`bnfimage` fournit une interface R à l’API IIIF. Le correctif 2026 conservé dans le dépôt de maintenance ajoute une classification des requêtes haute définition, une cadence compatible avec les limites actuelles et la gestion de `429` / `Retry-After`.

### gargallica

`gargallica` facilite notamment l’extraction de métadonnées et de texte OCR. Le correctif 2026 migre les appels SRU historiques vers HTTPS et ajoute une politique de débit/retry pour `.texteBrut`.

## Limites d’usage Gallica actuellement publiées

Pendant la phase transitoire de déploiement du gestionnaire d’API, api.bnf.fr publie notamment les limites suivantes :

- IIIF Image en `full/full` ou avec une taille supérieure à 1000 pixels : 5 appels/minute ;
- `.texteBrut` : 5 appels/minute ;
- `.PDF` : 4 appels/minute ;
- image `.highres` : 50 appels/minute ;
- dépassement : HTTP `429 Too Many Requests`.

Ces limites sont susceptibles d’évoluer. La page « API Gallica » fait foi pour leur valeur courante.

## Statut et maintenance

Une page publique de wrappers doit séparer explicitement trois notions :

1. **API BnF documentée** : service exploité par la BnF ;
2. **wrapper tiers actif** : projet externe dont l’état courant a été vérifié ;
3. **ressource historique** : projet utile pour comprendre ou reproduire d’anciens scripts, mais ne devant pas être présenté comme solution actuelle sans avertissement.
