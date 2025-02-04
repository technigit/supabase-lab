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
  var url = core.Session.url;
  var api_key = null;
  if ('url' in core.Session.config) {
    url = core.Session.config['url'];
  }
  if ('api_key' in core.Session.config) {
    api_key = core.Session.config['api_key'];
  }
  console.log(`Connecting to ${url}`);
  if (api_key == null) {
    core.error_print('No api_key configuration found.');
    return;
  }
  core.Session.config['url'] = url;
  core.Session.config['api_key'] = api_key;
  try {
    core.Session.supabase = createClient(url, api_key);
    console.log('Ready to login.');
  } catch (e) {
    core.handle_error('connect', e, true);
  }
};

////////////////////////////////////////////////////////////////////////////////
// run a Supabase Edge Function
////////////////////////////////////////////////////////////////////////////////

const edge_function = async (url, payload) => {
  var headers = {
    "Authorization": `Bearer ${core.Session.jwt_token}`,
    "Content-Type": "application/json"
  };
  axios.post(url, payload, { headers: headers, timeout: 10000 })
    .then(response => {
      if (core.verbose()) {
        show_response(response);
      } else {
        console.log(response.data);
      }
    })
    .catch(error => {
      if (error.response) {
        console.log('Response error:', error.response.data); // Response error
      } else if (error.request) {
        console.log('Request error:', error.request); // Request error
      } else {
        console.log('Error:', error.message); // Other errors
      }
    });
};

////////////////////////////////////////////////////////////////////////////////
// display response values after sending a request to Supabase
////////////////////////////////////////////////////////////////////////////////

function show_response(response) {
  console.log(`Response URL: ${response.config.url}`);
  console.log(`Status Code: ${response.status}`);
  console.log(`Status Text: ${response.statusText}`);
  console.log(`Request Method: ${response.request.method}`);
  console.log('Response Data:');
  for (let key in response.data) {
    console.log(`   ${key}: ${response.data[key]}`);
  }  
  console.log('Response Headers:');
  for (let key in response.headers) {
    console.log(`   ${key}: ${response.headers[key]}`);
  }  
}

////////////////////////////////////////////////////////////////////////////////
// sign in the user using email/password authentication
////////////////////////////////////////////////////////////////////////////////

const sign_in = async (email, password) => {
  if (email == '' || password == '') {
    console.log('Invalid email or password.');
    return;
  }
  console.log('Logging in...');

  try {
    const { data, error } = await core.Session.supabase.auth.signInWithPassword({ email: email, password: password });
    if (error) {
      console.error('Login failed:', error.message);
    } else {
      core.Session.jwt_token = data.session.access_token;
      var session_user_email = data.session.user.email;
      var last_sign_in_at = core.show_time(data.user.last_sign_in_at);
      console.log(`${session_user_email} logged in.`);
      console.log(`Last login: ${last_sign_in_at}`);
      core.Session.authenticated = true;
    }
  } catch (e) {
    console.error('Unexpected error:', e);
  }
};

////////////////////////////////////////////////////////////////////////////////
// sign out
////////////////////////////////////////////////////////////////////////////////

const sign_out = async () => {
  console.log('Logging out.');
  core.Session.supabase.auth.signOut();
  core.Session.jwt_token = null;
  core.Session.authenticated = false;
};

module.exports.connect = connect;
module.exports.edge_function = edge_function;
module.exports.sign_in = sign_in;
module.exports.sign_out = sign_out;