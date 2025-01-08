#!/usr/bin/env python3

################################################################################
#
# Supabase Lab
#
# core.py - Core variables and functions
#
# Copyright (c) 2024, 2025 Andy Warmack
# This file is part of Supabase Lab, licensed under the MIT License.
# See the LICENSE file in the project root for more information.
################################################################################

import fileinput
import os
import re
try:
    import requests
    REQUESTS_IMPORTED = True
except ImportError:
    REQUESTS_IMPORTED = False
import traceback
from datetime import datetime
try:
    from supabase import create_client
    SUPABASE_IMPORTED = True
except ImportError:
    SUPABASE_IMPORTED = False

################################################################################
# all primary environment values and functions are accessed here
################################################################################

class Main():
    # default url
    url = "http://127.0.0.1:54321"

    # user credentials
    email = ""
    password = ""
    jwt_token = None

    # get base working directory
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # general settings
    auth_prompt = '> '      # authentication prompt before logging in
    config = {}             # configuration values
    config_dir = 'config'   # default config directory
    running = True          # accepting auth/session input
    session_prompt = '>> '  # session prompt after logging in
    session_active = False  # authenticated status
    supabase = None         # Supabase connection object
    verbose = False         # extra output for debugging
    version = ''            # version set from session.py

################################################################################
# check for required imports
################################################################################

def requests_imported():
    return REQUESTS_IMPORTED

def supabase_imported():
    return SUPABASE_IMPORTED

################################################################################
# primary connection routines
################################################################################

def connect():
    # initialize the supabase client
    url = Main.url
    api_key = None
    if 'url' in Main.config and 'api_key' in Main.config:
        url = Main.config['url']
        api_key = Main.config['api_key']
    print(f"Connecting to {url}")
    if api_key is None:
        error_print('No api_key configuration found.')
        return
    Main.config['url'] = url
    Main.config['api_key'] = api_key
    try:
        Main.supabase = create_client(url, api_key)
        print('Ready to login.')
    except Exception as e: # pylint: disable=broad-exception-caught
        handle_error('connect()', e)

def get_config(config_files):
    # read values from a config file, superceding default values
    try:
        with fileinput.FileInput(files=(f"{Main.base_dir}/{Main.config_dir}/{f}" for f in config_files), mode='r') as lines:
            for line in lines:
                line = line.strip()
                if line.startswith('#') or line == '':
                    continue
                if line != '\n':
                    m = re.match(r'^(\S*)\s*=\s*(.*)$', line)
                    if m is None:
                        m = re.match(r'^(\S*)\s*=()$', line)
                        if m is None:
                            m = re.match(r'^(\S*)\s*=(\{.*\})$', line)
                    if m is not None:
                        key = m.group(1)
                        value = m.group(2).replace(' ', '\x00')
                        if value.lower() in ['t', 'true', 'y', '1']:
                            value = True
                        elif value.lower() in ['f', 'false', 'n', '0']:
                            value = False
                        if m is not None:
                            Main.config[key] = value
                    else:
                        print(f"{line}?")
    except FileNotFoundError as e:
        handle_error('get_config()', e)
    except Exception as e: # pylint: disable=broad-exception-caught
        handle_error('get_config()', e, True)

