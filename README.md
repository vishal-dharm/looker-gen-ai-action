## Overview

This repository provides an example of using generative AI (PaLM API) to examine the results of a query and email you a summary of the results. This is done using the Looker Action API to trigger a Google Cloud Function and generate an explanation using the [PaLM API (Vertex AI)](https://cloud.google.com/vertex-ai/docs/generative-ai/learn/models). With this action, users can take the results of an Explore query, specify their LLM parameters (temperature, top-k, top-p, and max_output_tokens), and email themselves the LLM-inspired insight into their data.

There are three Cloud Functions included in this demo that are used to communicate from Looker to Vertex AI via the [Action API](https://github.com/looker-open-source/actions/blob/master/docs/action_api.md):

1. `list/main.py` - Lists the metadata for the action, including the form and execute endpoints
1. `form/main.py` - The dynamic form template to presented to users to send parameters to the execute endpoint
1. `execute/main.py` - The function to run the prediction on the data that is being sent, and send an email

## Requirements:

- Looker instance in which you have aAdmin permissions.
- Google Cloud Project with the following APIs enabled:
  - Secret Manager API
  - Cloud Build API
  - Cloud Functions API
  - Vertex AI API
- Sendgrid account and API Key for sending emails.
  - You can create a free developer account from the [GCP marketplace](https://console.cloud.google.com/marketplace/details/sendgrid-app/sendgrid-email)

Use [Cloud Shell](https://cloud.google.com/shell) or the [`gcloud CLI`](https://cloud.google.com/sdk/docs/install) for the following steps.

The two variables you must to modify are:

- `PROJECT` - ID you want to deploy the Cloud Functions to
- `EMAIL_SENDER` - Email address of the sender

1. Set the variables below:

   ```
   ACTION_LABEL="Vertex AI"
   ACTION_NAME="vertex-ai"
   REGION="us-central1"
   PROJECT="my-project-id"
   EMAIL_SENDER="my-sender-email-address@foo.com"

   ```

1. Create a [.env.yaml](.env.yaml.example) with variables:

   ```
   printf "ACTION_LABEL: ${ACTION_LABEL}\nACTION_NAME: ${ACTION_NAME}\nREGION: ${REGION}\nPROJECT: ${PROJECT}\nEMAIL_SENDER: ${EMAIL_SENDER}" > .env.yaml
   ```

1. Generate the `LOOKER_AUTH_TOKEN` secret. The auth token secret can be any randomly generated string. You can generate such a string with the openssl command:

   ```
   LOOKER_AUTH_TOKEN="`openssl rand -hex 64`"
   ```

1. Add the Auth Token and [Sendgrid API key](https://app.sendgrid.com/settings/api_keys) as Secrets, then create a Service Account to run the Cloud Functions and give it access to the Secrets:

   ```
   SENDGRID_API_KEY="<INSERT SENDGRID API KEY>"

   printf ${SENDGRID_API_KEY} | gcloud secrets create SENDGRID_API_KEY --data-file=- --replication-policy=user-managed --locations=${REGION} --project=${PROJECT}

   printf ${LOOKER_AUTH_TOKEN} | gcloud secrets create LOOKER_AUTH_TOKEN --data-file=- --replication-policy=user-managed --locations=${REGION} --project=${PROJECT}

   gcloud iam service-accounts create vertex-ai-actions-cloud-function --display-name="Vertex AI Actions Cloud Functions" --project=${PROJECT}

   SERVICE_ACCOUNT_EMAIL=vertex-ai-actions-cloud-function@${PROJECT}.iam.gserviceaccount.com

   eval gcloud projects add-iam-policy-binding ${PROJECT} --member=serviceAccount:${SERVICE_ACCOUNT_EMAIL} --role='roles/cloudfunctions.invoker'

   eval gcloud projects add-iam-policy-binding ${PROJECT} --member=serviceAccount:${SERVICE_ACCOUNT_EMAIL} --role='roles/aiplatform.user'

   eval gcloud projects add-iam-policy-binding ${PROJECT} --member=serviceAccount:${SERVICE_ACCOUNT_EMAIL} --role='roles/secretmanager.secretAccessor'

   eval gcloud secrets add-iam-policy-binding SENDGRID_API_KEY --member=serviceAccount:${SERVICE_ACCOUNT_EMAIL} --role='roles/secretmanager.secretAccessor' --project=${PROJECT}

   eval gcloud secrets add-iam-policy-binding LOOKER_AUTH_TOKEN --member=serviceAccount:${SERVICE_ACCOUNT_EMAIL} --role='roles/secretmanager.secretAccessor' --project=${PROJECT}
   ```

1. Deploy 3 Cloud Functions for action hub list, action form, and action execute.

   1. Basics
      1. **Runtime**: `Python 3.11`
      1. **Environment**: `2nd gen`
      1. **Region**: same as above
      1. **Authentication**: `Allow unauthenticated`
   1. Runtime, build, connections, and security settings
      1. Memory allocated: `1024 MB`
      1. Timeout: `540 s`
   1. Secrets
      1. `LOOKER_AUTH_TOKEN`
      1. `SENDGRID_API_KEY`
   2. Example gcloud command to deploy action_execute:
      ```
      gcloud functions deploy vertex-ai-execute --entry-point action_execute --env-vars-file .env.yaml --trigger-http --runtime=python311 --allow-unauthenticated --timeout=540s --region=${REGION} --project=${PROJECT} --service-account ${SERVICE_ACCOUNT_EMAIL} --set-secrets 'LOOKER_AUTH_TOKEN=LOOKER_AUTH_TOKEN:latest,SENDGRID_API_KEY=SENDGRID_API_KEY:latest' --memory=1024MB
      ```


1. Copy the Action Hub URL (`action_list` endpoint) and the `LOOKER_AUTH_TOKEN` to input into Looker:

1. In Looker, go to the **Admin > Actions** page and click **Add Action Hub**

   - Enter the Action Hub URL
   - click **Configure Authorization** and enter the `LOOKER_AUTH_TOKEN` value for the Authorization Token and click **Enable**
   - Toggle the **Enabled** button and click **Save**
