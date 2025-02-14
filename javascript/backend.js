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
    core.error_print('No api_key configuration found.');
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
      core.error_print(`Axios error: ${error.message}`);
      if (error.code) {
        core.error_print(`Axios error code: ${error.code}`);
      }
    });
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
      console.error('Login failed:', error.message);
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
      core.writeln(error.message);
    } else {
      console.error('Unexpected error:', error);
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
module.exports.sign_in = sign_in;
module.exports.sign_out = sign_out;
