#!/usr/bin/env python


"""
File name: reg_pool_tool.py
Author: Tim Thomas
Date created: 10/19/2018
Date last modified: 10/19/2018
Python Version: 2.7.15
version:
    0.0.1 

./reg_pool_tool.py -h for usage.


Example:

To install addon key to existing offering:

./reg_pool_tool.py -a 10.3.214.7 -m <reg_key_pool> -r <offering> -A <add_on_key>



Copyright 2018 Tim Thomas

Licensed under the Apache License, Version 2.0 (the "License"); you may not use
this file except in compliance with the License. You may obtain a copy of the
License at:

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed
under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
CONDITIONS OF ANY KIND, either express or implied. See the License for the
specific language governing permissions and limitations under the License.






"""

from __future__ import print_function
import argparse
from base64 import b64encode
import json
#from pprint import pprint
import sys
import time
import urllib3
import requests


### Arguments parsing section ###
def cmd_args():
    """Handles command line arguments given."""
    parser = argparse.ArgumentParser(description='This is a tool for working'
                                                 'with regkey pool on BIG-IQ')
    parser.add_argument('-d',
                        '--debug',
                        action="store_true",
                        default=False,
                        help='enable debug')
    parser.add_argument('-v',
                        '--verbose',
                        action="store_true",
                        default=False,
                        help='enable verbose for options that have it')
    parser.add_argument('-a',
                        '--address',
                        action="store",
                        dest="address",
                        help='IP address of the target host')
    parser.add_argument('-u',
                        '--username',
                        action="store",
                        dest="username",
                        default='admin',
                        help='username for auth to host')
    parser.add_argument('-p',
                        '--password',
                        action="store",
                        dest="password",
                        default='admin',
                        help='password for auth to host')
    parser.add_argument('-l',
                        '--list-pools',
                        action="store_true",
                        default=False,
                        help='list the UUIDs for existing regkey pools, requires no args')
    parser.add_argument('-o',
                        '--offerings',
                        action="store",
                        dest="pool_uuid",
                        help='take UUID of pool as arg and list the offerings for a pool'
                             ' use -v to also show the active modules')
    parser.add_argument('-r',
                        '--regkey',
                        action="store",
                        dest="reg_key",
                        help='takes and stores the regkey for use in other options')
    parser.add_argument('-A',
                        '--add-on-keys',
                        action="store",
                        dest="add_on_key_list",
                        help='takes string of comma sep addon keys for use by other options')
    parser.add_argument('-i',
                        '--install-offering',
                        action="store",
                        dest="install_pool_uuid",
                        help='takes pool UUID as arg and installs new offering,'
                             'requires -r, -A can be used to install addon keys at'
                             'the same time')
    parser.add_argument('-m',
                        '--modify-offering-addons',
                        action="store",
                        dest="modify_pool_uuid",
                        help='takes pool UUID as arg and installs addon to offering,'
                             'requires -A [addon_key_list] and -r reg_key')


    parsed_arguments = parser.parse_args()

    # debug set print parser info
    if parsed_arguments.debug is True:
        print(parsed_arguments)


    # required args here
    if parsed_arguments.address is None:
        parser.error('-a target address is required, '
                     'use mgmt for local')
    if parsed_arguments.install_pool_uuid:
        if parsed_arguments.reg_key is None:
            parser.error('-i requires -r')
    if parsed_arguments.modify_pool_uuid:
        if parsed_arguments.add_on_key_list is None:
            parser.error('-m requires -A and -r')
        elif parsed_arguments.reg_key is None:
            parser.error('-m requires -A and -r')

    return parsed_arguments

### END ARGPARSE SECTION ###


