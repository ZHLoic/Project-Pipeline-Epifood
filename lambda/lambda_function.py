import json
import os
import urllib.request
import time
from datetime import datetime
import boto3

# Client S3
s3 = boto3.client("s3")

# Variables d'environnement
BUCKET_NAME = os.environ.get("BUCKET_NAME")

# API CROUStillant
API_URL = "https://api.croustillant.menu/v1/plats/top"

# Configuration
MAX_RETRIES = 10
TIMEOUT_SECONDS = 60
RETRY_DELAY = 1  # secondes

def lambda_handler(event, context):

    # Vérification variable d'environnement
    if not BUCKET_NAME:
        raise ValueError("La variable d'environnement BUCKET_NAME n'est pas définie")

    last_exception = None

    # Appel API avec retry
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"Tentative {attempt} d'appel API CROUStillant")

            request = urllib.request.Request(
                API_URL,
                headers={
                    "User-Agent": "aws-lambda-data-pipeline"
                }
            )

            with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                status_code = response.getcode()
                response_body = response.read()

            # Gestion du throttling
            if status_code == 429:
                print("429 Too Many Requests → retry")
                time.sleep(RETRY_DELAY)
                continue

            # Parse JSON
            api_response = json.loads(response_body)

            # 🔥 IMPORTANT : on extrait uniquement la liste pour Glue
            data = api_response["data"]

            print(f"{len(data)} plats récupérés depuis l'API")

            break  # succès → sortie de la boucle

        except Exception as e:
            print(f"Erreur tentative {attempt}: {e}")
            last_exception = e
            time.sleep(RETRY_DELAY)

    else:
        # Toutes les tentatives ont échoué
        raise last_exception

    # Timestamp pour partition Glue
    ingestion_time = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")

    # Clé S3 (Data Lake RAW)
    s3_key = f"raw/plats_top/ingestion_time={ingestion_time}/plats.json"

    # Écriture dans S3
    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=s3_key,
        Body=json.dumps(data, ensure_ascii=False),
        ContentType="application/json"
    )

    print(f"Données écrites dans s3://{BUCKET_NAME}/{s3_key}")

    return {
        "statusCode": 200,
        "body": f"{len(data)} plats écrits dans s3://{BUCKET_NAME}/{s3_key}"
    }
