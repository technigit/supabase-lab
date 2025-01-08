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

import os
import traceback
from datetime import datetime

################################################################################
# all primary environment values and functions are accessed here
################################################################################

class Main():
    # get base working directory
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # general settings
    auth_prompt = '> '      # authentication prompt before logging in
    running = True          # accepting auth/session input
    verbose = False         # extra output for debugging
    version = ''            # version set from lab.py

################################################################################
# all session values are accessed here
################################################################################

class Session():
    # default url
    url = "http://127.0.0.1:54321"

    # user credentials
    jwt_token = None

    # session settings
    authenticated = False   # authentication status
    config = {}             # configuration values
    config_dir = 'config'   # default config directory
    prompt = '>> '          # session prompt after logging in
    supabase = None         # Supabase connection object

################################################################################
# output functions
################################################################################

def show_info():
    should_show = True
    if 'suppress_header' in Session.config and Session.config['suppress_header']:
        should_show = False
    if should_show:
        print(f"""
Supabase Lab
{Main.version}
""")

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
    if 'verbose' in Session.config:
        local_verbose = Session.config['verbose']
    return local_verbose