def get_auth_token(address, user, password,
                   uri='/mgmt/shared/authn/login'):  # -> unicode
    """Get and auth token( to be used but other requests"""
    credentials_list = [user, ":", password]
    credentials = ''.join(credentials_list)
    user_and_pass = b64encode(credentials).decode("ascii")
    headers = {'Authorization':'Basic {}'.format(user_and_pass), 'Content-Type':'application/json'}
    post_data = '{"username":"' + user + '","password":"' + password +'"}'
    url_list = ['https://', address, uri]
    url = ''.join(url_list)
    try:
        request_result = requests.post(url, headers=headers, data=post_data, verify=False)
    except requests.exceptions.ConnectionError as connection_error:
        print(connection_error)
        sys.exit(1)
    except requests.exceptions.RequestException as request_exception:
        print(request_exception)
        sys.exit(1)

    #returns an instance of unicode that is an auth token with 300 dec timeout
    return request_result.json()['token']['token']


def get(url, auth_token, debug=False, return_encoding='json'):
    """Generic GET function. The return_encoding can be:'text', 'json', 'content'(binary),
    or raw """
    headers = {'X-F5-Auth-Token':'{}'.format(auth_token), 'Content-Type':'application/json'}

    get_result = requests.get(url, headers=headers, verify=False)

    if debug is True:
        print('GET request...')
        print('get_result.encoding: {}'.format(get_result.encoding))
        print('get_result.status_code: {}'.format(get_result.status_code))
        print('get_result.raise_for_status: {}'.format(
            get_result.raise_for_status()))

    if return_encoding == 'json':
        return get_result.json()
    elif return_encoding == 'text':
        return get_result.text
    elif return_encoding == 'content':
        return get_result.content
    elif return_encoding == 'raw':
        return get_result.raw()  # requires 'stream=True' in request


def post(url, auth_token, post_data, debug):
    """ generic POST function """
    headers = {'X-F5-Auth-Token':'{}'.format(auth_token), 'Content-Type':'application/json'}
    #post_data = '{"key":"value"}'
    try:
        post_result = requests.post(url, post_data, headers=headers, verify=False, timeout=10)
    except requests.exceptions.ConnectionError as connection_error:
        print ("Error Connecting: {}".format(connection_error))
        sys.exit(1)
    except requests.exceptions.RequestException as request_exception:
        print(request_exception)
        sys.exit(1)

    if debug is True:
        print('POST request...')
        print('post_result.encoding: {}'.format(post_result.encoding))
        print('post_result.status_code: {}'.format(post_result.status_code))
        print('post_result.raise_for_status: {}'.format(
            post_result.raise_for_status()))

    return post_result.json()


def patch(url, auth_token, patch_data, debug):
    """generic PATCH function"""
    headers = {'X-F5-Auth-Token':'{}'.format(auth_token), 'Content-Type':'application/json'}
    #patch_data = '{"key":"value"}'
    try:
        patch_result = requests.patch(url, patch_data, headers=headers, verify=False, timeout=10)
    except requests.exceptions.ConnectionError as connection_error:
        print ("Error Connecting: {}".format(connection_error))
        sys.exit(1)
    except requests.exceptions.RequestException as request_exception:
        print(request_exception)
        sys.exit(1)

    if debug is True:
        print('PATCH request...')
        print('patch_result.encoding: {}'.format(patch_result.encoding))
        print('patch_result.status_code: {}'.format(patch_result.status_code))
        print('patch_result.raise_for_status: {}'.format(
            patch_result.raise_for_status()))

    return patch_result.json()


def ls_pools(address, auth_token):  # -> List[{dict}]
    """ Lists existing regkey pools """
    uri = '/mgmt/cm/device/licensing/pool/regkey/licenses'
    url_list = ['https://', address, uri]
    url = ''.join(url_list)
    pool_list_result = get(url, auth_token, debug=False, return_encoding='json')

    # returns list of dict for each regkey pool
    return pool_list_result['items']


def list_offereings(address, auth_token, regkey_pool_uuid):
    """Returns a list of offerings for the regkey pool UUID given"""
    url_list = ['https://', address, '/mgmt/cm/device/licensing/pool/regkey/licenses/',
                regkey_pool_uuid, '/offerings']
    url = ''.join(url_list)
    offering_get_result = get(url, auth_token, debug=False, return_encoding='json')
    offering_list_result = offering_get_result['items']

    # returns list of dictionaries of offerings
    return offering_list_result



