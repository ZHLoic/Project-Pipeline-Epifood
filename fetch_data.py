import json
import os
import urllib.request
import time
from datetime import datetime
import boto3

# généré avec mon pote titi

s3 = boto3.client("s3")

BUCKET_NAME = os.environ.get("BUCKET_NAME")# recup var environnement defini dans la configuration de la fonction sur AWS
API_URL = "https://api.croustillant.menu/v1/plats/top"

# Config
MAX_RETRIES = 3
TIMEOUT_SECONDS = 15
RETRY_DELAY = 10  # secondes entre chaque tentative

def lambda_handler(event, context):
    # Vérification variable d'environnement
    if not BUCKET_NAME:
        raise ValueError("BUCKET_NAME n'est pas défini !")

    last_exception = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"Tentative {attempt} d'appel API")

            request = urllib.request.Request(
                API_URL,
                headers={"User-Agent": "aws-lambda-data-pipeline"}
            )

            with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                status = response.getcode()
                response_body = response.read()
                data = json.loads(response_body)

            # Gérer throttling si API retourne 429
            if status == 429:
                print("429 Too Many Requests, retrying...")
                time.sleep(RETRY_DELAY)
                continue

            # Affiche le JSON pour Loïc
            print("=== JSON de l'API ===")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            print("=====================")

            break  # succès → sortir de la boucle

        except Exception as e:
            print(f"Erreur tentative {attempt}: {e}")
            last_exception = e
            time.sleep(RETRY_DELAY)
    else:
        # toutes les tentatives ont échoué
        raise last_exception

    # Écriture S3 avec timestamp
    ingestion_time = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
    s3_key = f"raw/plats_top/ingestion_time={ingestion_time}/plats.json"

    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=s3_key,
        Body=json.dumps(data, ensure_ascii=False),
        ContentType="application/json"
    )

    return {
        "statusCode": 200,
        "body": f"Données écrites dans s3://{BUCKET_NAME}/{s3_key}"
    }