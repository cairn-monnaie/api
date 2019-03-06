# Cairn

## Prérequis
 * git
 * docker && docker-compose

Se placer sur la branche cairn du dépôt api. Depuis la racine du projet :
```
git fetch origin cairn:cairn
git checkout cairn
```

## Introduction
L'application API (ce dépôt) est centrale dans le fonctionnement des différentes applications "clientes" : CEL, BDC, et GI. Il est donc logique que l'organisation des services (au sens de docker) reflète bien cette dépendance des applications dites clientes envers l'API.
Il est donc logique que les conteneurs Cyclos soient dans ce dépôt, puisque toutes les applications vont en avoir besoin.
C'est donc, seulement une fois que les services du dépôt API sont correctement installés qu'on passe à l'installation du dépôt CEL.

## Télécharger les images docker
Seule l'image docker correspondant au fichier _Dockerfile_ sera créée. Il s'agit de celle du service _api_. Les images docker des services Cyclos (app et db) seront créées automatiquement avant le lancement des services puisqu'ils reposent sur une image existante et non sur un Dockerfile
```
sudo docker-compose build
```

## Restaurer une configuration initiale de Cyclos à partir d'un dump

Le fichier _cyclos.sql_ contenu dans le dossier `etc/cyclos/dump` contient un dump valable pour la version 4.11.2 de Cyclos. Il est donc nécessaire de spécifier, dans le fichier docker-compose.yml, que l'image docker à installer en local correspond à la version 4.11.2 (voir le `docker_compose.yml`). Le cas échéant, il faut recréer un fichier dump correspondant à la version souhaitée.  
Pour plus d'informations sur comment créer, voir [doc docker de l'image cyclos](https://hub.docker.com/r/cyclos/cyclos/)

Ce dump, très minimaliste, ne contient que : 
 * les informations concernant la licence utilisée
 * un administrateur global d'identifiants admin:admin
 * l'autorisation, au niveau global, d'utilisation des services web (indispensable par la suite)

NB : il s'agit d'un dump correspondant à une licence gratuite, prise en janvier 2019, qui expira donc dans le futur.  

Créer le service contenant la Base de données Cyclos (PostGreSQL)
```
docker-compose up -d cyclos-db
```
Tout d'abord, le réseau *mlc_net* est créé. Il va permettre à nos applications de communiquer entre elles.
Ensuite, l'image de cyclos db est installée si elle n'est pas déjà présente en local. Pour plus d'informations sur comment créer, voir [doc docker de l'image cyclos db](https://hub.docker.com/r/cyclos/db)

Une fois l'image installée, la création puis restauration de la base de données à partir du dump se fait automatiquement à la création du service. En effet, le fichier docker_compose.yml, et plus précisement services.cyclos-db.volumes contient cette ligne : `- ./etc/cyclos/dump/cyclos.sql:/docker-entrypoint-initdb.d/cyclos.sql`. C'est parce que le fichier de dump, au format sql, est placé dans le dossier _docker-entrypoint-initdb.d_, qu'il est exécuté au lancement du service.

On vérifie que la restauration de la BDD est bien en cours : 
```
docker-compose logs -f cyclos-db
```

Une fois la restauration complétée, on lance le service de l'application Cyclos. De même, l'image est installée en local si elle n'est pas déjà présente avant d'effectivement créer le service. 
```
docker-compose up -d cyclos-app
```

Il nous reste à créer le service api. A la création du service, plusieurs scripts sont automatiquement lancés afin de :
 * générer toute la configuration Cyclos : un réseau, les monnaies, les groupes d'utilisateurs, les produits...
 * si l'environnement n'est pas 'prod', générer un ensemble de données : utilisateurs, paiement

Mais avant, jetons un oeil au fichier docker_compose.yml. 
Si on a services.api.environment.ENV=dev et services.api.environment.CURRENCY\_SLUG=cairn, le réseau cyclos automatiquement généré aura pour  nom et  nom interne 'devcairn'. L'URL pour accéder à ce réseau dans cyclos sera donc localhost:1234/devcairn
De plus, si ENV != prod, le script python présent dans le fichier `etc/cyclos/init\_test\_data.py` est lancé et génère des données automatiques : des utilisateurs prestataires/particuliers, des administateurs réseaux, puis des paiements.
```
docker-compose up -d api
```

On peut contrôler la génération de la configuration Cyclos puis des données : 
```
docker-compose logs -f api
```

A la fin de la création de ces 3 services, on a : 
 * une base de données Cyclos PostGreSql 
 * une configuration Cyclos
 * un jeu de données créé grâce au script `etc/cyclos/init\_test\_data.py` avec des administrateurs réseaux, des adhérents particuliers/prestataires, des changes numériques et des paiements immédiats / programmés
 * un fichier `etc/cyclos/cyclos\_constants\_dev.yml` contenant toutes les constantes Cyclos. Il est nécessaire au fonctionnement de l'API

## Et si on veut ?
 * Recréer les applications à partir de 0 ?
    ``` 
    sudo rm -rf data/cyclos
    sudo rm etc/cyclos/cyclos_constants_dev.yml
    sudo docker-compose stop
    sudo docker-compose rm
    ```
    Puis on reprend depuis le début du README. 
    ATTENTION 1 : Si les fichiers dans data/cyclos ne sont pas supprimés, la restauration à partir du dump n'est pas executée à la création du script
    ATTENTION 2 : Si services.api.environment.ENV=dev et le fichier etc/cyclos/cyclos_constants_dev.yml, la configuration Cyclos et le jeu de données ne sont pas executés

 * Regénérer des données (utilisateurs / paiements) mais conserver la BDD Cyclos et sa configuration ?
    On se place, pour l'exemple, dans le cas où services.api.environment.ENV=dev . On va, depuis le conteneur avec la BDD Cyclos, lancer un script sql qui va nettoyer les réseaux cyclos ayant dans leur nom interne la sous-chaîne de caractères 'dev'.
    
    WARNING : Ce script ne fonctionne pas dans le cas général, le nombre de liens entre les différentes tables (clés étrangères notamment) étant très varié et dépendant de l'utilisation de l'outil. Il fonctionne dans le cadre du script de génération de données actuel.

    D'abord, on affiche la liste des conteneurs actifs, afin de récupérer le nom du conteneur de la BDD Cyclos
    ```
    sudo docker ps
    ```
    On suppose que le nom est : api_cairn_cyclos-db_1

    Pour l'instant, je ne suis pas parvenu à lancer le script depuis l'extérieur du conteneur, il faut donc le lancer depuis l'intérieur
    ```
    docker cp etc/cyclos/script_clean_database_dev.sql  api_cairn_cyclos-db_1:/
    docker-compose exec cyclos-db sh
    psql -U cyclos cyclos < script_clean_database_dev.sql    
    ```

    Ensuite, vous pouvez ajouter/modifier des données dans `etc/cyclos/init\_test\_data.py`
    Enfin, la commande pour relancer le script de génération de données : 
    ```
    docker-compose exec api python /cyclos/init_test_data.py http://cyclos-app:8080/ `echo -n admin:admin | base64`
    ```

## Applications à développer

- Front BDC: Bureau de change
- Front GI: Gestion interne
- Front EA: Espace adhérents

- API globale: Django REST Framework

- Cyclos: App monétaire/bancaire (image: cyclos/cyclos:4.6.1, dépendant de pgSQL 9.* -> version a définir + PostGIS 2.2)
- Dolibarr custom Euskalmoneta: CRM pour gestion des adhérents, etc... (version 3.9 custom Euskalmoneta + docker-compose custom META-IT + MariaDB 10.1)
  - Branche utilisée: develop


## Comment ça marche ?

La méthode que j'utilise pour travailler dans cet environnement:

1) Je lance tous les services

