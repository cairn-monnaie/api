# coding: utf-8
from __future__ import unicode_literals

import os
import argparse
import base64
import logging

import requests
import yaml  # PyYAML
from datetime import datetime
from datetime import timedelta

logging.basicConfig()
logger = logging.getLogger(__name__)


def check_request_status(r):
    if r.status_code == requests.codes.ok:
        logger.info('OK')
    else:
        logger.error(r.text)
        r.raise_for_status()

# Ensemble des constantes nécessaires au fonctionnement du script.
ENV = os.environ.get('ENV')

LOCAL_CURRENCY_INTERNAL_NAME = os.environ.get('CURRENCY_SLUG')
NETWORK_INTERNAL_NAME = LOCAL_CURRENCY_INTERNAL_NAME

if ENV != 'prod':
    NETWORK_INTERNAL_NAME = ENV + LOCAL_CURRENCY_INTERNAL_NAME

LOCAL_CURRENCY_SYMBOL = os.environ.get('CURRENCY_SYMBOL')

# Arguments à fournir dans la ligne de commande
parser = argparse.ArgumentParser()
parser.add_argument('url', help='URL of Cyclos')
parser.add_argument('authorization',
        help='string to use for Basic Authentication')
parser.add_argument('--debug',
                    help='enable debug messages',
                    action='store_true')
args = parser.parse_args()

if not args.url.endswith('/'):
    args.url = args.url + '/'
if args.debug:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)

for k, v in vars(args).items():
    logger.debug('args.%s = %s', k, v)

# URLs des web services
global_web_services = args.url + 'global/web-rpc/'
network_web_services = args.url + '/' + NETWORK_INTERNAL_NAME + '/web-rpc/'

# En-têtes pour toutes les requêtes (il n'y a qu'un en-tête, pour
# l'authentification).
headers = {'Authorization': 'Basic ' + args.authorization}

# On fait une 1ère requête en lecture seule uniquement pour vérifier
# si les paramètres fournis sont corrects.
logger.info('Vérification des paramètres fournis...')
r = requests.post(global_web_services + 'network/search',
                  headers=headers, json={})
check_request_status(r)


########################################################################
# Création des utilisateurs pour les banques de dépôt et les comptes
# dédiés.
#
def create_user(group, name, login, email=None, password=None,address={}, custom_values=None):
    logger.info('Création de l\'utilisateur "%s" (groupe "%s")...', name, group)
    # FIXME code à déplacer pour ne pas l'exécuter à chaque fois
    r = requests.post(network_web_services + 'group/search',
                      headers=headers, json={})
    check_request_status(r)
    groups = r.json()['result']['pageItems']
    for g in groups:
        if g['name'] == group:
            group_id = g['id']
    if not address:
        address = {'street':'7 rue Très Cloitres',
                'city':'Grenoble',
                'zipCode':'38000'}

    user_registration = {
        'group': group_id,
        'name': name,
        'username': login,
        'skipActivationEmail': True,
        'addresses':[
            {
                'name': 'work',
                'addressLine1': address['street'],
                'city': address['city'],
                'zip': address['zipCode'],
                'defaultAddress': True,
                'hidden': False
                }
            ]
    }
    if email:
        user_registration['email'] = email
    if password:
        user_registration['passwords'] = [
            {
                'type': 'login',
                'value': password,
                'confirmationValue': password,
                'assign': True,
                'forceChange': False,
            },
        ]
    if custom_values:
        user_registration['customValues'] = []
        for field_id, value in custom_values.items():
            r = requests.get(network_web_services + 'userCustomField/load/' + field_id, headers=headers)
            check_request_status(r)
            custom_field_type = r.json()['result']['type']
            if custom_field_type == 'LINKED_ENTITY':
                value_key = 'linkedEntityValue'
            user_registration['customValues'].append({
                'field': field_id,
                value_key: value,
            })
    logger.debug('create_user : json = %s', user_registration)
    r = requests.post(network_web_services + 'user/register',
                      headers=headers,
                      json=user_registration)
    check_request_status(r)
    logger.debug('result = %s', r.json()['result'])
    user_id = r.json()['result']['user']['id']
    logger.debug('user_id = %s', user_id)
    return user_id

