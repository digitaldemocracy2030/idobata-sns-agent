import base64
import hashlib
import json
import os
import time
import urllib.parse

import requests

from config import (
    TWITTER_CLIENT_ID,
    TWITTER_CLIENT_SECRET,
    TWITTER_REDIRECT_URI,
    TWITTER_SCOPES,
    TWITTER_AUTHORIZATION_URL,
    TWITTER_TOKEN_URL,
    TOKEN_FILE
)


def generate_code_verifier():
    """Generate a code verifier for PKCE authentication."""
    return base64.urlsafe_b64encode(os.urandom(40)).decode('utf-8').rstrip('=')


def generate_code_challenge(verifier):
    """Generate a code challenge from the verifier for PKCE authentication."""
    hashed = hashlib.sha256(verifier.encode('utf-8')).digest()
    return base64.urlsafe_b64encode(hashed).decode('utf-8').rstrip('=')


def initial_auth():
    """Perform initial OAuth2 authentication flow."""
    verifier = generate_code_verifier()
    challenge = generate_code_challenge(verifier)

    params = {
        'response_type': 'code',
        'client_id': TWITTER_CLIENT_ID,
        'redirect_uri': TWITTER_REDIRECT_URI,
        'scope': TWITTER_SCOPES,
        'state': 'state',
        'code_challenge': challenge,
        'code_challenge_method': 'S256'
    }

    url = f"{TWITTER_AUTHORIZATION_URL}?{urllib.parse.urlencode(params)}"
    print(f"↓のURLにアクセスして認証してください：\n{url}\n")

    redirected = input("リダイレクト後のURLを貼り付けてください: ")
    parsed = urllib.parse.urlparse(redirected)
    code = urllib.parse.parse_qs(parsed.query)['code'][0]

    # Get access token using authorization code
    data = {
        'code': code,
        'grant_type': 'authorization_code',
        'client_id': TWITTER_CLIENT_ID,
        'redirect_uri': TWITTER_REDIRECT_URI,
        'code_verifier': verifier
    }
    resp = requests.post(TWITTER_TOKEN_URL, data=data, auth=(TWITTER_CLIENT_ID, TWITTER_CLIENT_SECRET)).json()

    # Save tokens
    if 'access_token' in resp:
        resp['expires_at'] = int(time.time()) + resp['expires_in']
        with open(TOKEN_FILE, 'w') as f:
            json.dump(resp, f, indent=2)
        print("アクセストークンが保存されました。")
        return resp['access_token']
    else:
        raise Exception(f"エラー: {resp}")


def refresh_access_token(refresh_token):
    """Refresh the access token using a refresh token."""
    data = {
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token',
        'client_id': TWITTER_CLIENT_ID
    }
    resp = requests.post(TWITTER_TOKEN_URL, data=data, auth=(TWITTER_CLIENT_ID, TWITTER_CLIENT_SECRET)).json()

    if 'access_token' in resp:
        resp['expires_at'] = int(time.time()) + resp['expires_in']
        # If no new refresh token is returned, keep using the old one
        resp['refresh_token'] = resp.get('refresh_token', refresh_token)

        with open(TOKEN_FILE, 'w') as f:
            json.dump(resp, f, indent=2)
        print("アクセストークンを更新しました。")
        return resp['access_token']
    else:
        raise Exception(f"トークン更新エラー: {resp}")


def load_token():
    """Load saved tokens from file."""
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r') as f:
            return json.load(f)
    return None


def get_valid_token():
    """Get a valid access token, refreshing if necessary."""
    tokens = load_token()
    if tokens:
        # Use existing token if it's valid for at least 60 more seconds
        if tokens['expires_at'] > int(time.time()) + 60:
            return tokens['access_token']
        else:
            print("アクセストークン期限切れ、更新します。")
            return refresh_access_token(tokens['refresh_token'])
    else:
        print("トークンがありません。初回認証を開始します。")
        return initial_auth()