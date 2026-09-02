# API IIIF de récupération des images de Gallica

## Version actuellement documentée

Au 2 septembre 2026, la fiche publique api.bnf.fr indique **Version 2** pour l’API IIIF de Gallica. Cette page doit documenter l’interface effectivement exposée au public et éviter de mélanger cette information avec un éventuel chantier de migration ou avec des exemples IIIF Presentation 3 issus d’autres contextes.

## API Image

Exemple :

```text
https://gallica.bnf.fr/iiif/ark:/12148/btv1b90017179/f15/0,1900,2400,1200/full/0/native.jpg
```

Pour les scripts génériques, éviter de choisir `full/full` ou une largeur supérieure à 1000 pixels comme défaut silencieux. Ces formes relèvent actuellement d’une classe limitée à 5 appels par minute.

Exemple prudent pour un usage automatisé :

```text
https://gallica.bnf.fr/iiif/ark:/12148/btv1b53066668g/f1/full/1000/0/native.jpg
```

Une application qui demande une résolution supérieure doit implémenter une politique de débit et gérer HTTP 429, notamment `Retry-After` lorsqu’il est fourni.

## API Presentation

Exemple actuellement documenté :

```text
https://gallica.bnf.fr/iiif/ark:/12148/btv1b550076223/manifest.json
```

Le numéro de version doit être indiqué explicitement à proximité des exemples lorsque plusieurs générations IIIF sont évoquées dans la documentation ou les dépôts liés.

## Exemples et dépôts externes

Les exemples liés depuis cette page peuvent contenir un mélange de ressources IIIF Presentation 2 et 3. La page publique doit donc préciser la version de chaque exemple ou renvoyer vers une matrice de compatibilité, plutôt que de présenter un dépôt entier comme homogène.

## Limites d’usage actuellement publiées

Pendant la phase transitoire de déploiement du gestionnaire d’API, la BnF indique :

- IIIF Image `full/full` ou taille >1000 px : 5 appels/minute ;
- bande passante associée à cette classe : 832 Ko/s ;
- dépassement : HTTP `429 Too Many Requests`.

Ces limites peuvent évoluer et doivent être référencées depuis la page « API Gallica » plutôt que dupliquées sans date ni contexte.

## Recommandations éditoriales

- afficher la version IIIF dans la section Documentation, pas uniquement dans la fiche technique ;
- distinguer clairement Image API et Presentation API ;
- indiquer la version associée aux exemples de manifestes ;
- mettre un avertissement visible avant tout exemple `full/full`, `3000`, `5000` ou autre requête HD ;
- ajouter un lien direct vers les limites d’usage et la signification de HTTP 429 ;
- dater toute information transitoire liée au gestionnaire d’API.