#pylint: disable-msg=too-many-arguments
# pylint: disable-msg=too-many-locals
def install_offering(address, auth_token, regkey_pool_uuid, new_regkey, add_on_keys, debug):
    """
    :type regkey_pool_uuid: str
    :type new_regkey: str
    :type add_on_keys: str comma sep keys

    This fucntion installs a new base regkey and optional addon keys and
    install, and attempts to activate. All status in printed by the function
    and there is no return statement. If it fails it will show that was well.
    """
    uri = '/mgmt/cm/device/licensing/pool/regkey/licenses/'
    url_list = ['https://', address, uri, regkey_pool_uuid, '/offerings/']
    url = ''.join(url_list)

    if add_on_keys:
        post_dict = {
            "regKey": new_regkey,
            "status": "ACTIVATING_AUTOMATIC",
            "addOnKeys": add_on_keys.split(','),
            "description" : ""
        }
    else:
        post_dict = {
            "regKey": new_regkey,
            "status": "ACTIVATING_AUTOMATIC",
            "description" : ""
        }
    # format dict to make sure it is json compliant
    payload = json.dumps(post_dict)
    try:
        post(url, auth_token, payload, debug)
        print('\nSent base regkey {} to License server status:'.format(new_regkey))
    except:
        print('Post to License server failed')
        raise

    # poll for "eulaText"
    poll_result = {}
    attempt = 0 # keep track of tries and give up exit script after 10
    uri = '/mgmt/cm/device/licensing/pool/regkey/licenses/'
    url_list = ['https://', address, uri, regkey_pool_uuid, '/offerings/', new_regkey]
    url = ''.join(url_list)
    while "eulaText" not in poll_result.keys():
        try:
            poll_result = get(url, auth_token, debug, return_encoding='json')
            print('\npoll {} for {}'.format(attempt +1, new_regkey))
            if "fail" in poll_result['message']:
                sys.exit(poll_result['message'])
            print(poll_result['status'])
            print(poll_result['message'])
            time.sleep(5)
        except:
            print('Poll for eula failed for regkey {}'.format(new_regkey))
            raise
        attempt += 1
        if attempt == 5:
            sys.exit('Giving up after 5 tries to poll for EULA for RegKey')
    print('Finished polling...')

    # since we have eula back we need to patch back the eula
    # update "status" in dict
    poll_result["status"] = "ACTIVATING_AUTOMATIC_EULA_ACCEPTED"
    uri = '/mgmt/cm/device/licensing/pool/regkey/licenses/'
    url_list = ['https://', address, uri, regkey_pool_uuid, '/offerings/', new_regkey]
    url = ''.join(url_list)
    patch_dict = {"status":poll_result['status'], "eulaText": poll_result['eulaText']}
    patch_payload = json.dumps(patch_dict)
    print('sending PATCH to accept EULA for {}'.format(new_regkey))
    try:
        patch_result = patch(url, auth_token, patch_payload, debug)
        print('{} for {}'.format(patch_result['message'], new_regkey))
        print(patch_result.get('status', 'ERROR: Status Not found in path_result'))
    except:
        raise