```
docker-compose up -d
```

2) Je stoppe ceux que je vais avoir besoin de redémarrer manuellement

```
docker-compose stop api
docker-compose stop bureaudechange
```

3) Je les relance individuellement

```
docker-compose up api
docker-compose up bureaudechange
```

4) Si vous modifiez du React (JavaScript ou JSX), il est **obligatoire** de lancer cette commande:

Elle lance le watcher webpack, et c'est lui qui compile notre JSX et gère nos dépendances Web, l'output de cette commande
est un (ou +) bundle(s) se trouvant dans `/assets/static/bundles` du container `bureaudechange`.

```
docker-compose exec bureaudechange npm run watch
```

Il existe également 2 autres commandes:

Cette commande est lancée automagiquement lors d'un build du docker bureaudechange (cf. Dockerfile), il va lui aussi compiler et produire les output bundles (avec les dépendances de Dev), mais sans le watch évidemment.

```
docker-compose exec bureaudechange npm run build
```

Comme précédemment, mais celle-ci est utilisée pour une mise en production (avec les dépendances de Prod, donc),
webpack va compresser les scripts/css et va retirer les commentaires, entre autres choses...

```
docker-compose run bureaudechange npm run build-production
```

Pour corriger les problèmes de droit sur dolibarr :
```
docker-compose exec dolibarr-app chown -hR www-data:www-data /var/www/documents
```

