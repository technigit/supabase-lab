#!/usr/bin/env python3

################################################################################
#
# Supabase Lab
#
# dev.py - Experimental development
#
# Copyright (c) 2024, 2025 Andy Warmack
# This file is part of Supabase Lab, licensed under the MIT License.
# See the LICENSE file in the project root for more information.
################################################################################

import ast
import re

import backend
import core

# non-printable null character for internal parsing
SPACE_DELIM = '\x00'

################################################################################
# explore supabase object for development purposes
################################################################################

def explore(args = None):
    if core.Session.authenticated:
        try:
            data = core.Session.supabase.auth.get_session().model_dump()
            found = True
            if args is not None:
                found = False
                for arg in args.split():
                    if isinstance(data, dict) and arg in data:
                        data = data[arg]
                        found = True
                    elif isinstance(data, list) and int(arg) < len(data):
                        data = data[int(arg)]
                        found = True
            if found:
                if isinstance(data, dict):
                    for key in data:
                        if isinstance(data[key], dict) or isinstance(data[key], list):
                            print(f"{key}:")
                            core.print_item(data[key], '   ')
                        else:
                            print(f"{key}: {data[key]}")
                elif isinstance(data, list):
                    for i, item in enumerate(data):
                        print(f"{i}:")
                        core.print_item(item, '   ')
                else:
                    core.print_item(data)
            else:
                core.print_item(data)
        except Exception as e: # pylint: disable=broad-exception-caught
            core.handle_error('explore()', e)
    else:
        print('login?')

################################################################################
# parse dev command-line statement
################################################################################

def edge(args = None):
    pa = parse_args(args)
    endpoint = pa[0]
    payload_str = pa[1].replace(SPACE_DELIM, ' ')
    try:
        payload = ast.literal_eval(payload_str)
    except: # pylint: disable=bare-except
        payload = {}
    backend.edge_function(core.Session.config['url'] + f"/functions/v1/{endpoint}", payload)

def ping(args = None):
    print(f"ping {args}")

def dev(args = None):
    if args is None:
        print('dev?')
        print('   explore [args]')
        print('   ping [args]')
        return
    experiment = None
    m = re.match(r'(\S*)(.*)$', args)
    if m is not None:
        experiment = m.group(1)
        args = m.group(2)
    if experiment == 'explore':
        explore(args)
    elif experiment == 'edge':
        edge(args)
    elif experiment == 'ping':
        ping(args)
    else:
        print(f"{experiment}?")

def parse_args(args = None):
    if args is None:
        return None
    return args.split()

################################################################################
# debug function to inspect important values
################################################################################

def debug(args = ''):
    if args is None:
        args = ''
    filter_list = args.split()
    no_filters = len(filter_list) == 0
    if 'url' in filter_list or no_filters:
        print(f"url = {core.Session.url}")
    if 'api_key' in filter_list or no_filters:
        print(f"api_key = {core.Session.config['api_key'] if 'api_key' in core.Session.config else None}")
    if 'email' in filter_list or no_filters:
        print(f"email = {core.Session.config['email'] if 'email' in core.Session.config else None}")
    if 'jwt_token' in filter_list or 'jwt' in filter_list or no_filters:
        print(f"jwt_token = {core.Session.jwt_token}")
    if 'running' in filter_list or no_filters:
        print(f"running = {core.Main.running}")
    if 'authenticated' in filter_list or no_filters:
        print(f"authenticated = {core.Session.authenticated}")
    if 'config' in filter_list or no_filters:
        print('config:')
        core.print_item(core.Session.config, '   ')
