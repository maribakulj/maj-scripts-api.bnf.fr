# maj-scripts-api.bnf.fr

Dépôt de travail canonique pour l’audit, la remédiation et la validation des scripts et wrappers référencés par api.bnf.fr.

## P0

La branche `p0/integration-0.1.3` contient :

- le client Gallica robuste ;
- les correctifs de compatibilité PyGallica et Pyllica ;
- le téléchargement PDF modernisé ;
- les remplacements legacy PyGallica, Pyllica, Gallipy et gargallica ;
- un moteur de déploiement sûr avec détection de dérive, sauvegarde, vérification et rollback ;
- les tests locaux de non-régression ;
- la validation live SRU, Pagination, OAIRecord, Issues, ALTO et IIIF depuis GitHub Actions, donc hors réseau BnF ;
- la validation des Git blob SHA des fichiers tiers audités ;
- les rapports de validation sous `validation/`.

## CI P0

La CI est séparée en trois workflows :

1. `P0 local regression suite` : tests déterministes sans dépendance au réseau, sur Python 3.10 et 3.12 ;
2. `P0 public Gallica validation` : smoke tests contre les services publics Gallica depuis un runner GitHub externe ;
3. `P0 legacy deployment validation` : simulation `apply → verify → rollback` et contrôle de dérive des fichiers amont.

La fusion du P0 n’est recommandée que lorsque les trois workflows sont verts.

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

Profils disponibles : `pygallica`, `pyllica`, `gallipy`, `gargallica`.

Le déployeur refuse par défaut un fichier dont le SHA ne correspond plus à la version auditée. `--force` ne doit être utilisé qu’après revue manuelle du diff.
