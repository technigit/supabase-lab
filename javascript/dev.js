////////////////////////////////////////////////////////////////////////////////
//
// Supabase Lab
//
// dev.py - Experimental development
//
// Copyright (c) 2024, 2025 Andy Warmack
// This file is part of Supabase Lab, licensed under the MIT License.
// See the LICENSE file in the project root for more information.
////////////////////////////////////////////////////////////////////////////////

const core = require('./core');
const backend = require('./backend');

const SPACE_DELIM = '\x00';

////////////////////////////////////////////////////////////////////////////////
// explore supabase object for development purposes
////////////////////////////////////////////////////////////////////////////////

const explore = async () => {
  const { data, error } = await core.Session.supabase.auth.getSession();
  if (error) {
    core.handle_error('dev explore', error);
  } else {
    console.log(data);
  }
};

////////////////////////////////////////////////////////////////////////////////
// parse dev command-line statement
////////////////////////////////////////////////////////////////////////////////

// edge
const edge = async (args) => {
  var pa = parse_args(args);
  var endpoint = pa[1];
  var payload_str = pa[2].replace(SPACE_DELIM, ' ');
  try {
    var payload = JSON.parse(payload_str);
  } catch {
    payload = {};
  }
  let url = `${core.Session.config['url']}/functions/v1/${endpoint}`;
  await backend.edge_function(url, payload);
};

// ping
const ping = async (args) => {
  console.log(`ping ${args}`);
};

// dev
const dev = async (args) => {
  if (args == '') {
    console.log('dev?');
    console.log('   explore [args]');
    console.log('   ping [args]');
    return;
  }
  var experiment = '';
  const m = args.match(/(\S*)(.*)$/);
  if (m) {
    experiment = m[1];
    args = m[2];
  }
  if (experiment == 'explore') {
    await explore(args);
  } else if (experiment == 'edge') {
    await edge(args);
  } else if (experiment == 'ping') {
    await ping(args);
  } else {
    console.log(`${experiment}?`);
  }
};

// parse_args
function parse_args(args) {
  if (args == '') {
    return '';
  }
  return args.split(' ');
}

////////////////////////////////////////////////////////////////////////////////
// debug function to inspect important values
////////////////////////////////////////////////////////////////////////////////

function debug(args) {
  if (args == null) {
    args = '';
  }
  var filter_list = args.trim() ? args.split(' ') : [];
  var no_filters = filter_list.length == 0;
  if (filter_list.includes('url') || no_filters) {
    console.log(`url = ${core.Session.url}`);
  }
  if (filter_list.includes('api_key') || no_filters) {
    console.log(`api_key = ${'api_key' in core.Session.config ? core.Session.config['api_key'] : null}`);
  }
  if (filter_list.includes('email') || no_filters) {
    console.log(`email = ${'email' in core.Session.config ? core.Session.config['email'] : null}`);
  }
  if (filter_list.includes('jwt_token') || filter_list.includes('jwt') || no_filters) {
    console.log(`jwt_token = ${core.Session.jwt_token}`);
  }
  if (filter_list.includes('running') || no_filters) {
    console.log(`running = ${core.Main.running}`);
  }
  if (filter_list.includes('authenticated') || no_filters) {
    console.log(`authenticated = ${core.Session.authenticated}`);
  }
  if (filter_list.includes('config') || no_filters) {
    console.log('config:');
    core.print_item(core.Session.config, '   ');
  }
}

module.exports.dev = dev;
module.exports.explore = explore;
module.exports.debug = debug;
