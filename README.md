# maj-scripts-api.bnf.fr

Dépôt de travail pour l’audit, la correction et la validation des scripts et wrappers référencés par [api.bnf.fr](https://api.bnf.fr/).

## P0

La branche `p0/integration-0.1.3` contient la première remédiation P0. Elle vise notamment PyGallica, Gallipy, Pyllica et les exemples historiques associés.

La CI exécute une validation **depuis les runners GitHub, donc hors réseau BnF**, contre les services publics Gallica : Pagination, OAIRecord, Issues, SRU, ALTO et IIIF.

```bash
python -m pip install -r requirements.txt
python scripts/live_validate.py --output p0-live-report.json
```

Le rapport distingue `PASS`, `FAIL` et `UNREACHABLE` afin de ne pas confondre une panne réseau avec une régression fonctionnelle.
