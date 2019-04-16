import logging

from django import forms
from django.conf import settings
from django.core.validators import validate_email
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from base64 import b64encode
from cyclos_api import CyclosAPI, CyclosAPIException
from cyclos_data import serializers

log = logging.getLogger('console')


@api_view(['POST'])
@permission_classes((AllowAny, ))
def login(request):
    """
    User login from cyclos
    """
    serializer = serializers.LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)  # log.critical(serializer.errors)

    try:
        cyclos = CyclosAPI()

        try:
            username = request.data['username']
            password = request.data['password']

            if not (username and password):
                raise AuthenticationFailed()

            auth_string=b64encode(bytes('{}:{}'.format(username, password), 'utf-8')).decode('ascii')
            cyclos_token = cyclos.login(auth_string)
            log.debug(cyclos_token)
        except CyclosAPIException:
            raise AuthenticationFailed()

    except (CyclosAPIException, KeyError, IndexError):
        raise AuthenticationFailed()

    return Response({'auth_token': cyclos_token, 'login': username})


@api_view(['GET'])
@permission_classes((AllowAny, ))
def verify_usergroup(request):
    """
    Verify that username is in a usergroup
    """
    serializer = serializers.VerifyUsergroupSerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)  # log.critical(serializer.errors)

    try:
        cyclos = CyclosAPI()
        try:
            auth_token = request.query_params['api_key']
            username = request.query_params['username']
            log.debug('username : ' + username)
            log.debug('auth_token : ' + auth_token)
            # à partir du username, récupérer id
            user_id = cyclos.get_member_id_from_login(member_login=username, token=auth_token)
            log.debug('id : ' + user_id)

            # à partir de l'id, récupérer la liste des groupes
            user_dto = cyclos.get(method='user/load', id=user_id, token=auth_token)['result']
        except (CyclosAPIException, KeyError, IndexError):
            return Response({'error': 'Unable to get user data (ID or groups) from your username!'},
                    status=status.HTTP_400_BAD_REQUEST)

    except CyclosAPIException:
        return Response({'error': 'Unable to connect to Cyclos!'}, status=status.HTTP_400_BAD_REQUEST)

    # get group of the authenticated user
    usergroup_id = user_dto['group']['id']
    log.debug(usergroup_id)
    try:
        group_constant_id = str(settings.CYCLOS_CONSTANTS['groups'][request.query_params['usergroup']])
    except KeyError:
        return Response(status=status.HTTP_204_NO_CONTENT)

    if group_constant_id == usergroup_id:
        return Response('OK')
    else:
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
def get_bdc_name(request):
    """
    Get the bdc name (lastname) for the current user.
    """
    return Response(request.user.profile.lastname)

@api_view(['GET'])
def get_digital_mlc_available(request):
    """
    Get the amount of digital mlc available in money safe
    """

    try:
        cyclos = CyclosAPI(token=request.user.profile.cyclos_token, mode='bdc')
        try:
#            auth_token = request.query_params['api_key']
#            username = request.query_params['username']
#            log.debug('username : ' + username)
#            log.debug('auth_token : ' + auth_token)
            query_data = [cyclos.user_id, None]
            accounts_summaries_data = cyclos.post(method='account/getAccountsSummary', data=query_data)

            # Stock de billets: stock_de_billets                                       
            # Compte de transit: compte_de_transit                                     
            res = {}
            filter_keys = ['compte_de_debit_mlc_numerique']
            for filter_key in filter_keys:
                data = [item
                        for item in accounts_summaries_data['result']
                        if item['type']['id'] == str(settings.CYCLOS_CONSTANTS['account_types'][filter_key])][0]

                res[filter_key] = {}
                res[filter_key]['balance'] = float(data['status']['balance'])
                res[filter_key]['currency'] = data['currency']['symbol']

        except (CyclosAPIException, KeyError, IndexError):
            return Response({'error': 'Unable to get account balance!'},
                    status=status.HTTP_400_BAD_REQUEST)

    except CyclosAPIException:
        return Response({'error': 'Unable to connect to Cyclos!'}, status=status.HTTP_400_BAD_REQUEST)

    return Response(res[filter_key])

