from django.shortcuts import redirect
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response

import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
import os

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# client_id, client secret etc. recieved while creating Oauth 2
CLIENT_SECRETS_FILE = 'credentials.json'

SCOPES = ['https://www.googleapis.com/auth/calendar']
REDIRECT_URL = 'http://127.0.0.1:8000/rest/v1/calendar/redirect'
API_SERVICE_NAME = 'calendar'
API_VERSION = 'v3'



class GoogleCalendarInitView(APIView):
    def get(self, request:Request):
        # Define the OAuth2 flow
        flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE, scopes=SCOPES
        )

        flow.redirect_uri = REDIRECT_URL

        authorization_url, state = flow.authorization_url(
            access_type = 'offline',
            include_granded_scopes = 'true'
        )
        
        request.session['state'] = state

        return Response({"authorization_url" : authorization_url})
    

class GoogleCalendarRedirectView(APIView):
    def get(self, request : Request):

        state = request.session['state']

        flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE, scopes=SCOPES, state=state
        )

        flow.redirect_uri = REDIRECT_URL

        authorization_response = request.get_full_path()
        flow.fetch_token(authorization_response=authorization_response)


        credentials = flow.credentials
        request.session['credentials'] = credentials_to_dict(credentials)

        if 'credentials' not in request.session:
            return redirect('v1/calender/init')
        
        credentials = google.oauth2.credentials.Credentials(
            **request.session['credentials']
        )

        service = googleapiclient.discovery.build(
            API_SERVICE_NAME, API_VERSION, credentials=credentials
        )

        calender_list = service.calendarList().list().execute()

        calender_id = calender_list['items'][0]['id']

        events = service.events().list(calendarId=calender_id).execute()

        events_list_append = []
        if not events['items']:
            return Response({"message": "No data found or Invalid user credentials"})

        else:
            for event_list in events['items']:
                events_list_append.append(event_list)
            return Response({"events" : events_list_append})
        


def credentials_to_dict(credentials):
  return {'token': credentials.token,
          'refresh_token': credentials.refresh_token,
          'token_uri': credentials.token_uri,
          'client_id': credentials.client_id,
          'client_secret': credentials.client_secret,
          'scopes': credentials.scopes}