def edge_function(url, payload):
    if not requests_imported():
        info_print('The Requests library is required: https://requests.readthedocs.io/en/latest/')
        return
    headers = {
        "Authorization": f"Bearer {Main.jwt_token}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        if verbose() or not response.ok:
            show_response(response)
        elif 'application/json' in response.headers.get('Content-Type', ''):
            print(response.json())
        else:
            print(response.headers.get('Content-Type', ''))
            print(response.text)
    except requests.exceptions.HTTPError as e:
        handle_error('edge_function()', e)
    except requests.exceptions.RequestException as e:
        handle_error('edge_function()', e)
    except Exception as e: # pylint: disable=broad-exception-caught
        handle_error('edge_function()', e, True)

################################################################################
# output functions
################################################################################

def show_info():
    should_show = True
    if 'suppress_header' in Main.config and Main.config['suppress_header']:
        should_show = False
    if should_show:
        print(f"""
Supabase Lab
{Main.version}
""")

def show_response(response):
    print(f"Response URL: {response.url}")
    print(f"Status Code: {response.status_code}")
    print(f"Response OK: {response.ok}")
    print(f"Elapsed Time: {response.elapsed.total_seconds()} seconds ({response.elapsed})")
    print(f"Content-Type: {response.headers.get('Content-Type', '')}")
    print(f"Cookies: {response.cookies.get_dict()}")
    print(f"Request Method: {response.request.method}")
    print(f"Request URL: {response.request.url}")
    print('Request Headers:')
    for header, value in response.request.headers.items():
        print(f"   {header}: {value}")
    print(f"Request Body: {response.request.body.decode('utf-8')}")
    print(f"History: {response.history}")
    print(f"Response JSON: {response.json()}")
    print(f"Response Test: {response.text}")

def show_time(date_string):
    dt_utc = datetime.fromisoformat(str(date_string))
    local_offset = datetime.now().astimezone().utcoffset()
    return dt_utc + local_offset

def info_print(message):
    print(f"<i> {message}")

def error_print(message):
    print(f"<E> {message}")

def handle_error(message, e, force_verbose = False):
    print(f"{message}: {type(e).__name__}: {str(e)}")
    if verbose() or force_verbose:
        traceback.print_exc()

def print_item(print_data, indent = ''):
    if isinstance(print_data, dict):
        for key in print_data:
            if key != 'password':
                print(f"{indent}{key}: {print_data[key]}")
            else:
                print(f"{indent}{key}: {'*' * len(print_data[key])}")
    elif isinstance(print_data, list):
        for i, item in enumerate(print_data):
            print(f"{indent}{i}: {item}")
    else:
        print(f"{indent}{print_data}")

def verbose():
    local_verbose = Main.verbose
    if 'verbose' in Main.config:
        local_verbose = Main.config['verbose']
    return local_verbose

################################################################################
# debug function to inspect important values
################################################################################

def debug(args = ''):
    if args is None:
        args = ''
    filter_list = args.split()
    no_filters = len(filter_list) == 0
    if 'url' in filter_list or no_filters:
        print(f"url = {Main.url}")
    if 'api_key' in filter_list or no_filters:
        print(f"api_key = {Main.config['api_key'] if 'api_key' in Main.config else None}")
    if 'email' in filter_list or no_filters:
        print(f"email = {Main.config['email'] if 'email' in Main.config else None}")
    if 'jwt_token' in filter_list or 'jwt' in filter_list or no_filters:
        print(f"jwt_token = {Main.jwt_token}")
    if 'running' in filter_list or no_filters:
        print(f"running = {Main.running}")
    if 'session_active' in filter_list or no_filters:
        print(f"session_active = {Main.session_active}")
    if 'config' in filter_list or no_filters:
        print('config:')
        print_item(Main.config, '   ')

################################################################################
# sign in the user using email/password authentication
################################################################################

def sign_in(email, password):
    if email == '' or password == '':
        print('Invalid email or password.')
        return
    print('Logging in...')
    response = None
    try:
        response = Main.supabase.auth.sign_in_with_password({"email": email, "password": password})
    except Exception as e: # pylint: disable=broad-exception-caught
        if response is not None:
            print(response)
        else:
            print('No response received.')
        print(f"sign_in({email}, ********):", e)
        Main.session_active = False

    # get JWT token and greet user
    if response is not None:
        Main.jwt_token = response.session.access_token
        email = Main.supabase.auth.get_user().model_dump()['user']['email']
        last_sign_in_at = show_time(Main.supabase.auth.get_user().model_dump()['user']['last_sign_in_at'])
        print(f"{email} logged in.")
        print(f"Last login: {last_sign_in_at}")
        Main.session_active = True

################################################################################
# sign out
################################################################################

def sign_out():
    print('Logging out.')
    Main.supabase.auth.sign_out({'scope': 'local'})
    Main.session_active = False

def exit_completely(cr = False):
    if cr:
        print('\r')
    if Main.session_active:
        sign_out()
    print('Bye.')
    Main.running = False
