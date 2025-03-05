////////////////////////////////////////////////////////////////////////////////
//
// Supabase Lab
//
// backend.py - Supabase-oriented functions
//
// Copyright (c) 2024, 2025 Andy Warmack
// This file is part of Supabase Lab, licensed under the MIT License.
// See the LICENSE file in the project root for more information.
////////////////////////////////////////////////////////////////////////////////

const axios = require('axios');

const { createClient } = require('@supabase/supabase-js');

const core = require('./core');

////////////////////////////////////////////////////////////////////////////////
// connect to Supabase
////////////////////////////////////////////////////////////////////////////////

const connect = async () => {
  // initialize the Supabase client
  let url = core.Session.url;
  let api_key = null;
  if ('url' in core.Session.config) {
    url = core.Session.config['url'];
  }
  if ('api_key' in core.Session.config) {
    api_key = core.Session.config['api_key'];
  }
  core.writeln(`Connecting to ${url}`);
  if (api_key == null) {
    core.supabase_error_print('No api_key configuration found.');
    return;
  }
  core.Session.config['url'] = url;
  core.Session.config['api_key'] = api_key;
  try {
    core.Session.supabase = createClient(url, api_key);
    core.writeln('Ready to login.');
  } catch (error) {
    core.handle_error('connect', error, true);
  }
};

////////////////////////////////////////////////////////////////////////////////
// run a Supabase Edge Function
////////////////////////////////////////////////////////////////////////////////

const edge_function = async (url, payload) => {
  let headers = {
    "Authorization": `Bearer ${core.Session.jwt_token}`,
    "Content-Type": "application/json"
  };
  axios.post(url, payload, { headers: headers, timeout: 5000 })
    .then(response => {
      if (core.verbose()) {
        show_response(response);
      } else {
        core.writeln(response.data);
      }
    })
    .catch(error => {
      core.supabase_error_print(`Axios error: ${error.message}`);
      if (error.code) {
        core.supabase_error_print(`Axios error code: ${error.code}`);
      }
    });
};

////////////////////////////////////////////////////////////////////////////////
// subscribe to a channel
////////////////////////////////////////////////////////////////////////////////

async function subscribe_channel(channel_name) {
  const subscription = core.Session.supabase.channel(channel_name);
  subscription
    .subscribe((status) => {
      if (status === 'SUBSCRIBED') {
        core.writeln(`Subscribed channel: ${channel_name}`);
      } else if (status === 'CLOSED') {
        core.writeln(`Closed channel: ${channel_name}`);
      } else if (status === 'RECONNECTING') {
        core.writeln(`Reconnecting to channel: ${channel_name}`);
      } else if (status === 'ERROR') {
        core.supabase_error_print(`Error subscribing to channel: ${channel_name}`);
      }
    });
  register_channel(channel_name, subscription);
  return subscription;
}

////////////////////////////////////////////////////////////////////////////////
// unsubscribe from a channel
////////////////////////////////////////////////////////////////////////////////

async function unsubscribe_channel(channel_name) {
  const subscription = core.Session.subscriptions[channel_name];
  if (subscription) {
    const { error: unsubscribeError } = await subscription.unsubscribe();
    if (unsubscribeError) {
      core.supabase_error_print(unsubscribeError);
    } else {
      delete core.Session.subscriptions[channel_name];
    }
  }
}

////////////////////////////////////////////////////////////////////////////////
// register a channel for later reference
////////////////////////////////////////////////////////////////////////////////

function register_channel(channel_name, subscription) {
  if (subscription) {
    core.Session.subscriptions[channel_name] = subscription;
  } else {
    core.supabase_error_print(`${channel_name}: Invalid subscription object.`);
  }
}

////////////////////////////////////////////////////////////////////////////////
// list registered channels
////////////////////////////////////////////////////////////////////////////////

async function list_channels() {
  for (let channel_name in core.Session.subscriptions) {
    core.writeln(channel_name);
  }
}

////////////////////////////////////////////////////////////////////////////////
// listen for broadcast messages on a channel
////////////////////////////////////////////////////////////////////////////////

async function listen_to_broadcast_channel(channel_name, event) {
  const subscription = await subscribe_channel(channel_name);
  subscription
    .on('broadcast', { event: event }, (payload) => {
      core.writeln(`FROM ${channel_name}: ${JSON.stringify(payload)}`);
    });
}

////////////////////////////////////////////////////////////////////////////////
// send broadcast message on a channel
////////////////////////////////////////////////////////////////////////////////

async function send_to_broadcast_channel(channel_name, event, message_text) {
  if (message_text == '' || !message_text) {
    core.error_print('Empty message not sent.');
    return;
  }
  const message = {
    type: 'broadcast',
    event: event,
    payload: {
      message: message_text,
    }
  };
  core.Session.supabase.channel(channel_name).send(message);
  core.writeln(`TO ${channel_name}: ${JSON.stringify(message)}`);
}

