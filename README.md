# maj-scripts-api.bnf.fr

Dépôt de travail canonique pour l’audit, la remédiation et la validation des scripts et wrappers référencés par api.bnf.fr.

## P0

La branche `p0/integration-0.1.3` contient :

- le client Gallica robuste ;
- les correctifs de compatibilité PyGallica et Pyllica ;
- le téléchargement PDF modernisé ;
- les tests locaux de non-régression ;
- la validation live SRU, Pagination, OAIRecord, Issues, ALTO et IIIF depuis GitHub Actions, donc hors réseau BnF ;
- les rapports de validation sous `validation/`.

La CI P0 est volontairement séparée en deux workflows :

1. `P0 local regression suite` : tests déterministes sans dépendance au réseau ;
2. `P0 public Gallica validation` : smoke tests contre les services publics Gallica.

La fusion du P0 n’est recommandée que lorsque les deux workflows sont verts.
