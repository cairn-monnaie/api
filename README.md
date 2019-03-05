# Cairn

## Télécharger les images docker

```
sudo docker-compose build
```
## Prérequis
Se placer sur la branche cairn du dépôt api

## Restaurer la BDD Cyclos à partir du dump

Le fichier dump contenu dans le dossier etc/cyclos/dump est valable pour la version 4.11.2 de Cyclos. Il est donc nécessaire d'utiliser, dans le fichier docker-compose.yml, l'image 4.11.2 de Cyclos.

```
docker-compose up -d cyclos-db
```

Ensuite, on vérifie que la restauration de la BDD se fait : 
```
docker-compose logs -f cyclos-db
```

Une fois la restauration complétée, on lance les autres services 
Si, dans le docker-compose, on a ENV=dev et CURRENCY\_SLUG=cairn, le réseau cyclos automatiquement généré aura pour  nom et  nom interne 'devcairn'. L'URL pour accéder à ce réseau dans cyclos sera donc localhost:1234/devcairn
De plus, si ENV != prod, le script init\_test\_data.sql est lancé et génère des données automatiques : des utilisateurs prestataires/particuliers, des administateurs réseaux, puis des paiements.
```
docker-compose up -d cyclos-app
docker-compose up -d api
```

On peut contrôler la génération de la configuration Cyclos puis des données : 
```
docker-compose logs -f api
```

A la fin, de la création de ces 3 services, on a la BDD Cyclos remplie avec des données, ainsi qu'un fichier etc/cyclos/cyclos\_constants\_dev.yml contenant toutes les constantes Cyclos.

## Et si on veut recréer Cyclos à partir de 0
``` 
sudo rm -rf data/cyclos
sudo rm etc/cyclos/cyclos_constants_dev.yml
sudo docker-compose stop
sudo docker-compose rm
```
Puis on reprend depuis le début du README.

## Install de l'application CEL
La structure actuelle des conteneurs dans les différents dépôts est la plus cohérente. En effet, l'API est le point central de fonctionnement des applications BDC, GI et CEL. Il est donc logique que les conteneurs Cyclos soient dans ce dépôt.
C'est donc, seulement une fois que les services du dépôt API sont correctement installés qu'on passe à l'installation des services CEL.

L'application CEL, à l'initialisation, a besoin que Cyclos contienne un réseau et un administrateur réseau.
Le fichier app/config/parameters.yml doit avoir des valeurs cohérentes avec le paramétrage des services API : le nom de la monnaie doit être 'cairn' et l'environnement doit être 'dev'.

```
sudo docker-compose exec engine ./build-setup.sh dev admin:admin
```
Cette commande, dans un environnement de dev, va créer une base de données vide, créer le schéma de BDD à partir des migrations et, finalement, créer un ROLE\_SUPER\_ADMIN avec les données de l'admin réseau Cyclos par défaut : (login = admin\_network et pwd = @@bbccdd )

Ensuite, on génère des données Symfony à partir des données Cyclos, en s'identifiant avec le login/pwd de l'admin qu'on vient de créer
```
sudo docker-compose exec engine php bin/console cairn.user:generate-database --env=dev admin_network @@bbccdd
```
Cette commande, à l'heure actuelle,  ne peut pas être reproduite sur n'importe quel réseau Cyclos contenant n'importe quel jeu de données. Elle a été développée, dans un premier temps, pour les besoins du Cairn. Elle permet d'avoir une variété de données permettant de tester plein de cas différents. Il y a donc un besoin de maîtrise du script de génération de données Cyclos pour adapter celui des données Symfony.

Une fois que c'est terminé, on a tout un panel d'utilisateurs avec des données différentes (les messages de log affichés pendant l execution du script permettent d'obtenir des informations, voir les scripts pour compléter)

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
