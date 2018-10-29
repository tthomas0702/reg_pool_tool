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

class RegPool:
    """work with regkey pools"""
    def __init__(self, bigiq_address, username, password):
        self.address = bigiq_address
        self.user = username
        self.password = password
        self.token = get_auth_token(self.address, self.user, self.password,
                                    uri='/mgmt/shared/authn/login')
        
    def list_pool():
        pass



if __name__ == "__main__":

    SCRIPT_NAME = sys.argv[0]

    # suppress ssl warning when disbling ssl verification with verify=False
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    OPT = cmd_args()


    # STATIC GLOBALS
    ADDRESS = OPT.address
    DEBUG = OPT.debug


    # -l
    if OPT.list_pools:
        pass


    # -o, if -v included will also show moodules
    if OPT.pool_uuid:
        pass

    # -i install new offereing with or without an addon keys, requires -r
    if OPT.install_pool_uuid:
        pass

    # -m requires -r -A
    if OPT.modify_pool_uuid:
        pass


    RUN = RegPool(OPT.address,OPT.username,OPT.password)


#TODO Next add list_pool to class
