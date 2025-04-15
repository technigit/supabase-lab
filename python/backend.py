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

import asyncio
import json
from datetime import datetime, timezone
try:
    from realtime._async.client import AsyncRealtimeClient
    from realtime.types import RealtimeSubscribeStates
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
from typing import Optional

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
        core.supabase_error_print('No api_key configuration found.')
        return
    core.Session.config['url'] = url
    core.Session.config['api_key'] = api_key
    try:
        core.Session.supabase = await acreate_client(url, api_key)
        core.Session.realtime = AsyncRealtimeClient(websocket_url(), api_key)
        print('Ready to login.')
    except Exception as e: # pylint: disable=broad-exception-caught
        core.handle_error('connect()', e)

def websocket_url():
    return core.Session.config['url'].replace('http://', 'wss://').replace('https://', 'wss://') + '/realtime/v1'

def check_connection():
    if core.Session.supabase:
        return True
    core.supabase_error_print('Supabase client not connected.')
    return False

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
# display subscribe state messages
################################################################################

def on_subscribe_for_channel(channel_name, for_table = False):
    def on_subscribe(status: RealtimeSubscribeStates, error: Optional[Exception]):
        if status == RealtimeSubscribeStates.SUBSCRIBED:
            if not for_table:
                print(f"Subscribed channel: {channel_name}")
            else:
                print(f"Listening for changes on table: {channel_name}")
        elif status == RealtimeSubscribeStates.CLOSED:
            print(f"Closed channel: {channel_name}")
        elif status == RealtimeSubscribeStates.TIMED_OUT:
            core.supabase_error_print('Channel connection timed out')
        elif status == RealtimeSubscribeStates.CHANNEL_ERROR:
            core.supabase_error_print(f"Error subscribing to channel: {error.message}")

    return on_subscribe

################################################################################
# subscribe to a channel
################################################################################

async def subscribe_channel(channel_name, event = 'test', force = True):
    if not check_connection():
        return False
    if channel_name in core.Session.subscriptions:
        subscription = core.Session.subscriptions[channel_name]
        return subscription
    if not force:
        core.error_print(f"Please first subscribe to channel: {channel_name}")
        return False
    client = core.Session.realtime
    await client.connect()
    channel = client.channel(channel_name, { 'type': 'broadcast', 'event': event, "config": {"broadcast": {"self": True}}})
    subscription = await channel.subscribe(on_subscribe_for_channel(channel_name))
    register_channel(channel_name, subscription)
    return subscription

################################################################################
# unsubscribe from a channel
################################################################################

async def unsubscribe_channel(channel_name):
    if not check_connection():
        return
    if channel_name not in core.Session.subscriptions:
        return
    subscription = core.Session.subscriptions[channel_name]
    if subscription:
        await subscription.unsubscribe()
        del core.Session.subscriptions[channel_name]
        print(f"Closed channel: {channel_name}")

################################################################################
# register a channel for later reference
################################################################################

def register_channel(channel_name, subscription):
    if subscription:
        core.Session.subscriptions[channel_name] = subscription
    else:
        core.supabase_error_print(f"{channel_name}: Invalid subscription object.")

################################################################################
# list registered channels
################################################################################

async def list_channels():
    for channel_name in core.Session.subscriptions:
        print(channel_name)

################################################################################
# listen for broadcast messages on a channel
################################################################################

async def listen_to_broadcast_channel(channel_name, event):
    if not check_connection():
        return
    if channel_name == '':
        core.error_print('Please specify a channel.')
        return

    await core.Session.realtime.connect()
    subscription = await subscribe_channel(channel_name)
    subscription.on_broadcast(event, lambda payload: print(f"FROM {channel_name}: {payload}"))

################################################################################
# send broadcast message on a channel
################################################################################

async def send_to_broadcast_channel(channel_name, event, payload):
    if not check_connection():
        return
    await core.Session.realtime.connect()
    subscription = await subscribe_channel(channel_name, event, False)
    if subscription is not False:
        await subscription.send_broadcast(event, payload)
        print(f"TO {channel_name}: {payload}")

################################################################################
# listen for presence signals on a channel
################################################################################

async def sync_track_presence(channel_name):
    channel = core.Session.supabase.channel(channel_name)
    register_channel(channel_name, channel)

    def on_sync():
        new_state = channel.presence_state()
        print(f"sync {json.dumps(new_state, indent=2)}")

    def on_join(key, _, new_presences):
        print(f"join {key} {json.dumps(new_presences, indent=2)}")

    def on_leave(key, _, left_presences):
        print(f"leave {key} {json.dumps(left_presences, indent=2)}")

    await channel.on_presence_sync(on_sync).on_presence_join(on_join).on_presence_leave(on_leave).subscribe()

################################################################################
# send presence state on a channel
################################################################################

async def send_presence(channel_name):
    channel = await subscribe_channel(channel_name)
    await asyncio.sleep(0.1)
    user_status = {
        "user": core.Session.config['email'],
        "online_at": datetime.now(timezone.utc).isoformat()
    }
    presence_track_status = await channel.track(user_status)
    print(f"{'ok' if presence_track_status is None else presence_track_status}")

################################################################################
# stop presence tracking on a channel
################################################################################

async def stop_presence(channel_name):
    subscription = await subscribe_channel(channel_name)
    await subscription.untrack()

################################################################################
# listen for database table changes
################################################################################

async def listen_to_table(table_name):
    client = core.Session.realtime
    await client.connect()
    channel = client.channel('table_changes', {
        'type': 'postgres_changes',
        'table': table_name,
        'event': '*'
    })
    channel.on_postgres_changes(
        "*",
        schema="public",
        callback=print
    )
    await channel.subscribe(on_subscribe_for_channel(table_name, True))
    await client.listen()

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
            core.supabase_error_print(response)
        else:
            core.supabase_error_print('No response received.')
        core.supabase_error_print(f"sign_in({email}, {'*' * min(len(password), 8)}): {e}")
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
    core.Session.jwt_token = None
    core.Session.authenticated = False
