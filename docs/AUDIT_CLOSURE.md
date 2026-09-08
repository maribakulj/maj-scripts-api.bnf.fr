# Clôture de l’audit scripts api.bnf.fr — 2026-09-02, rouvert le 2026-09-08

Ce document relie l’audit initial aux remédiations fusionnées dans `main`.

## Résumé

> **Réouverture du 8 septembre 2026.** Une contre-vérification menée en exécutant réellement les scripts — et non en relisant le code — a établi que Gallica avait changé deux règles d’accès sans les documenter, et que deux lignes portées « closes » ne l’étaient pas. Conformément au critère de fin ci-dessous, les lignes concernées sont rouvertes plutôt que corrigées en silence, et quatre lignes nouvelles (25 à 28) sont ajoutées.

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
| 8 | Gallipy `iiif_info()` async / `image` indéfini | Patch `image` → `view`, **puis** User-Agent posé dans `helpers.py` (voir 26) : le correctif initial levait la `NameError` mais la fonction échouait toujours en 403, ce que personne n’avait constaté faute de la rappeler | **Rouvert le 2026-09-08** — Mitigé, contribution amont recommandée |
| 9 | Gallipy `iiif_data()` async / `image` indéfini | Idem 8 | **Rouvert le 2026-09-08** — Mitigé, contribution amont recommandée |
| 10 | Gallipy `structures` vs `structure` | Lecture du schéma actuel + suppression du fallback arbitraire | Clos |
| 11 | Gallipy / ancien PyPDF2 | Migration `pypdf` moderne | Clos |
| 14 | Pyllica `textpress()` double téléchargement | Le double téléchargement était corrigé, mais sur `.texteBrut`, désormais derrière une vérification anti-robot (voir 25). `textpress()` lit maintenant l’ALTO | **Rouvert le 2026-09-08** — Clos sur une autre route |
| 16 | Pyllica PDF sans gestion de quota | Le quota était géré, mais sur `.pdf`, désormais protégé (voir 25). `pdfpress()` reconstruit depuis IIIF ; `source="web"` conserve la route historique | **Rouvert le 2026-09-08** — Clos sur une autre route |
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
| 22 | `gargallica` SRU HTTP et `.texteBrut` non limité | HTTPS et cadence restent valides ; `.texteBrut` est protégé (voir 25) et `gargallica_read_html()` détecte désormais la page de vérification au lieu de l’analyser | **Rouvert le 2026-09-08** — Mitigé, contribution amont recommandée |

## P2

| ID | Sujet | État dans ce dépôt | Clôture |
|---:|---|---|---|
| 21 | `bnfimage` : versions IIIF annoncées / dette de compatibilité | La page Wrappers et la page IIIF de remplacement imposent d’indiquer précisément les versions et séparent Image/Presentation. Les tests R couvrent le comportement corrigé, mais le README du dépôt tiers n’est pas modifié ici. | Mitigé, contribution amont recommandée |
| 24 | dépôt `altomator/IIIF` mélangeant exemples v2/v3 | La page IIIF de remplacement exige une indication explicite de version et traite le dépôt comme collection hétérogène d’exemples. | Mitigé, normalisation du dépôt tiers recommandée |

## Éléments ouverts le 2026-09-08

Quatre constats issus de la contre-vérification. Les trois premiers ont une caractéristique commune : le dépôt vérifiait un signal indirect — un code HTTP, une absence de réponse, l’octet d’un fichier généré — plutôt que ce qu’il avait réellement reçu.

| ID | Sujet | État dans ce dépôt | Clôture |
|---:|---|---|---|
| 25 | Vérification anti-robot sur `.texteBrut` et `.pdf`, servie en **HTTP 200** avec du HTML. Ce ne sont pas des API mais les URL du site web ; un client qui ne contrôle que le statut enregistre le captcha comme contenu (23 460 o de HTML dans un `.txt`, un `.pdf` que `pypdf` rejette). Mesuré à froid après 13 min de silence, avec témoins. | `guard.py` refuse une réponse dont le type ne correspond pas à l’attendu et nomme la vérification. Routes de remplacement : ALTO pour le texte, IIIF pour le PDF. `client.pdf()` et `download_pdf()` conservés à l’identique pour le jour où Gallica rouvrira. | Clos côté correctif — **publication CMS requise** |
| 26 | Gallica refuse par **403** les agents utilisateurs par défaut de plusieurs bibliothèques HTTP. Les dix fonctions de Gallipy passent par un `urlopen` sans agent : aucune ne fonctionnait. Non documenté sur api.bnf.fr. | `text_patch` sur `gallipy/helpers.py`. `probe_user_agent()` surveille que l’agent du dépôt reste accepté et nomme la cause si elle change. | Clos côté correctif — **publication CMS requise**, contribution amont recommandée |
| 27 | ALTO servi avec une déclaration `encoding="ISO-8859-1"` alors que les octets sont de l’UTF-8 (l’en-tête HTTP annonce `charset=UTF-8`). Tout analyseur conforme suit la déclaration : 33 mots accentués corrompus sur une seule page. | `alto.py` corrige la déclaration avant analyse. Le test existant ne comptait que les octets reçus et ne pouvait pas le voir. | Clos — **signalement à la BnF recommandé** |
| 28 | Déployeur : `__pycache__` vendorisé puis comparé, d’où un `--force` exigé pour un non-événement ; sauvegardes horodatées à la seconde avec `exist_ok=False`. Invisible en CI, un checkout neuf n’ayant pas de cache. | Caches exclus de la copie et de la comparaison ; noms de sauvegarde suffixés. | Clos |

## Ce que la contre-vérification n’a pas pu établir

Trois surfaces restent couvertes par des tests unitaires mais **pas par une exécution réelle** : `Document.texte_brut` après sa bascule vers l’ALTO, et six des dix fonctions de Gallipy — dont `Resource.content(mode="pdf")`, qui emprunte la couche HTTP interne de gallipy et non le garde-fou. Les essais répétés ont fait bloquer l’adresse de test par Gallica ; poursuivre aurait dégradé un service public. À reprendre depuis un autre réseau.

## Validation automatisée

La clôture technique repose sur cinq rails GitHub Actions :

1. Python 3.10 / 3.12 ;
2. smoke tests publics Gallica ;
3. cycle de déploiement `apply → verify → rollback` + SHA amont ;
4. parsing et validation R ;
5. validation du pack éditorial + détection de dérive de la documentation publique.

Depuis le 8 septembre 2026, deux de ces rails distinguent une indisponibilité d’un vrai défaut : `live_validate.py` nomme un agent refusé (`USER_AGENT_REFUSED`, code 3) plutôt que d’accuser les API, et `verify_public_documentation_contract.py` sépare `UNREACHABLE` (code 2) d’une dérive documentaire (code 4).

Le workflow documentaire est également planifié chaque lundi à 07:37 UTC.

## Ce qui reste volontairement hors du dépôt

Trois catégories d’actions ne peuvent pas être considérées comme accomplies par ce dépôt seul :

- publier les textes P2 dans le CMS api.bnf.fr ;
- fusionner les correctifs dans les dépôts tiers historiques ;
- décider de retirer ou remplacer les liens externes devenus non vérifiables.

Ces actions sont des opérations de gouvernance ou de publication, pas des défauts techniques du package de maintenance.

## Critère de fin

Le chantier peut être considéré **techniquement clôturé** lorsque `main` contient P0, P1, P2 et cette matrice, et que les workflows associés sont verts. Toute modification future de quota, de contrat public api.bnf.fr ou de fichier tiers audité doit rouvrir la ligne concernée plutôt que modifier silencieusement les hypothèses historiques.
