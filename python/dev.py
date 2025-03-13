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
import asyncio
import re
import threading

import backend
import core

# non-printable null character for internal parsing
SPACE_DELIM = '\x00'

# time suffix translation into multipliers
TIME_SUFFIX_DICT = {'': 1, 's': 1, 'm': 60, 'h': 60 * 60}

################################################################################
# explore supabase object for development purposes
################################################################################

async def explore(args = None):
    if core.Session.authenticated:
        try:
            gs = await core.Session.supabase.auth.get_session()
            data = gs.model_dump()
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

# edge
def edge(args = None):
    pa = parse_args(args)
    endpoint = pa[0]
    payload_str = pa[1].replace(SPACE_DELIM, ' ')
    try:
        payload = ast.literal_eval(payload_str)
    except: # pylint: disable=bare-except
        payload = {}
    backend.edge_function(core.Session.config['url'] + f"/functions/v1/{endpoint}", payload)

# ping
def ping(args = None):
    print(f"ping {args}")

# subscribe to channel
async def sub(args):
    channel_name = args.strip()
    await backend.subscribe_channel(channel_name)

# unsubscribe from channel
async def unsub(args):
    channel_name = args.strip()
    await backend.unsubscribe_channel(channel_name)

# list channels
async def lschan():
    await backend.list_channels()

# listen to broadcast channel
async def lchan(args):
    arg_strings = parse_args(args)
    channel_name = arg_strings[0]
    event = arg_strings[1] if len(arg_strings) > 1 else 'test'
    await backend.listen_to_broadcast_channel(channel_name, event)

# send to broadcast channel
async def schan(args):
    arg_strings = parse_args(args)
    channel_name = arg_strings[0]
    event = arg_strings[1] if len(arg_strings) > 2 else 'test'
    message = arg_strings[-1]
    await backend.send_to_broadcast_channel(channel_name, event, message)

# listen to table
async def ldb(args):
    await backend.listen_to_table(args.strip())

# beep
def beeping(beep_id, status = None):
    if beep_id is not None and status is not None:
        core.Session.config['beeping'][beep_id] = status
    elif beep_id is None:
        for key in core.Session.config['beeping']:
            core.Session.config['beeping'][key] = False
    else:
        status = core.Session.config['beeping'][beep_id]
    return status

def get_beep_id():
    if 'beeping' not in core.Session.config:
        core.Session.config['beeping'] = {}
    beep_id = 0
    while True:
        if beep_id not in core.Session.config['beeping']:
            break
        beep_id += 1
    return beep_id

def del_beep_id(beep_id):
    if beep_id in core.Session.config['beeping']:
        del core.Session.config['beeping'][beep_id]

async def run_beep(beep_id, beep_message, beep_interval):
    beep_seq = 1
    try:
        while beeping(beep_id):
            print(f"{beep_id}: beep_seq={beep_seq} {beep_message}")
            beep_seq += 1
            core.Session.prompt_app.invalidate()
            await asyncio.sleep(beep_interval)
    except asyncio.CancelledError:
        pass

async def beep(args = None):
    # check for beep stop
    args = args.strip()
    m = re.match(r'^stop (\d*)$', args)
    if m is not None:
        beep_id = int(m.group(1))
        beeping(beep_id, False)
        return
    if args == 'stop':
        beeping(None)
        return

    # get beep parameters
    beep_id = get_beep_id()
    beeping(beep_id, True)
    beep_interval = '1'
    beep_duration = '10'
    beep_message = 'beep'
    float_regex = r'(\d+(\.\d+)?|\.\d+)' # match an int string or a float string
    time_suffix_regex = r'[smhSMH]?'
    m = re.match(rf'^({float_regex}{time_suffix_regex})\s+({float_regex}{time_suffix_regex})\s+(\S.*)$', args)
    if m is not None:
        beep_interval = m.group(1)
        beep_duration = m.group(4)
        beep_message = m.group(7)
    else:
        m = re.match(rf'^({float_regex}{time_suffix_regex})\s+({float_regex}{time_suffix_regex})$', args)
        if m is not None:
            beep_interval = m.group(1)
            beep_duration = m.group(4)
        else:
            m = re.match(rf'^({float_regex}{time_suffix_regex})\s+([^\d\s].*)$', args)
            if m is not None:
                beep_interval = m.group(1)
                beep_message = m.group(7)
            else:
                m = re.match(rf'^({float_regex}{time_suffix_regex})$', args)
                if m is not None:
                    beep_interval = m.group(1)

    # parse beep time suffixes
    m = re.match(rf'^(\d*)({time_suffix_regex})$', beep_interval)
    if m is not None:
        time_suffix = m.group(2)
        beep_interval = float(m.group(1)) * TIME_SUFFIX_DICT[time_suffix]
    m = re.match(rf'^(\d*)({time_suffix_regex})$', beep_duration)
    if m is not None:
        time_suffix = m.group(2)
        beep_duration = float(m.group(1)) * TIME_SUFFIX_DICT[time_suffix]

    # start beeping
    beep_task = asyncio.create_task(run_beep(beep_id, beep_message, beep_interval))

    # sleep while beeping
    try:
        if beeping(beep_id):
            await asyncio.sleep(beep_duration)
    finally:
        beep_task.cancel()
        beeping(beep_id, False)
        await beep_task
        del_beep_id(beep_id)

# dev
async def dev(args = None):
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
        await explore(args)
    elif experiment == 'beep':
        asyncio.create_task(beep(args))
    elif experiment == 'edge':
        edge(args)
    elif experiment == 'subscribe' or experiment == 'sub':
        asyncio.create_task(sub(args))
    elif experiment == 'unsubscribe' or experiment == 'unsub':
        asyncio.create_task(unsub(args))
    elif experiment == 'listchannels' or experiment == 'lschan':
        asyncio.create_task(lschan())
    elif experiment == 'listenchan' or experiment == 'lchan':
        asyncio.create_task(lchan(args))
    elif experiment == 'sendchan' or experiment == 'schan':
        asyncio.create_task(schan(args))
    elif experiment == 'listendb' or experiment == 'ldb':
        asyncio.create_task(ldb(args))
    elif experiment == 'ping':
        ping(args)
    else:
        print(f"{experiment}?")

# parse_args
def parse_args(args):
    if args == '':
        return ['']
    regex = r'(?:([^\s\'"]+)|"([^"]*)"|\'([^\']*)\')+' # group quoted terms
    matches = re.findall(regex, args)
    return [match[0] or match[1] or match[2] for match in matches]

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
    if 'tasks' in filter_list:
        list_tasks()
    if 'threads' in filter_list:
        list_threads()

def list_tasks():
    print('\nTasks:')
    for task in asyncio.all_tasks():
        print(f"   {task}")

def list_threads():
    print('\nThreads:')
    for thread in threading.enumerate():
        print(f"   {thread.name}")
