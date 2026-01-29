import boto3
glue = boto3.client("glue")

def lambda_handler(event, context):
    crawler_name = event.get("crawler_name", "croustillant_crawler-demo")
    glue.start_crawler(Name=crawler_name)
    return {"status": "started", "crawler": crawler_name}