#@api_view(['GET'])
#def get_usergroups(request):
#    """
#    Get usergroups for a username
#    """
#    serializer = serializers.GetUsergroupsSerializer(data=request.query_params)
#    serializer.is_valid(raise_exception=True)  # log.critical(serializer.errors)
#
#    try:
#        dolibarr = DolibarrAPI(api_key=request.user.profile.dolibarr_token)
#        user_results = dolibarr.get(model='users', sqlfilters="login='{}'".format(request.query_params['username']))
#
#        user_id = [item
#                for item in user_results
#                if item['login'] == request.query_params['username']][0]['id']
#    except DolibarrAPIException:
#        return Response({'error': 'Unable to connect to Dolibarr!'}, status=status.HTTP_400_BAD_REQUEST)
#    except (KeyError, IndexError):
#        return Response({'error': 'Unable to get user ID from your username!'}, status=status.HTTP_400_BAD_REQUEST)
#
#    return Response(dolibarr.get(model='users/{}/groups'.format(user_id)))
#
#
#@api_view(['GET'])
#def associations(request):
#    """
#    List all associations, and if you want, you can filter them.
#    """
#    dolibarr = DolibarrAPI(api_key=request.user.profile.dolibarr_token)
#    results = dolibarr.get(model='associations')
#    approved = request.GET.get('approved', '')
#    if approved:
#        # We want to filter out the associations that doesn't have the required sponsorships
#        filtered_results = [item
#                for item in results
#                if int(item['nb_parrains']) >= settings.MINIMUM_PARRAINAGES_3_POURCENTS]
#        return Response(filtered_results)
#    else:
#        return Response(results)
#
#
#@api_view(['GET'])
#def towns_by_zipcode(request):
#    """
#    List all towns, filtered by a zipcode.
#    """
#    search = request.GET.get('zipcode', '')
#    if not search:
#        return Response({'error': 'Zipcode must not be empty'}, status=status.HTTP_400_BAD_REQUEST)
#
#    dolibarr = DolibarrAPI(api_key=request.user.profile.dolibarr_token)
#    return Response(dolibarr.get(model='setup/dictionary/towns', zipcode=search))
#
#
#@api_view(['GET'])
#def countries(request):
#    """
#    Get the list of countries.
#    """
#    dolibarr = DolibarrAPI(api_key=request.user.profile.dolibarr_token)
#    return Response(dolibarr.get(model='setup/dictionary/countries', lang='fr_FR'))
#
#


#@api_view(['GET'])
#def get_username(request):
#    """
#    Get the username for the current user.
#    """
#    return Response(str(request.user))
#
#
#@api_view(['GET'])
#def get_member_name(request):
#    """
#    Get the member name (firstname + lastname or companyname) for the current user.
#    """
#    if request.user.profile.companyname:
#        member_name = '{}'.format(request.user.profile.companyname)
#    else:
#        member_name = '{} {}'.format(request.user.profile.firstname, request.user.profile.lastname)
#    return Response(member_name)
#
#
#@api_view(['GET'])
#def get_user_data(request):
#    """
#    Get user data for a user.
#    """
#    serializer = serializers.GetUserDataSerializer(data=request.query_params)
#    serializer.is_valid(raise_exception=True)  # log.critical(serializer.errors)
#
#    try:
#        username = serializer.data['username']
#    except KeyError:
#        username = str(request.user)
#
#    try:
#        dolibarr = DolibarrAPI(api_key=request.user.profile.dolibarr_token)
#        user_results = dolibarr.get(model='users', sqlfilters="login='{}'".format(username))
#
#        user_data = [item
#                for item in user_results
#                if item['login'] == username][0]
#    except DolibarrAPIException:
#        return Response({'error': 'Unable to connect to Dolibarr!'}, status=status.HTTP_400_BAD_REQUEST)
#    except IndexError:
#        return Response({'error': 'Unable to get user data from this user!'}, status=status.HTTP_400_BAD_REQUEST)
#
#    return Response(user_data)
