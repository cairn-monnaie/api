""" euskalmoneta API URL Configuration """

from django.conf.urls import url
from rest_framework import routers

from bureauxdechange.views import BDCAPIView
from members.views import MembersAPIView, MembersSubscriptionsAPIView
from cel.beneficiaire import BeneficiaireViewSet
from cel.security_qa import SecurityQAViewSet

from auth_token import views as auth_token_views
import bdc_cyclos.views as bdc_cyclos_views
import cel.views as cel_views
import cyclos_data.views as cyclos_data_views
import dolibarr_data.views as dolibarr_data_views
import association_data.views as association_data_views
import gestioninterne.views as gi_views
import gestioninterne.credits_comptes_prelevements_auto as credits_views


router = routers.SimpleRouter()
router.register(r'bdc', BDCAPIView, base_name='bdc')
router.register(r'members', MembersAPIView, base_name='members')
router.register(r'members-subscriptions', MembersSubscriptionsAPIView, base_name='members-subscriptions')
router.register(r'beneficiaires', BeneficiaireViewSet, base_name='beneficiaires')
router.register(r'securityqa', SecurityQAViewSet, base_name='securityqa')

urlpatterns = [
    # Auth token
    url(r'^api-token-auth/', auth_token_views.obtain_auth_token),
    # Cyclos data, data we fetch from its API
    url(r'^login/$', cyclos_data_views.login),
    url(r'^usergroups/$', dolibarr_data_views.get_usergroups),
    url(r'^verify-usergroup/$', cyclos_data_views.verify_usergroup),
    url(r'^associations/$', dolibarr_data_views.associations),
    url(r'^countries/$', dolibarr_data_views.countries),
    url(r'^bdc-name/$', cyclos_data_views.get_bdc_name),
    url(r'^available-electronic-mlc/$', cyclos_data_views.get_digital_mlc_available),
    url(r'^member-name/$', dolibarr_data_views.get_member_name),
    url(r'^user-data/$', dolibarr_data_views.get_user_data),
    url(r'^username/$', dolibarr_data_views.get_username),
    url(r'^towns/$', dolibarr_data_views.towns_by_zipcode),

    # Euskal moneta data (hardcoded data we dont fetch from APIs)
    url(r'^payment-modes/$', association_data_views.payment_modes),
    url(r'^porteurs-mlc/$', association_data_views.porteurs_mlc),
    url(r'^deposit-banks/$', association_data_views.deposit_banks),

    # Cyclos data, data we fetch from/push to its API
    url(r'^accounts-summaries/(?P<login_bdc>[\w\-]+)?/?$', bdc_cyclos_views.accounts_summaries),
    url(r'^system-accounts-summaries/$', bdc_cyclos_views.system_accounts_summaries),
    url(r'^dedicated-accounts-summaries/$', bdc_cyclos_views.dedicated_accounts_summaries),
    url(r'^deposit-banks-summaries/$', bdc_cyclos_views.deposit_banks_summaries),
    url(r'^accounts-history/$', bdc_cyclos_views.accounts_history),
    url(r'^payments-available-entree-stock/$', bdc_cyclos_views.payments_available_for_entree_stock),
    url(r'^entree-stock/$', bdc_cyclos_views.entree_stock),
    url(r'^sortie-stock/$', bdc_cyclos_views.sortie_stock),
    url(r'^change-euro-mlc/$', bdc_cyclos_views.change_euro_mlc),
    url(r'^change-euro-mlc-numeriques/$', bdc_cyclos_views.change_euro_mlc_numeriques),
    url(r'^reconversion/$', bdc_cyclos_views.reconversion),
    url(r'^bank-deposit/$', bdc_cyclos_views.bank_deposit),
    url(r'^cash-deposit/$', bdc_cyclos_views.cash_deposit),
#    url(r'^sortie-caisse-mlc/$', bdc_cyclos_views.cash_deposit),
    url(r'^sortie-retour-mlc/$', bdc_cyclos_views.sortie_retour_mlc),
    url(r'^depot-mlc-numerique/$', bdc_cyclos_views.depot_mlc_numerique),
    url(r'^retrait-mlc-numerique/$', bdc_cyclos_views.retrait_mlc_numerique),
    url(r'^change-password/$', bdc_cyclos_views.change_password),

    # Endpoints for Gestion Interne
    url(r'^banks-history/$', gi_views.payments_available_for_banques),
    url(r'^sortie-coffre/$', gi_views.sortie_coffre),
    url(r'^payments-available-entree-coffre/$', gi_views.payments_available_for_entree_coffre),
    url(r'^entree-coffre/$', gi_views.entree_coffre),
    url(r'^payments-available-entrees-euro/$', gi_views.payments_available_for_entrees_euro),
    url(r'^validate-entrees-euro/$', gi_views.validate_history),
    url(r'^payments-available-entrees-mlc/$', gi_views.payments_available_for_entrees_mlc),
    url(r'^validate-entrees-mlc/$', gi_views.validate_history),
    url(r'^payments-available-banques/$', gi_views.payments_available_for_banques),
    url(r'^validate-banques-rapprochement/$', gi_views.validate_history),
    url(r'^validate-banques-virement/$', gi_views.validate_banques_virement),
    url(r'^payments-available-depots-retraits/$', gi_views.payments_available_depots_retraits),
    url(r'^validate-depots-retraits/$', gi_views.validate_depots_retraits),
    url(r'^payments-available-reconversions/$', gi_views.payments_available_for_reconversions),
    url(r'^validate-reconversions/$', gi_views.validate_reconversions),
    url(r'^calculate-3-percent/$', gi_views.calculate_3_percent),
    url(r'^export-vers-odoo/$', gi_views.export_vers_odoo),
    url(r'^change-par-virement/$', gi_views.change_par_virement),
    url(r'^paiement-cotisation-mlc-numerique/$', gi_views.paiement_cotisation_mlc_numerique),

    # Crédit des comptes Eusko par prélèvement automatique
    url(r'^credits-comptes-prelevement-auto/import/(?P<filename>[^/]+)$', credits_views.import_csv),
    url(r'^credits-comptes-prelevement-auto/perform/$', credits_views.perform),
    url(r'^credits-comptes-prelevement-auto/delete/$', credits_views.delete),
    url(r'^credits-comptes-prelevement-auto/list/(?P<mode>[^/]+)$', credits_views.list),

    # Endpoints for Compte en Ligne
    url(r'^first-connection/$', cel_views.first_connection),
    url(r'^validate-first-connection/$', cel_views.validate_first_connection),
    url(r'^lost-password/$', cel_views.lost_password),
    url(r'^validate-lost-password/$', cel_views.validate_lost_password),

    url(r'^payments-available-history-adherent/$', cel_views.payments_available_for_adherents),
    url(r'^account-summary-adherents/$', cel_views.account_summary_for_adherents),
    url(r'^export-history-adherent/$', cel_views.export_history_adherent),
    url(r'^export-rie-adherent/$', cel_views.export_rie_adherent),
    url(r'^has-account/$', cel_views.has_account),
    url(r'^one-time-transfer/$', cel_views.one_time_transfer),
    url(r'^reconvert-mlc/$', cel_views.reconvert_mlc),
    url(r'^user-rights/$', cel_views.user_rights),
    url(r'^accept-cgu/$', cel_views.accept_cgu),
    url(r'^refuse-cgu/$', cel_views.refuse_cgu),

    # mlckart
    url(r'^mlckart/$', cel_views.mlckart_list),
    url(r'^mlckart-block/$', cel_views.mlckart_block),
    url(r'^mlckart-unblock/$', cel_views.mlckart_unblock),
    url(r'^mlckart-pin/$', cel_views.mlckart_pin),
    url(r'^mlckart-upd-pin/$', cel_views.mlckart_update_pin),
    url(r'^member-cel-subscription/$', cel_views.members_cel_subscription),

]

urlpatterns += router.urls
