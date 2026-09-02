# Clôture de l’audit scripts api.bnf.fr — 2026-09-02

Ce document relie l’audit initial aux remédiations fusionnées dans `main`.

## Résumé

L’audit initial recensait 24 éléments :

- 15 en P0 ;
- 7 en P1 ;
- 2 en P2.

Les défauts techniques bloquants ont été corrigés ou contournés par des remplacements testés. Les points qui dépendent de dépôts tiers ou du CMS api.bnf.fr sont considérés comme **mitigés** lorsque le dépôt de maintenance fournit un correctif vérifié, une documentation de remplacement et une surveillance de dérive, mais ils ne doivent pas être déclarés « corrigés en amont » tant que les mainteneurs concernés n’ont pas publié ces changements.

## P0

| ID | Sujet | État dans ce dépôt | Clôture |
|---:|---|---|---|
| 1 | Page Wrappers BnF sans statut de maintenance | Pack éditorial P2 + matrice de statut | Mitigé, publication CMS requise |
| 2 | PyGallica archivé | Couche de compatibilité + statut historique documenté | Clos côté dépôt de maintenance |
| 3 | PyGallica `Search.search()` / variable `file` | Remplacement sans fichier temporaire | Clos |
| 4 | PyGallica `document_api.py` / sérialisation XML | Parsing XML direct en mémoire | Clos |
| 5 | `Document.oai` vs `Document.OAI` | Alias compatible + exemple corrigé | Clos |
| 8 | Gallipy `iiif_info()` async / `image` indéfini | Patch minimal `image` → `view` | Clos côté correctif |
| 9 | Gallipy `iiif_data()` async / `image` indéfini | Patch minimal `image` → `view` | Clos côté correctif |
| 10 | Gallipy `structures` vs `structure` | Lecture du schéma actuel + suppression du fallback arbitraire | Clos |
| 11 | Gallipy / ancien PyPDF2 | Migration `pypdf` moderne | Clos |
| 14 | Pyllica `textpress()` double téléchargement | Un seul téléchargement `.texteBrut` | Clos |
| 16 | Pyllica PDF sans gestion de quota | Rate limiting + retry/429 | Clos |
| 17 | Pyllica JPG 3000 px sans limitation | HTTPS + largeur prudente par défaut + classe HD limitée | Clos |
| 18 | Pyllica JPG presse idem | Client commun robuste | Clos |
| 19 | Documentation BnF recommandant 3000/5000 px sans avertissement | Texte P2 corrigé | Mitigé, publication CMS requise |
| 23 | gargallica `full_hd_image.R` sans schéma/quota | HTTPS + attente entre appels + 429 | Clos côté correctif |

## P1

| ID | Sujet | État dans ce dépôt | Clôture |
|---:|---|---|---|
| 6 | PyGallica IIIF sans robustesse HTTP | Client central avec timeout, retry, 429 et rate limiting | Clos |
| 7 | Gallipy globalement ancien | Correctifs ciblés et compatibilité maintenue sans réécriture complète du projet | Mitigé |
| 12 | Gallipy `getpdf` retries récursifs immédiats | Client robuste et politique de retry bornée | Clos |
| 13 | `fdh-gallica` historique non résolu | Marqué ressource historique à vérifier dans le pack éditorial | Mitigé, décision éditoriale requise |
| 15 | Pyllica `pressdate()` et années bissextiles | `datetime.date` + `timedelta` | Clos |
| 20 | `bnfimage` limiteur trop rapide et absence 429 | Remplacement R avec classification HD, `Retry-After`, timeout | Clos côté correctif |
| 22 | `gargallica` SRU HTTP et `.texteBrut` non limité | HTTPS + helper réseau + rate limiting + retry | Clos côté correctif |

## P2

| ID | Sujet | État dans ce dépôt | Clôture |
|---:|---|---|---|
| 21 | `bnfimage` : versions IIIF annoncées / dette de compatibilité | La page Wrappers et la page IIIF de remplacement imposent d’indiquer précisément les versions et séparent Image/Presentation. Les tests R couvrent le comportement corrigé, mais le README du dépôt tiers n’est pas modifié ici. | Mitigé, contribution amont recommandée |
| 24 | dépôt `altomator/IIIF` mélangeant exemples v2/v3 | La page IIIF de remplacement exige une indication explicite de version et traite le dépôt comme collection hétérogène d’exemples. | Mitigé, normalisation du dépôt tiers recommandée |

## Validation automatisée

La clôture technique repose sur cinq rails GitHub Actions :

1. Python 3.10 / 3.12 ;
2. smoke tests publics Gallica ;
3. cycle de déploiement `apply → verify → rollback` + SHA amont ;
4. parsing et validation R ;
5. validation du pack éditorial + détection de dérive de la documentation publique.

Le workflow documentaire est également planifié chaque lundi à 07:37 UTC.

## Ce qui reste volontairement hors du dépôt

Trois catégories d’actions ne peuvent pas être considérées comme accomplies par ce dépôt seul :

- publier les textes P2 dans le CMS api.bnf.fr ;
- fusionner les correctifs dans les dépôts tiers historiques ;
- décider de retirer ou remplacer les liens externes devenus non vérifiables.

Ces actions sont des opérations de gouvernance ou de publication, pas des défauts techniques du package de maintenance.

## Critère de fin

Le chantier peut être considéré **techniquement clôturé** lorsque `main` contient P0, P1, P2 et cette matrice, et que les workflows associés sont verts. Toute modification future de quota, de contrat public api.bnf.fr ou de fichier tiers audité doit rouvrir la ligne concernée plutôt que modifier silencieusement les hypothèses historiques.
