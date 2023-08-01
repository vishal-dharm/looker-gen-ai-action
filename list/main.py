import json
import os
from flask import Response
from icon import icon_data_uri
from utils import authenticate

BASE_DOMAIN = 'https://{}-{}.cloudfunctions.net/{}-'.format(os.environ.get(
    'REGION'), os.environ.get('PROJECT'), os.environ.get('ACTION_NAME'))

# https://github.com/looker-open-source/actions/blob/master/docs/action_api.md#actions-list-endpoint
def action_list(request):
    """Return action hub list endpoint data for action"""
    auth = authenticate(request)
    if auth.status_code != 200:
        return auth

    response = {
        'label': 'PaLM API (Vertex AI)',
        'integrations': [{
            'name': os.environ.get('ACTION_NAME'),
            'label': os.environ.get('ACTION_LABEL'),
            'supported_action_types': ['query'],
            "icon_data_uri": icon_data_uri,
            'form_url': BASE_DOMAIN + 'form',
            'url': BASE_DOMAIN + 'execute',
            'supported_formats': ['json'],
            'supported_formattings': ['formatted'],
            'supported_visualization_formattings': ['noapply'],
            'params': [
                {'name': 'email', 'label': 'Email',
                    'user_attribute_name': 'email', 'required': True},
                {'name': 'user_id', 'label': 'User ID',
                    'user_attribute_name': 'id', 'required': True}
            ]
        }]
    }

    print('returning integrations json')
    return Response(json.dumps(response), status=200, mimetype='application/json')