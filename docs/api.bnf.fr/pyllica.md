# Pyllica, extraction de corpus de périodiques de Gallica

Pyllica est un ensemble historique de scripts Python destiné à extraire du texte, des PDF et des images de documents et périodiques Gallica. Pour un usage actuel, il faut tenir compte des endpoints et limites d’usage publiés par la BnF ainsi que des correctifs apportés depuis la version historique.

## Point important en 2026

Les scripts historiques effectuaient plusieurs opérations qui ne sont plus adaptées à un usage robuste : téléchargements redondants, résolution fragile des fascicules par redirection, requêtes IIIF haute définition sans limitation explicite et absence de gestion de `429 Too Many Requests`.

Le dépôt de maintenance `maribakulj/maj-scripts-api.bnf.fr` fournit des remplacements compatibles pour les quatre surfaces historiques :

- `pyllicalabs.py` : texte brut ;
- `pyllicalabspdf.py` : PDF ;
- `pyllicalabsjpg.py` : images d’un document ;
- `pyllicalabsjpgpress.py` : images de périodiques.

## Résolution des fascicules

Pour les périodiques, préférer le service Gallica `Issues`, qui expose les fascicules disponibles et leur `dayOfYear`, plutôt que de construire une URL de date puis d’inférer l’ARK depuis une redirection.

Exemple de service :

```text
https://gallica.bnf.fr/services/Issues?ark=ark:/12148/cb32798952c/date
```

La date structurée doit être calculée à partir de `dayOfYear`. Ne pas parser le libellé humain de l’élément `issue`, dont la forme n’est pas un contrat de données.

## Texte brut

Les extractions `.texteBrut` sont actuellement limitées à 5 appels par minute. Un client doit donc :

- espacer les appels ;
- traiter HTTP 429 ;
- respecter `Retry-After` lorsqu’il est fourni ;
- éviter tout téléchargement en double.

Le remplacement maintenu corrige notamment un ancien comportement qui téléchargeait deux fois le même texte en cas de succès.

## PDF

Les téléchargements `.PDF` sont actuellement limités à 4 appels par minute. Les scripts doivent intégrer une cadence appropriée et ne pas réessayer immédiatement en boucle en cas de limitation.

Pour la reconstruction de PDF par blocs, utiliser `pypdf` plutôt que les anciennes classes `PdfFileReader`, `PdfFileWriter` et `PdfFileMerger` de PyPDF2.

## Images IIIF

L’API IIIF Image publique documentée par api.bnf.fr est actuellement indiquée en version 2.

Pour un usage courant, une largeur de 1000 pixels constitue un défaut plus prudent :

```python
for page in pages:
    url = (
        "https://gallica.bnf.fr/iiif/ark:/12148/"
        f"{ark}/f{page}/full/1000/0/native.jpg"
    )
```

Les requêtes `full/full` ou demandant une taille supérieure à 1000 pixels sont actuellement limitées à 5 appels par minute. Une résolution de 3000 ou 5000 pixels reste possible lorsque le document et le service le permettent, mais elle ne doit pas être présentée sans le mécanisme de limitation correspondant.

Exemple haute définition, à utiliser avec throttling :

```text
https://gallica.bnf.fr/iiif/ark:/12148/<ARK>/f1/full/3000/0/native.jpg
```

## Années bissextiles

Ne pas réimplémenter manuellement la règle des années bissextiles avec uniquement `% 4` et `% 100`. Utiliser `datetime.date` et `datetime.timedelta`, ce qui gère correctement la règle des années divisibles par 400, notamment l’année 2000.

## Limites d’usage actuellement publiées

Au 2 septembre 2026, la page « API Gallica » indique pendant la phase transitoire du gestionnaire d’API :

- IIIF `full/full` ou >1000 px : 5 appels/minute ;
- `.texteBrut` : 5 appels/minute ;
- `.PDF` : 4 appels/minute ;
- `.highres` : 50 appels/minute ;
- dépassement : HTTP 429.

Ces valeurs sont des paramètres d’exploitation et peuvent évoluer. La page « API Gallica » doit rester la référence normative plutôt que de recopier durablement ces chiffres dans du code.

## Compatibilité

La documentation historique peut rester utile pour comprendre les quatre outils et leurs paramètres métier. En revanche, les exemples de transport HTTP et de résolution de fascicules doivent être remplacés par les versions testées du dépôt de maintenance.
