# maj-scripts-api.bnf.fr

Dépôt de travail canonique pour l’audit, la remédiation et la validation des scripts et wrappers référencés par api.bnf.fr.

## État du chantier

Les lots P0, P1 et P2 ont été fusionnés dans `main`.

- **P0** corrige les défauts bloquants des clients historiques Python/R et ajoute un client Gallica robuste, des remplacements legacy, un déployeur sûr et des tests live.
- **P1** modernise les clients R encore fragiles (`bnfimage`, `gargallica`) et renforce le moteur de déploiement.
- **P2** fournit un pack éditorial publiable pour les pages Wrappers, Pyllica et IIIF, avec détection automatique de dérive de la documentation publique.

La matrice détaillée de clôture est disponible dans `docs/AUDIT_CLOSURE.md`.

## P0 : défauts bloquants

Le P0 apporte :

- le client Gallica robuste ;
- les correctifs de compatibilité PyGallica et Pyllica ;
- le téléchargement PDF modernisé ;
- les remplacements legacy PyGallica, Pyllica, Gallipy et gargallica ;
- un moteur de déploiement sûr avec détection de dérive, sauvegarde, vérification et rollback ;
- les tests locaux de non-régression ;
- la validation live SRU, Pagination, OAIRecord, Issues, ALTO et IIIF depuis GitHub Actions, donc hors réseau BnF ;
- la validation des Git blob SHA des fichiers tiers audités ;
- les rapports de validation sous `validation/`.

## P1 : maintenance et clients R

La version `0.2.0` étend le chantier aux deux clients R encore fragiles.

### bnfimage

Le remplacement P1 :

- conserve l’interface historique de `bi_image()` ;
- distingue les requêtes IIIF haute définition ;
- applique une cadence conservatrice de 12,5 secondes pour les requêtes HD, soit moins de 5 appels/minute ;
- respecte `Retry-After` sur HTTP 429 et utilise un backoff borné en secours ;
- ajoute un timeout HTTP et remonte les autres erreurs HTTP au lieu de tenter de décoder leur corps comme une image.

### gargallica

Le remplacement P1 :

- migre le SRU de HTTP vers HTTPS ;
- centralise les appels Gallica dans `gallica_api.R` ;
- limite les appels `.texteBrut` à une cadence conservatrice de 12,5 secondes ;
- gère 429, 500, 502, 503 et 504 avec `Retry-After` / backoff ;
- conserve le script d’analyse historique en le modifiant le moins possible.

Le déployeur sait désormais créer un helper absent en amont avec l’action gérée `create`. Une collision est considérée comme une dérive et bloque l’application sans `--force`; le rollback supprime le fichier s’il avait été créé par le déployeur.

## P2 : normalisation documentaire

Le pack `docs/api.bnf.fr/` contient des textes de remplacement prêts à relire/publier pour :

- la page des wrappers Gallica ;
- la documentation Pyllica ;
- la page IIIF Gallica ;
- la matrice de statut des wrappers tiers ;
- les sources et dates de vérification.

Les corrections éditoriales couvrent notamment les exemples Python invalides, les statuts de maintenance, les quotas Gallica, la distinction IIIF Image / Presentation et les mélanges de versions dans les dépôts d’exemples.

## CI

Cinq rails indépendants couvrent désormais le chantier :

1. `P0 local regression suite` : Python 3.10 et 3.12 ;
2. `P0 public Gallica validation` : smoke tests publics contre Gallica depuis GitHub ;
3. `P0 legacy deployment validation` : `apply → verify → rollback` et contrôle des SHA amont ;
4. `P1 R compatibility validation` : parsing réel des remplacements R et classification des requêtes IIIF HD ;
5. `P2 documentation validation` : validation des exemples éditoriaux et détection de dérive de la documentation publique api.bnf.fr.

Le rail P2 s’exécute également chaque lundi à 07:37 UTC. Une fusion n’est recommandée que lorsque tous les rails concernés sont verts sur la même tête de commit.

## Déploiement legacy

Toujours commencer par un plan :

```bash
python scripts/deploy_legacy.py plan --profile pygallica --target /chemin/PyGallica
```

Puis appliquer et vérifier :

```bash
python scripts/deploy_legacy.py apply --profile pygallica --target /chemin/PyGallica
python scripts/deploy_legacy.py verify --profile pygallica --target /chemin/PyGallica
```

En cas de problème :

```bash
python scripts/deploy_legacy.py rollback --target /chemin/PyGallica
```

Pour les clients R :

```bash
python scripts/deploy_legacy.py plan --profile bnfimage --target /chemin/bnfimage
python scripts/deploy_legacy.py apply --profile bnfimage --target /chemin/bnfimage
python scripts/deploy_legacy.py verify --profile bnfimage --target /chemin/bnfimage

python scripts/deploy_legacy.py plan --profile gargallica --target /chemin/gargallica
python scripts/deploy_legacy.py apply --profile gargallica --target /chemin/gargallica
python scripts/deploy_legacy.py verify --profile gargallica --target /chemin/gargallica
```

Profils disponibles : `pygallica`, `pyllica`, `gallipy`, `gargallica`, `bnfimage`.

Le déployeur refuse par défaut un fichier dont le SHA ne correspond plus à la version auditée. `--force` ne doit être utilisé qu’après revue manuelle du diff.

## Limite importante

Ce dépôt fournit des correctifs, remplacements, tests et textes de publication. Il ne modifie pas automatiquement les dépôts tiers ni le CMS api.bnf.fr. Les écarts encore visibles en amont doivent être traités par publication éditoriale ou par contribution aux projets concernés.
