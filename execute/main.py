import json
from flask import Response
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from utils import authenticate, handle_error, list_to_html, safe_cast, sanitize_and_load_json_str
from palm_api import model_with_limit_and_backoff, reduce

# https://github.com/looker-open-source/actions/blob/master/docs/action_api.md#action-execute-endpoint
def action_execute(request):
    """Generate a response from Generative AI Studio from a Looker action"""
    auth = authenticate(request)
    if auth.status_code != 200:
        return auth

    request_json = request.get_json()
    attachment = request_json['attachment']
    action_params = request_json['data']
    form_params = request_json['form_params']
    question = form_params['question']
    print(action_params)
    print(form_params)

    temperature = 0.2 if 'temperature' not in form_params else safe_cast(
        form_params['temperature'], float, 0.0, 1.0, 0.2)
    max_output_tokens = 1024 if 'max_output_tokens' not in form_params else safe_cast(
        form_params['max_output_tokens'], int, 1, 1024, 1024)
    top_k = 40 if 'top_k' not in form_params else safe_cast(
        form_params['top_k'], int, 1, 40, 40)
    top_p = 0.8 if 'top_p' not in form_params else safe_cast(
        form_params['top_p'], float, 0.0, 1.0, 0.8)

    # placeholder for model error email response
    body = 'There was a problem running the model. Please try again with less data. '
    summary = ''
    row_chunks = 50  # mumber of rows to summarize together
    try:
        all_data = sanitize_and_load_json_str(
            attachment['data'])
        if form_params['row_or_all'] == 'row':
            row_chunks = 1

        summary = model_with_limit_and_backoff(
            all_data, question, row_chunks, temperature, max_output_tokens, top_k, top_p)

        # if row, zip prompt_result with all_data and send html table
        if form_params['row_or_all'] == 'row':
            for i in range(len(all_data)):
                all_data[i]['prompt_result'] = summary[i]
            body = list_to_html(all_data)

        # if all, send summary on top of all_data
        if form_params['row_or_all'] == 'all':
            if len(summary) == 1:
                body = 'Prompt Result:<br><strong>{}</strong><br><br><br>'.format(
                    summary[0].replace('\n', '<br>'))
            else:
                reduced_summary = reduce(
                    '\n'.join(summary), temperature, max_output_tokens, top_k, top_p)
                body = 'Final Prompt Result:<br><strong>{}</strong><br><br>'.format(
                    reduced_summary.replace('\n', '<br>'))
                body += '<br><br><strong>Batch Prompt Result:</strong><br>'
                body += '<br><br><strong>Batch Prompt Result:</strong><br>'.join(
                    summary).replace('\n', '<br>') + '<br><br><br>'

            body += list_to_html(all_data)

    except Exception as e:
        body += 'PaLM API Error: ' + e.message
        print(body)

    if body == '':
        body = 'No response from model. Try asking a more specific question.'

    try:
        # todo - make email prettier
        message = Mail(
            from_email=os.environ.get('EMAIL_SENDER'),
            to_emails=action_params['email'],
            subject='Your GenAI Report from Looker',
            html_content=body
        )

        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)
        print('Message status code: {}'.format(response.status_code))
    except Exception as e:
        error = handle_error('SendGrid Error: ' + e.message, 400)
        return error

    return Response(status=200, mimetype='application/json')