create_user(
    group='Network administrators',
    name= 'Administrator',
    login= 'admin_network',
    email= 'administrator@localhost.fr',
    password= '@@bbccdd' #@WARNING : nécessité d'avoir ce mot de passe pour les tests appli CEL du Cairn
)

create_user(
    group='Banques de dépôt',
    name='Banque de dépôt 1',
    login='BDP1',
)
create_user(
    group='Banques de dépôt',
    name='Banque de dépôt 2',
    login='BDP2',
)


########################################################################
# Création des utilisateurs pour les tests.
if ENV != 'prod':
    # On récupère l'id du champ perso 'BDC'.
    r = requests.get(network_web_services + 'userCustomField/list', headers=headers)
    check_request_status(r)
    user_custom_fields = r.json()['result']
    for field in user_custom_fields:
        if field['internalName'] == 'bdc':
            id_user_custom_field_bdc = field['id']

    gestion_interne = {
        'demo': 'Demo',
        'demo2': 'Demo2',
    }
    for login, name in gestion_interne.items():
        create_user(
            group='Gestion interne',
            name=name,
            login=login,
            password=login,
        )

    bureaux_de_change = {
        'B000': 'Association Monnaie Locale',
        'B001': 'Bureau de change 1',
        'B002': 'Bureau de change 2',
    }
    for login, name in bureaux_de_change.items():
        id_bdc = create_user(
            group='Bureaux de change',
            name=name + ' (BDC)',
            login=login + '_BDC',
            password=login,
        )
        create_user(
            group='Opérateurs BDC',
            name=name,
            login=login,
            password=login,
            custom_values={
                id_user_custom_field_bdc: id_bdc,
            }
        )

    create_user(
        group='Anonyme',
        name='Anonyme',
        login='anonyme',
        password='anonyme',
    )

    adherents_utilisateurs = [
        ['gjanssens', 'Janssens Gaetan'],
        ['cretine_agnes', 'Créttine Agnès'],
        ['alberto_malik', 'Malik Alberto'],
        ['noire_aliss', 'La noire Aliss'],
        ['tous_andre', 'Tous Ensemble André'],
        ['speedy_andrew', 'Speedy Andrew'],
        ['stuart_andrew', 'Stuart Andrew'],
        ['crabe_arnold', 'Le Crabe Arnold'],
        ['barbare_cohen', 'le Barbare Cohen'],
        ['lacreuse_desiderata', 'Lacreuse Desiderata'],
        ['comblant_michel', 'Comblant Michel'],
        ['nico_faus_perso', 'Le Caméléon Nicolas'],
        ['benoit_perso', 'Le Rigolo Benoît'],
    ]

    adherents_prestataires = [
        ['asso_mlc', 'Association Monnaie Locale','7 rue Très Cloitres','Grenoble','38000'],
        ['maltobar', 'MaltOBar','1 place Edmond Arnaud','Grenoble','38000'],
        ['labonnepioche', 'La Bonne Pioche','2 rue Condillac','Grenoble','38000'],
        ['DrDBrew', 'DocteurD Brew Pub','2 rue des Clercs','Grenoble','38000'],
        ['apogee_du_vin', 'Apogée du vin','6 rue Lesdigueres','Grenoble','38000'],
        ['tout_1_fromage', 'Tout un fromage','99 Cours Berriat','Grenoble','38000'],
        ['vie_integrative', 'vie intégrative','1 Avenue Georges Frier','Voiron','38500'],
        ['denis_ketels', 'Denis Ketels','36 RUE SERMORENS','Voiron','38500'], #used only for changePassword test
        ['nico_faus_prod', 'Nico Faus Production','1 rue Colonel Dumont','Grenoble','38000'],
        ['hirundo_archi', 'Hirundo Architecture','30 rue Nicolas Chorier','Grenoble','38000'],
        ['maison_bambous', 'Maison aux Bambous','100 Chemin du Tilleul','Vinay','38470'],
        ['recycleco', 'Recycleco','Route de la Croix de May','Saint-Sauveur','38160'],
        ['elotine_photo', 'Elotine Photo','13 Rue Montorge','Grenoble','38000'],
        ['boule_antan', 'La Boule d Antan','50 Rue Vaucanson','Villard-de-Lans','38250'],
        ['la_remise', 'La Remise','35 Rue Général Ferrié','Grenoble','38100'],
        ['episol', 'Episol','45 Rue Général Ferrié','Grenoble','38000'],
        ['alter_mag', 'Alter Mag','39 grande Rue','Saint-Marcellin','38160'],
        ['verre_a_soi', 'Le Verre à soi','34 ROUTE DE CHARAVINES','Bilieu','38850'],
        ['FluoDelik', 'Fluodélik','La place Gérard Clet','Méaudre','38112'],
        ['1001_saveurs', '1001 Saveurs','69 Rue des Pionniers','Villard-de-Lans','38250'],
        ['belle_verte', 'La Belle Verte','Route Pont de la Fange','Susville','38350'],
        ['kheops_boutique', 'Khéops boutique','40 grande Rue','Saint-Marcellin','38160'],
        ['ferme_bressot', 'La ferme du Bressot','761 chemin du Bressot','Beaulieu','38470'],
        ['atelier_eltilo', 'Atelier Eltilo','147 bis cours Berriat','Grenoble','38000'],
        ['la_belle_verte', 'Belle Verte Permaculture','589 rue Vaugauthier','Sillans','38590'],
        ['mon_vrac', 'Mon Vrac','16 Rue Dode','Voiron','38500'],
        ['le_marque_page', 'Le Marque Page','8 grande Rue','Saint-Marcellin','38160'],
        ['boutik_creative', 'La Boutik Creative','54 Rue de la République','Rives','38140'],
        ['pain_beauvoir', 'Le Pain de Beauvoir','18 Rue porte d\'aris','Beauvoir-en-Royans','38160'],
        ['la_mandragore', 'La Mandragore','4 bis Rue de Bonne','Grenoble','38000'],
        ['jardins_epices', 'Les jardins epicés tout','967 Chemin des Terres','Herbeys','38320'],
        ['lib_colibri', 'Librairie Colibri','6 Rue Adolphe Péronnet','Voiron','38500'],
        ['Claire_Dode', 'La Vie Claire Dode',' 6 Rue Louis Leprince Ringuet','Voiron','38500'],
        ['fil_chantant', 'Le Fil qui Chante','3 Rue Porte de la Buisse','Voiron','38500'],
        ['epicerie_sol', 'Epicerie Solidaire Amandine','14 Rue Porte de la Buisse','Voiron','38500'],
        ['NaturaVie', 'Naturavie','12 rue Dode','Voiron','38500'],
        ['montagne_arts', 'Les montagnarts','1034 Rue Principale','Valbonnais','38740'],
        ['Biocoop', 'Biocoop','ZA La Gloriette','Chatte','38160'],
        ['Alpes_EcoTour', 'Alpes Ecotourisme','63 rue emile Zola','Grenoble','38100'],
        ['trankilou', 'Le Trankilou','45 Boulevard Joseph Vallier','Grenoble','38000']
    ]

    groupes_locaux = [
        ['gl_grenoble', 'Groupe Local Grenoble','7 rue Très Cloitres','Grenoble','38000'],
        ['gl_voiron', 'Groupe Local Voiron','12 Rue Mainssieux','Voiron','38500'],
        ['gl_tullins', 'Groupe Local Tullins','Clos des Chartreux','Tullins','38210'],
    ]

    for member in adherents_utilisateurs:
        create_user(
            group='Adhérents utilisateurs',
            name=member[1],
            login=member[0],
            email = member[0] + '@test.fr',
            password = '@@bbccdd',
        )

    create_user(
        group='Adhérents utilisateurs',
        name='Max Maz',
        login='mazmax',
        email = 'maxime.mazouth-laurol@cairn-monnaie.com',
        password = '@@bbccdd',
    )

    for member in adherents_prestataires:
        create_user(
            group='Adhérents prestataires',
            name=member[1],
            login=member[0],
            email = member[0] + '@test.fr',
            password = '@@bbccdd',
            address = {'street': member[2],'city':member[3],'zipCode':member[4]}
        )

    for member in groupes_locaux:
        create_user(
            group='Network administrators',
            name=member[1],
            login=member[0],
            email = member[0] + '@test.fr',
            password = '@@bbccdd',
            address = {'street': member[2],'city':member[3],'zipCode':member[4]}
        )

    porteurs = {
        'P001': 'Porteur 1',
        'P002': 'Porteur 2',
        'P003': 'Porteur 3',
        'P004': 'Porteur 4',
    }
    for login, name in porteurs.items():
        create_user(
            group='Porteurs',
            name=name,
            login=login,
        )

    # Récupération des constantes

    logger.info('Récupération des constantes depuis le YAML...')
    CYCLOS_CONSTANTS = None
    with open("/cyclos/cyclos_constants_"+ENV+".yml", 'r') as cyclos_stream:
        try:
            CYCLOS_CONSTANTS = yaml.load(cyclos_stream)
        except yaml.YAMLError as exc:
            assert False, exc

    # Impression billets mlc
    logger.info('Impression billets '+ LOCAL_CURRENCY_INTERNAL_NAME +'...')
    logger.debug(str(CYCLOS_CONSTANTS['payment_types']['impression_de_billets_mlc']) + "\r\n" +
                 str(CYCLOS_CONSTANTS['currencies']['mlc']) + "\r\n" +
                 str(CYCLOS_CONSTANTS['account_types']['compte_de_debit_mlc_billet']) + "\r\n" +
                 str(CYCLOS_CONSTANTS['account_types']['stock_de_billets']))


    r = requests.post(network_web_services + 'payment/perform',
                      headers={'Authorization': 'Basic {}'.format(base64.standard_b64encode(b'demo:demo').decode('utf-8'))},  # noqa
                      json={
                          'type': CYCLOS_CONSTANTS['payment_types']['impression_de_billets_mlc'],
                          'amount': 126500,
                          'currency': CYCLOS_CONSTANTS['currencies']['mlc'],
                          'from': 'SYSTEM',
                          'to': 'SYSTEM',
                      })

    logger.info('Impression billets ' + LOCAL_CURRENCY_INTERNAL_NAME + '... Terminé !')
    logger.debug(r.json())

    #@WARNING : specifique au cairn, à supprimer dans le rendu au mvt Sol
    today = datetime.now()

    def date_modify(nb_days):
            today = datetime.now()
            date = today + timedelta(days=nb_days)
            return date.strftime("%Y")+ '-' + date.strftime("%m")+'-'+date.strftime("%d")


    def credit_numeric_money_safe(amount):
        logger.info('Creation de MLC numeriques  ...')
        r = requests.post(network_web_services + 'payment/perform',
                          headers={'Authorization': 'Basic {}'.format(base64.standard_b64encode(b'admin_network:@@bbccdd').decode('utf-8'))},
                          json={
                              'type': CYCLOS_CONSTANTS['payment_types']['creation_mlc_numeriques'],
                              'amount': amount,
                              'currency': CYCLOS_CONSTANTS['currencies']['mlc'],
                              'from': 'SYSTEM',
                              'to': 'SYSTEM',
                              'description': 'creation initiale de ' + LOCAL_CURRENCY_INTERNAL_NAME ,
                          })
        logger.info('Creation de MLC numeriques... Terminé !')
        logger.debug(r.json())

    def credit_de_compte(member,amount):
        logger.info('Change numérique pour ' + member[1] + ' ...')
        r = requests.post(network_web_services + 'payment/perform',
                          headers={'Authorization': 'Basic {}'.format(base64.standard_b64encode(b'admin_network:@@bbccdd').decode('utf-8'))},
                          json={
                              'type': CYCLOS_CONSTANTS['payment_types']['credit_du_compte'],
                              'amount': amount,
                              'currency': CYCLOS_CONSTANTS['currencies']['mlc'],
                              'from': 'SYSTEM',
                              'to': member[0],
                              'description': 'dépôt ' + LOCAL_CURRENCY_INTERNAL_NAME ,
                              'customValues': [
                                  {
                                      'field': str(CYCLOS_CONSTANTS['transaction_custom_fields']['bdc']),
                                      'linkedEntityValue': id_bdc  # ID de l'utilisateur Bureau de change
                                      },
                                  ]
                          })
        logger.info('Change numérique pour ' + member[1] + '... Terminé !')
        logger.debug(r.json())

    def payment_inter_adherent(debitor, creditor, amount, offset):
        logger.info('Virement de ' + str(amount) + ' ' + LOCAL_CURRENCY_INTERNAL_NAME + ' ' + debitor + ' vers ' + creditor + ' ...')

        if offset == 0:
            cyclos_method = 'payment/perform'
        else:
            cyclos_method = 'scheduledPayment/perform'

        r = requests.post(network_web_services + cyclos_method,
                          headers={'Authorization': 'Basic {}'.format(base64.standard_b64encode(b'admin_network:@@bbccdd').decode('utf-8'))},
                          json={
                              'type': CYCLOS_CONSTANTS['payment_types']['virement_inter_adherent'],
                              'amount': amount,
                              'currency': CYCLOS_CONSTANTS['currencies']['mlc'],
                              'description': 'virement ' + LOCAL_CURRENCY_INTERNAL_NAME ,
                              'firstInstallmentDate': date_modify(offset),
                              'installmentsCount': 1,
                              'from': debitor,
                              'to': creditor,
                          })
        logger.info('Virement de ' + str(amount) + ' ' + LOCAL_CURRENCY_INTERNAL_NAME + ' '  + debitor + ' vers ' + creditor + ' ... Terminé !')
        logger.debug(r.json())

    #Creation initiale de MLC numeriques
    credit_numeric_money_safe(10000000000)

    # Changes numériques afin d'avoir des comptes avec des soldes non nuls + des opérations à injecter dans l'appli CEL
    logger.info('Changes numériques en '+ LOCAL_CURRENCY_INTERNAL_NAME +' pour tous les pros à Grenoble...')
    logger.debug(str(CYCLOS_CONSTANTS['payment_types']['credit_du_compte']) + "\r\n" +
                 str(CYCLOS_CONSTANTS['account_types']['compte_de_debit_mlc_numerique']) + "\r\n" +
                 str(CYCLOS_CONSTANTS['account_types']['compte_d_adherent']))

    initial_credit = 1000

    for pro in adherents_prestataires:
        if pro[2] == 'Grenoble':
            credit_de_compte(pro, initial_credit)

    for person in adherents_utilisateurs:
        credit_de_compte(person, initial_credit)

    logger.info('Changes numériques en ' + LOCAL_CURRENCY_INTERNAL_NAME + '... Terminé !')

    logger.info('Virements immédiats de compte à compte en '+ LOCAL_CURRENCY_INTERNAL_NAME +' ...')

    #trankilou has null account again
    logger.info('"Le Trankilou" réalise un virement vers "la Remise" remettant son solde à 0')
    payment_inter_adherent('trankilou','la_remise',initial_credit,0)

#    for i in range(0,10):
#        payment_inter_adherent('DrDBrew','apogee_du_vin',10,0)

    logger.info('Virements immédiats de compte à compte en '+ LOCAL_CURRENCY_INTERNAL_NAME +'... Terminé !')

    logger.info('Virements programmés en '+ LOCAL_CURRENCY_INTERNAL_NAME +' de La Bonne Pioche vers AlterMag...')
    for i in range(0,5):
        payment_inter_adherent('labonnepioche','alter_mag',10,2)

    logger.info('Virements programmés en '+ LOCAL_CURRENCY_INTERNAL_NAME +' ... Terminé !!')

logger.info('Fin du script !')
