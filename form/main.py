import json
from flask import Response
from utils import authenticate

def action_form(request):
    """Return form endpoint data for action"""
    auth = authenticate(request)
    if auth.status_code != 200:
        return auth

    request_json = request.get_json()
    form_params = request_json['form_params']
    print(form_params)

    default_question = 'Can you summarize the following dataset in 10 bullet points?'
    if 'question' in form_params:
        default_question = form_params['question']

    default_params = 'yes'
    if 'default_params' in form_params:
        default_params = form_params['default_params']

    default_row_or_all = 'all'
    if 'row_or_all' in form_params:
        default_row_or_all = form_params['row_or_all']

    # step 1 - select a prompt
    response = [{
        'name': 'question',
        'label': 'Type your AI prompt',
        'description': 'Type your prompt to generate a model response.',
        'type': 'textarea',
        'required': True,
        "default":  default_question
    },
        {
        'name': 'row_or_all',
        'label': 'Run per row or all results?',
        'description': "Choose whether to run the model on all the results together, or, individually per row.",
        'type': 'select',
        'required': True,
        "default":  default_row_or_all,
        'options': [{'name': 'all', 'label': 'All Results'},
                    {'name': 'row', 'label': 'Per Row'}],
    },
        {
        'name': 'default_params',
        'label': 'Default Parameters?',
        'description': "Select 'no' to customize text model parameters.",
        'type': 'select',
        'required': True,
        "default":  default_params,
        'options': [{'name': 'yes', 'label': 'Yes'},
                    {'name': 'no', 'label': 'No'}],
        'interactive': True  # dynamic field for model specific options
    }]

    # step 2 - optional - customize model params
    if 'default_params' in form_params and form_params['default_params'] == 'no':
        response.extend([{
            'name': 'temperature',
            'label': 'Temperature',
            'description': 'The temperature is used for sampling during the response generation, which occurs when topP and topK are applied (Acceptable values = 0.0–1.0)',
            'type': 'text',
            'default': '0.2',
        },
            {
            'name': 'max_output_tokens',
            'label': 'Max Output Tokens',
            'description': 'Maximum number of tokens that can be generated in the response (Acceptable values = 1–1024)',
            'type': 'text',
            'default': '1024',
        },
            {
            'name': 'top_k',
            'label': 'Top-k',
            'description': 'Top-k changes how the model selects tokens for output. Specify a lower value for less random responses and a higher value for more random responses. (Acceptable values = 1-40)',
            'type': 'text',
            'default': '40',
        },
            {
            'name': 'top_p',
            'label': 'Top-p',
            'description': 'Top-p changes how the model selects tokens for output. Specify a lower value for less random responses and a higher value for more random responses. (Acceptable values = 0.0–1.0)',
            'type': 'text',
            'default': '0.8',
        }
        ])

    print('returning form json: {}'.format(json.dumps(response)))
    return Response(json.dumps(response), status=200, mimetype='application/json')