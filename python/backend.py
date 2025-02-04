#!/usr/bin/env python3

################################################################################
#
# Supabase Lab
#
# backend.py - Supabase-oriented functions
#
# Copyright (c) 2024, 2025 Andy Warmack
# This file is part of Supabase Lab, licensed under the MIT License.
# See the LICENSE file in the project root for more information.
################################################################################

try:
    from realtime._async.client import AsyncRealtimeClient
    REALTIME_IMPORTED = True
except ImportError:
    REALTIME_IMPORTED = False
try:
    import requests
    REQUESTS_IMPORTED = True
except ImportError:
    REQUESTS_IMPORTED = False
try:
    from supabase import acreate_client
    SUPABASE_IMPORTED = True
except ImportError:
    SUPABASE_IMPORTED = False

import core

################################################################################
# check for required imports
################################################################################

def realtime_imported():
    return REALTIME_IMPORTED

def requests_imported():
    return REQUESTS_IMPORTED

def supabase_imported():
    return SUPABASE_IMPORTED

################################################################################
# connect to Supabase
################################################################################

async def connect():
    # initialize the Supabase client
    url = core.Session.url
    api_key = None
    if 'url' in core.Session.config:
        url = core.Session.config['url']
    if 'api_key' in core.Session.config:
        api_key = core.Session.config['api_key']
    print(f"Connecting to {url}")
    if api_key is None:
        core.error_print('No api_key configuration found.')
        return
    core.Session.config['url'] = url
    core.Session.config['api_key'] = api_key
    try:
        core.Session.supabase = await acreate_client(url, api_key)
        core.Session.realtime = AsyncRealtimeClient(url, api_key)
        print('Ready to login.')
    except Exception as e: # pylint: disable=broad-exception-caught
        core.handle_error('connect()', e)

################################################################################
# run a Supabase Edge Function
################################################################################

def edge_function(url, payload):
    if not requests_imported():
        core.info_print('The Requests library is required: https://requests.readthedocs.io/')
        return
    headers = {
        "Authorization": f"Bearer {core.Session.jwt_token}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        if core.verbose() or not response.ok:
            show_response(response)
        elif 'application/json' in response.headers.get('Content-Type', ''):
            print(response.json())
        else:
            print(response.headers.get('Content-Type', ''))
            print(response.text)
    except requests.exceptions.HTTPError as e:
        core.handle_error('edge_function()', e)
    except requests.exceptions.RequestException as e:
        core.handle_error('edge_function()', e)
    except Exception as e: # pylint: disable=broad-exception-caught
        core.handle_error('edge_function()', e, True)

################################################################################
# display response values after sending a request to Supabase
################################################################################

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

################################################################################
# sign in the user using email/password authentication
################################################################################

async def sign_in(email, password):
    if email == '' or password == '':
        print('Invalid email or password.')
        return
    print('Logging in...')
    response = None
    try:
        response = await core.Session.supabase.auth.sign_in_with_password({"email": email, "password": password})
    except Exception as e: # pylint: disable=broad-exception-caught
        if response is not None:
            print(response)
        else:
            print('No response received.')
        print(f"sign_in({email}, {'*' * min(len(password), 8)}):", e)
        core.Session.authenticated = False

    # get JWT token and greet user
    if response is not None:
        core.Session.jwt_token = response.session.access_token
        email = response.session.user.email
        last_sign_in_at = core.show_time(response.user.last_sign_in_at)
        print(f"{email} logged in.")
        print(f"Last login: {last_sign_in_at}")
        core.Session.authenticated = True

################################################################################
# sign out
################################################################################

async def sign_out():
    print('Logging out.')
    await core.Session.supabase.auth.sign_out({'scope': 'local'})
    core.Session.authenticated = False
