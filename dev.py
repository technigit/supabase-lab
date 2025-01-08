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

import core

################################################################################
# explore supabase object for development purposes
################################################################################

def explore(args = None):
    if core.Main.session_active:
        try:
            data = core.Main.supabase.auth.get_session().model_dump()
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
    payload_str = pa[1].replace('\x00', ' ')
    try:
        payload = ast.literal_eval(payload_str)
    except: # pylint: disable=bare-except
        payload = {}
    core.edge_function(core.Main.config['url'] + f"/functions/v1/{endpoint}", payload)

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