////////////////////////////////////////////////////////////////////////////////
// listen for presence signals on a channel
////////////////////////////////////////////////////////////////////////////////

async function sync_track_presence(channel_name) {
  let channel = core.Session.subscriptions[channel_name];
  if (!channel) {
    channel = await subscribe_channel(channel_name);
  }
  channel
    .on('presence', { event: 'sync' }, () => {
      const newState = channel.presenceState();
      core.writeln(`sync ${JSON.stringify(newState, null, 2)}`);
    })
    .on('presence', { event: 'join' }, ({ key, newPresences }) => {
      core.writeln(`join ${key} ${JSON.stringify(newPresences, null, 2)}`);
    })
    .on('presence', { event: 'leave' }, ({ key, leftPresences }) => {
      core.writeln(`leave ${key} ${JSON.stringify(leftPresences, null, 2)}`);
    });
}

////////////////////////////////////////////////////////////////////////////////
// send presence state on a channel
////////////////////////////////////////////////////////////////////////////////

async function send_presence(channel_name) {
  let channel = core.Session.subscriptions[channel_name];
  if (!channel) {
    channel = await subscribe_channel(channel_name);
  }
  const userStatus = {
    user: core.Session.config['email'],
    online_at: new Date().toISOString(),
  };
  const presenceTrackStatus = await channel.track(userStatus);
  core.writeln(JSON.stringify(presenceTrackStatus, null, 2));
}

////////////////////////////////////////////////////////////////////////////////
// stop presence tracking on a channel
////////////////////////////////////////////////////////////////////////////////

async function stop_presence(channel_name) {
  const channel = core.Session.subscriptions[channel_name];
  if (channel) {
    channel.untrack();
  }
}

////////////////////////////////////////////////////////////////////////////////
// listen for database table changes
////////////////////////////////////////////////////////////////////////////////

const listen_to_table = async (table_name) => {
  core.Session.supabase
    .channel('table_changes')
    .on(
      'postgres_changes',
      { event: '*', schema: 'public', table: table_name },
      (payload) => {
        core.writeln(payload);
      }
    )
    .subscribe();
  core.writeln(`Listening for changes on table: ${table_name}`);
};

////////////////////////////////////////////////////////////////////////////////
// display response values after sending a request to Supabase
////////////////////////////////////////////////////////////////////////////////

function show_response(response) {
  core.writeln(`Response URL: ${response.config.url}`);
  core.writeln(`Status Code: ${response.status}`);
  core.writeln(`Status Text: ${response.statusText}`);
  core.writeln(`Request Method: ${response.request.method}`);
  core.writeln('Response Data:');
  for (let key in response.data) {
    core.writeln(`   ${key}: ${response.data[key]}`);
  }  
  core.writeln('Response Headers:');
  for (let key in response.headers) {
    core.writeln(`   ${key}: ${response.headers[key]}`);
  }  
}

////////////////////////////////////////////////////////////////////////////////
// sign in the user using email/password authentication
////////////////////////////////////////////////////////////////////////////////

const sign_in = async (email, password) => {
  if (email == '' || password == '') {
    core.writeln('Invalid email or password.');
    return;
  }
  core.writeln('Logging in...');

  try {
    const { data, error } = await core.Session.supabase.auth.signInWithPassword({ email: email, password: password });
    if (error) {
      core.supabase_error_print(`Login failed: ${error.message}`);
    } else {
      core.Session.jwt_token = data.session.access_token;
      let session_user_email = data.session.user.email;
      let last_sign_in_at = core.show_time(data.user.last_sign_in_at);
      core.Session.authenticated = true;
      core.update_prompt();
      core.writeln(`${session_user_email} logged in.`);
      core.writeln(`Last login: ${last_sign_in_at}`);
    }
  } catch (error) {
    if (error instanceof TypeError) {
      core.supabase_error_print(error.message);
    } else {
      core.supabase_error_print('Unexpected error:', error);
    }
  }
};

////////////////////////////////////////////////////////////////////////////////
// sign out
////////////////////////////////////////////////////////////////////////////////

const sign_out = async () => {
  core.writeln('Logging out.');
  core.Session.supabase.auth.signOut();
  core.Session.jwt_token = null;
  core.Session.authenticated = false;
};

module.exports.connect = connect;
module.exports.edge_function = edge_function;
module.exports.subscribe_channel = subscribe_channel;
module.exports.unsubscribe_channel = unsubscribe_channel;
module.exports.register_channel = register_channel;
module.exports.list_channels = list_channels;
module.exports.listen_to_broadcast_channel = listen_to_broadcast_channel;
module.exports.send_to_broadcast_channel = send_to_broadcast_channel;
module.exports.sync_track_presence = sync_track_presence;
module.exports.send_presence = send_presence;
module.exports.stop_presence = stop_presence;
module.exports.listen_to_table = listen_to_table;
module.exports.sign_in = sign_in;
module.exports.sign_out = sign_out;
