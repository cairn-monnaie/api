# Cairn

## Prérequis
 * git
 * docker && docker-compose (Docker Engine version 17.12.0 and higher)

 * Se placer sur la branche cairn du dépôt api. Depuis la racine du projet :  
   ```
   git fetch origin cairn:cairn
   git checkout cairn
   ```

## Introduction
L'application API (ce dépôt) est centrale dans le fonctionnement des différentes applications "clientes" : CEL, BDC, et GI. Il est donc logique que l'organisation des services (au sens de docker) reflète bien cette dépendance des applications dites clientes envers l'API.
Il est donc logique que les conteneurs Cyclos soient dans ce dépôt, puisque toutes les applications vont en avoir besoin.  
Ainsi, c'est seulement une fois que les services du dépôt API sont correctement installés qu'on passe à l'installation du dépôt CEL.

## Installation 
  
 * **Construire notre image Docker**

    Notre image est générée à partir du `Dockerfile` du dossier racine. Il s'agit de celle du service _api_ dans le fichier de configuration docker nommé `docker_compose.yml: services.api.build = .`   
    ```
    sudo docker-compose build
    ```

 * **Restaurer une configuration minimale de Cyclos à partir d'un dump existant**

    Le fichier `etc/cyclos/dump/cyclos.sql` contient un dump valable pour la version 4.11.2 de Cyclos. Il est donc nécessaire de spécifier, dans le fichier docker-compose.yml, que l'image docker à installer en local correspond à la version 4.11.2 (voir le `docker_compose.yml: services.cyclos-app.image`). Le cas échéant, il faut recréer un fichier dump correspondant à la version de l'image souhaitée.   
    Pour plus d'informations sur comment créer un dump à partir d'une base de données existante, voir [la page docker de cyclos](https://hub.docker.com/r/cyclos/cyclos/)  

    Ce dump, très minimaliste, ne contient que : 
     * les informations concernant la licence utilisée
     * un administrateur global d'identifiants admin:admin
     * l'autorisation, au niveau global, d'utilisation des services web (indispensable par la suite)

    **WARNING** : il s'agit d'un dump correspondant à une licence gratuite, prise en janvier 2019, qui expirera donc dans le futur.  

    * _Créer le conteneur de base de données Cyclos (PostGreSQL)_  
      ```
      sudo docker-compose up -d cyclos-db
      ```

      Tout d'abord, le réseau de nom *mlc_net* est créé. Il va permettre aux applications de communiquer entre elles.
      Ensuite, l'image de cyclos db est installée si elle n'est pas déjà présente en local. Pour plus d'informations sur [l'image cyclos db](https://hub.docker.com/r/cyclos/db)  
      
      Une fois l'image téléchargée, la création puis restauration de la base de données à partir du dump se fait automatiquement à la création du service. En effet, le chemin du docker_compose `services.cyclos-db.volumes` contient cette ligne : `- ./etc/cyclos/dump/cyclos.sql:/docker-entrypoint-initdb.d/cyclos.sql`.  
      C'est parce que le fichier de dump, au format sql, est placé dans le dossier `/docker-entrypoint-initdb.d`, qu'il est exécuté au lancement du service.

    * _Vérifier que la restauration est bien en cours_  
      ```
      sudo docker-compose logs -f cyclos-db
      ```
    * _Créer le conteneur de l'application Cyclos_
      Copier le fichier template des variables d'environnement docker et choisir le port externe pour l'application Cyclos.   
       `cp .env.dist .env`
     
      Une fois la restauration complétée, on lance le service de l'application Cyclos. De même, l'image est installée en local si elle n'est pas déjà présente avant d'effectivement créer le service.  
      ```
      sudo docker-compose up -d cyclos-app
      ```
 * **Générer la configuration finale de Cyclos et un jeu de données**
   
    Dans le cadre de la documentation, nous allons nous mettre en situation de développement, c'est-à-dire  `services.api.environment.ENV = dev`. Mais la méthode est la même pour un environnement différent (test / prod)
    Pour générer la configuration Cyclos et le jeu de données, nous allons créer le dernier conteneur de ce dépôt : le conteneur _api_.  
    Notre Dockerfile contient une instruction qui va être executée au lancement du service :  
    `ENTRYPOINT ["/cyclos/setup_cyclos.sh"]`  

    Le script python `etc/cyclos/setup_cyclos.py` fait trois choses :
      * vérifie que le fichier `etc/cyclos/cyclos_constants_dev.yml` n'existe pas. S'il existe, cela signifie que la configuration Cyclos a déjà été effectuée, et que les scripts de génération n'ont pas à être exécutés.
      * lance le script `setup.py` de génération de la configuration cyclos (voir `etc/cyclos/setup.py` dans le dépôt local). La configuration contient un réseau (au sens de Cyclos), les monnaies, des groupes d'utilisateurs, des produits... 
      * lance le script `init_test_data.py` de génération du jeu de données (si et seulement si  `services.api.environment.ENV != prod`) : création d'utilisateurs adhérents particuliers/prestataires, des administrateurs réseaux. Réalisation de changes numériques et de paiements.

    _Info_ : Si on a `services.api.environment.ENV=dev` et `services.api.environment.CURRENCY_SLUG=cairn`, le réseau cyclos automatiquement généré aura pour  nom et  nom interne 'devcairn'. L'URL pour accéder à ce réseau dans cyclos sera donc localhost:1234/devcairn.  
    
    * _Créer le conteneur api et vérifier l'exécution des scripts_

      * Lancer les scripts d'initialisation 
        Etant donné que le script bash `etc/cyclos/setup_cyclos.sh` nécessite une interaction avec l'utilisateur, nous allons créer un conteneur temporaire nommé 'api_container' à partir du service 'api', puis nous allons le supprimer. 
        ```
        sudo docker-compose run --name api_container api (renseigner login puis password de l'admin global Cyclos)
        sudo docker container rm api_container
        ```

      * Lancer le service destiné à tourner en permanence
        ```
        sudo docker-compose up -d api
        sudo docker-compose logs -f api
        ```

    A la fin de la création de ces 3 services, on a : 
      * une base de données Cyclos
      * une configuration Cyclos
      * un jeu de données créé grâce au script `etc/cyclos/init_test_data.py`
      * un fichier `etc/cyclos/cyclos_constants_dev.yml` généré, contenant toutes les constantes Cyclos. Il est nécessaire au fonctionnement de l'API

## Et si on veut ?
 * **Recréer les applications à partir de 0 ?**
    ``` 
    sudo rm -rf data/cyclos
    sudo rm etc/cyclos/cyclos_constants_dev.yml
    sudo docker-compose stop
    sudo docker-compose rm
    ```
    Puis on reprend depuis le début du README.   
    **ATTENTION 1** : Si les fichiers dans data/cyclos ne sont pas supprimés, la restauration à partir du dump n'est pas executée à la création du conteneur  
    **ATTENTION 2** : Si services.api.environment.ENV=dev et le fichier etc/cyclos/cyclos_constants_dev.yml existe, la configuration Cyclos et le jeu de données ne sont pas réexécutés

 * **Regénérer des données (utilisateurs / paiements) mais conserver la BDD Cyclos et sa configuration ?**  

    On se place, dans le cadre explication, dans un environnement de développement . Directement dans le conteneur de la base de données Cyclos (services.cyclos-db), on va lancer un script sql (voir `etc/cyclos/script_clean_database_dev.sql`) qui va nettoyer les réseaux cyclos ayant dans leur nom interne la sous-chaîne de caractères 'dev'.  
    
    **WARNING** : Ce script ne fonctionne pas dans le cas général. En effet, les clés étrangères liant les différentes tables sont très nombreuses, ce qui rend difficile la mise en place d'un script générique. Il va dépendre de l'utilisation que chacun a de l'outil. Il fonctionne dans le cadre du script de génération de données actuel.  

    * _Récupérer le nom du conteneur cyclos-db_  
    On récupère la liste des conteneurs actifs, et on sélectionne le nom correspondant à l'image cyclos/db
    ```
    sudo docker ps
    ```
    Supposons que le nom est : api_cairn_cyclos-db_1

    * _Lancer le script de nettoyage de la base de données_  
      Pour l'instant, je ne suis pas parvenu à lancer le script depuis l'extérieur du conteneur, il faut donc le lancer depuis l'intérieur
      ```
      docker cp etc/cyclos/script_clean_database_dev.sql  api_cairn_cyclos-db_1:/
      docker-compose exec cyclos-db sh
      psql -U cyclos cyclos < script_clean_database_dev.sql    
      ```
      Le 1er 'cyclos' correspond au nom du user (au sens PostGreSQL) ayant les privilèges en écriture/lecture de la base de données nommée 'cyclos' (2ème)

    * _Modifier le jeu de données de test et le générer_   
      Ensuite, vous pouvez ajouter/modifier des données dans `etc/cyclos/init_test_data.py`, puis
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