def modify_offering_addon(address, auth_token, regkey_pool_uuid, new_regkey, add_on_keys, debug):
    """
    :type regkey_pool_uuid: str
    :type new_regkey: str
    :type add_on_keys: str comma sep keys

    """

    uri = '/mgmt/cm/device/licensing/pool/regkey/licenses/'
    url_list = ['https://', address, uri, regkey_pool_uuid, '/offerings/', new_regkey]
    url = ''.join(url_list)
    patch_dict = {"status": "ACTIVATING_AUTOMATIC", "addOnKeys": add_on_keys.split(',')}
    payload = json.dumps(patch_dict)

    try:
        patch(url, auth_token, payload, debug)
        print('\nAdding {} addons for offering {} to License server status:'.format(
            add_on_keys.split(','), new_regkey))
    except:
        print('Post to License server failed')
        raise

    # poll for "eulaText"
    poll_result = {}
    attempt = 0 # keep track of tries and give up exit script after 10
    uri = '/mgmt/cm/device/licensing/pool/regkey/licenses/'
    url_list = ['https://', address, uri, regkey_pool_uuid, '/offerings/', new_regkey]
    url = ''.join(url_list)
    while not poll_result.get('status'):
        try:
            poll_result = get(url, auth_token, debug, return_encoding='json')
            print('\npoll {} for {}, Addons: {}'.format(
                attempt +1, new_regkey, add_on_keys.split(',')))
            if "fail" in poll_result['message']:
                sys.exit(poll_result['message'])
            print(poll_result['status'])
            print(poll_result['message'])
            time.sleep(5)
        except:
            print('Poll for eula failed for regkey {}'.format(new_regkey))
            raise
        attempt += 1
        if attempt == 5:
            sys.exit('Giving up after 5 tries to poll for EULA for RegKey')
    print('Reactivation complete')
    print(poll_result.get('status'))
    print('Finished polling...')



if __name__ == "__main__":

    SCRIPT_NAME = sys.argv[0]

    # suppress ssl warning when disbling ssl verification with verify=False
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    OPT = cmd_args()

    # This is the auth token that will be used in request(5 min timeout)
    TOKEN = get_auth_token(OPT.address,
                           OPT.username,
                           OPT.password,
                           uri='/mgmt/shared/authn/login')

    # STATIC GLOBALS
    ADDRESS = OPT.address
    DEBUG = OPT.debug


    # -l
    if OPT.list_pools:
        REG_POOLS = ls_pools(ADDRESS, TOKEN)
        for pool in REG_POOLS:
            print('{:38} {}'.format(pool['id'], pool['name']))
        print('\n')

    # -o, if -v included will also show moodules
    if OPT.pool_uuid:
        REG_KEY_POOL_UUID = OPT.pool_uuid
        POOL_OFFERINGS = list_offereings(ADDRESS, TOKEN, REG_KEY_POOL_UUID)
        print('{0:35}  {1:20} {2:10}'.format('RegKey', 'Status', 'addOnKeys'))
        print(73 * '-')
        for offering in  POOL_OFFERINGS:
            if 'addOnKeys' in offering:
                print('{0:35}  {1:20} {2:10}'.format(offering['regKey'], offering['status'], 'YES'))
                # if verbose given list Active modules
                if OPT.verbose:
                    active_modules = offering.get('licenseText', 'Not available').splitlines()
                    for line in active_modules:
                        if line.startswith('active module'):
                            print('   {} '.format(line[:80]))
            else:
                # -v not given list without active module info
                print('{0:35}  {1:20} {2:10}'.format(offering['regKey'],
                                                     offering['status'],
                                                     offering.get('addOnKeys')))


    # -i install new offereing with or without an addon keys, requires -r
    if OPT.install_pool_uuid:
        INSTALL_POOL = OPT.install_pool_uuid
        NEW_REGKEY = OPT.reg_key
        ADD_ON_KEY_LIST = OPT.add_on_key_list
        install_offering(ADDRESS, TOKEN, INSTALL_POOL, NEW_REGKEY, ADD_ON_KEY_LIST, DEBUG)

    # -m requires -r -A
    if OPT.modify_pool_uuid:
        MODIFY_POOL = OPT.modify_pool_uuid
        OFFERING = OPT.reg_key
        ADD_ON_KEY_LIST = OPT.add_on_key_list
        modify_offering_addon(ADDRESS, TOKEN, MODIFY_POOL, OFFERING, ADD_ON_KEY_LIST, DEBUG)

    print('SCRIPT END')