### En cas de problème

Dans le cas où l'on veut remettre à zéro les bases de données Cyclos et/ou Dolibarr, il faudra effectuer depuis le dossier de l'api:
```
# pour Cyclos
(sudo) rm -rf data/cyclos/
(sudo) rm etc/cyclos/cyclos_constants.yml

# pour Dolibarr
(sudo) rm -rf data/mariadb/
```
Afin de supprimer les données liées au Cyclos et/ou Dolibarr actuels.


Puis, stopper toute la pile API (Cyclos + Dolibarr, et leurs bases de données…):
```
docker-compose stop
```

La relancer:
```
docker-compose up -d
```

Il est possible de jeter un oeil aux logs des restauration pour s'assurer de leur bon fonctionnement:
```
# pour Cyclos
docker-compose logs -f cyclos-db

# pour Dolibarr
docker-compose logs -f dolibarr-db
```

Pour Cyclos, une fois le restore terminé, il faudra redémarrer `cyclos-app`:
```
docker-compose restart cyclos-app
```

L'entrypoint de l'API devrait maintenant pouvoir se connecter à `cyclos-app`, et ainsi lancer les scripts d'init de Cyclos.
```
docker-compose logs -f api
```

Une fois ces scripts passés: l'API démarre enfin Django, et le développement peut commencer.

## Comment initier le circuit Euskal Moneta ?

Afin d'effectuer les différentes opérations de nos applications, nous avons besoin avant toute chose d'initier les flux d'Eusko.

### I) Impression des billets Eusko 

Cette étape est maintenant automatisée dans le script `init_test_data.py`, ce qui suit reste pour documentation, nous pouvons d’ores et déjà aller au point II).

Pour cela, rendez-vous dans [l'interface d'administration de Cyclos](http://localhost:8081/global/#login).

Connectez-vous avec les identifiants Gestion interne (demo/demo), puis dans `Banking > System payment > Between system accounts`.

Rentrer dans le formulaire:
```
From account: Compte de débit eusko billet
Montant: 126,500 EUS.
```

### II) Sortie Coffre

Rendez-vous dans l'application Gestion interne pour sortir ces nouveaux billets du Coffre:

1. Se connecter avec les identifiants notés ci-dessus
2. Dans `Coffre > Sortie`, mettre un certain montant, 500 par exemple vers un bureau de change donné, comme Euskal Moneta (B001).

Vous pouvez maintenant déclarer une entrée stock dans l'application Bureau de change en se connectant avec le compte B001:
`Gestion > Stock de billets > Entrée`, sélectionner la liste correspondante à votre Sortie coffre.... Et voilà !

### III) Suite et fin

Une fois ceci fait, vous avez accès à toutes les actions possibles dans l'application BDC (sauf cotisation en Eusko, il faudra faire un change en premier lieu):

* Change
* Cotisation Eusko
* Reconversions
* Sortie stock, etc...
