import base64
import datetime
import hashlib
import hmac
import json
#import urllib.request as req
import requests
import yaml
from datetime import datetime
from dateutil.tz import tzoffset

class Bca():
    ''' BCA API Wrapper '''

    api_key = ""
    api_secret = ""
    client_id = ""
    client_secret = ""
    host = "sandbox.bca.co.id"
    corporate_id = ""
    account_number = ""
    origin = "yourhostname"
    
    _oauth_path = "/api/oauth/token"
    _access_token = False
    _balance_path = '/banking/v2/corporates/{corporate_id}/accounts/{account_number}'
    _statement_path = '/banking/v2/corporates/{corporate_id}/accounts/' \
            '{account_number}/statements?EndDate={end_date}&StartDate={start_date}'
    _transfer_path = '/banking/corporates/transfers'


    def __init__(self, cfg):

        self.api_key = cfg['api_key']
        self.api_secret = cfg['api_secret']
        self.client_id = cfg['client_id']
        self.client_secret = cfg['client_secret']
        self.host = cfg['host']
        self.corporate_id = cfg['corporate_id']
        self.account_number = cfg['account_number']
        self.origin = cfg['origin']


        oauth =  self.get_token()

    def get_token(self):
        ''' Signing in client and get access token.'''
        url = self.host + self._oauth_path
        payload = {'grant_type': 'client_credentials'}
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': 'Basic ' + \
                base64.b64encode(str.encode(self.client_id + ':' + self.client_secret)).decode('UTF-8')
        }

        req = requests.post(url, data=payload, headers=headers)
        response_data =  req.json()

        if 'access_token' in response_data:
            self._save_token(response_data['access_token'])
            return True
        return r

    def get_statement(self, start_date, end_date=None, corporate_id=False, account_number=False):
        ''' Get BCA statement data '''

        path = self._statement_path.format(**{
            'corporate_id': corporate_id or self.corporate_id,
            'account_number': account_number or self.account_number[0],
            'start_date': start_date,
            'end_date': end_date if end_date else start_date
        })
        url = self.host + path

        timestamp = self._get_timestamp()        
        signature = self._generate_signature(path, timestamp, http_method='GET')

        headers = self._set_headers(timestamp, signature)
        payload = {}

        req = requests.get(url, data=payload, headers=headers)
        response_data =  req.json()
        return response_data

    def get_balance(self, corporate_id=False, account_number=False):
        ''' Get API Balance '''

        path = self._balance_path.format(**{
            'corporate_id': corporate_id  if corporate_id else self.corporate_id,
            'account_number': ",".join(account_number) \
                if isinstance(account_number, list) else self.account_number[0] 
        })

        url = self.host + path

        timestamp = self._get_timestamp()        
        signature = self._generate_signature(path, timestamp, http_method='GET')

        headers = self._set_headers(timestamp, signature)
        payload = {}

        req = requests.get(url, data=payload, headers=headers)
        response_data =  req.json()
        return response_data

    def _get_timestamp(self):
        now = datetime.now(tzoffset('GMT', +7*60*60))
        timestamp = now.isoformat()
        timestamp = timestamp[:23] + timestamp[26:]
        return timestamp

    def _set_headers(self, timestamp, signature):
        headers = {
            'Authorization': 'Bearer {}'.format(self._get_token()),
            'Content-Type': 'application/json',
            'Origin': self.origin,
            'X-BCA-Key': self.api_key,
            'X-BCA-Timestamp': timestamp,
            'X-BCA-Signature': signature
        }

        return headers

    def _generate_signature(self, path, timestamp, http_method="POST", request_body=""):
        ''' Generate signature to be sent. '''
        signature = hmac.new(self.api_secret.encode(), digestmod=hashlib.sha256)
        value = http_method + ':' + path + ':' + self._get_token() + \
            ':' + hashlib.sha256(request_body).hexdigest() + ':' + timestamp
        signature.update(value.encode())
        return signature.hexdigest()

    def _save_token(self, token):
        #TODO save to cache
        self._access_token = token
        return self._access_token

    def _get_token(self):
        #TODO get from cache
        return self._access_token