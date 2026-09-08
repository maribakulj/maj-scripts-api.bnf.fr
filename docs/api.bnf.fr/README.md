# Pack éditorial api.bnf.fr

Ce dossier contient des propositions de remplacement prêtes à relire pour les pages publiques d’api.bnf.fr concernées par l’audit des wrappers Gallica.

## Périmètre

- `wrappers-gallica.md` : remplace la page « Wrappers pour les API Gallica » datée de 2021 ;
- `pyllica.md` : remplace la documentation Pyllica en intégrant les quotas publics actuels et l’API `Issues` ;
- `iiif-gallica.md` : clarifie la version IIIF actuellement documentée publiquement et les limites d’usage ;
- `wrapper-status.json` : matrice machine-readable des projets tiers et du niveau de confiance documentaire ;
- `sources.md` : URLs et faits vérifiés les 2 et 8 septembre 2026.

## Point à valider avant publication

La page Pyllica oriente désormais les traitements automatisés de texte vers l’ALTO, `.texteBrut` étant une adresse du site web soumise à une vérification anti-robot. Ce changement a une conséquence d’exploitation qui dépasse la rédaction : l’ALTO est paginé, une requête par vue là où `.texteBrut` renvoyait le document entier. Orienter publiquement tous les extracteurs vers cette route multiplie la charge par le nombre de pages.

Le texte proposé demande donc explicitement de ne solliciter que les vues utiles, d’espacer les appels et de prendre contact pour un besoin massif. **Cet arbitrage relève de l’équipe API et devrait être validé par elle avant publication.**

## Principes éditoriaux

1. Distinguer une API BnF d’un wrapper tiers.
2. Ne jamais laisser entendre que la présence d’un lien implique que le projet est maintenu ou supporté par la BnF.
3. Afficher les limites d’usage à proximité des exemples susceptibles de les déclencher.
4. Ne pas mélanger la version IIIF actuellement exposée/documentée sur api.bnf.fr avec un chantier de migration distinct.
5. Préférer des exemples minimalement exécutables et testables.
6. Donner un statut explicite aux ressources historiques, archivées ou non vérifiables.
7. Distinguer les services d’API des adresses du site web portant un suffixe, dont le comportement ne relève pas du même contrat.
8. Décrire une contrainte d’accès par le geste correct à adopter — identifier son client — plutôt que par l’énumération des cas refusés.

Les fichiers de ce dossier ne modifient pas automatiquement le CMS api.bnf.fr. Ils constituent la source de publication proposée et sont vérifiés par CI avant intégration éditoriale.
