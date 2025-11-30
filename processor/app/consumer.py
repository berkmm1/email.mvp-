# RabbitMQ consumer: kuyruğu dinler, sınıflandırır, ekleri MinIO'ya yükler, basit threat_score hesaplar
import os
import pika
import json
from classifier import MailClassifier
from utils import upload_to_minio
import base64

RABBIT_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672")
QUEUE_NAME = os.getenv("QUEUE_NAME", "new_message")

def submit_to_sandbox_stub(s3_path):
    # STUB: sandbox entegrasyonu buraya gelecek (AnyRun, VirusTotal, Cuckoo vb)
    # Bu demo için rastgele "unknown" döndürüyoruz.
    return {"verdict": "unknown", "notes": "sandbox not configured"}

def process_message(ch, method, properties, body):
    msg = json.loads(body)
    print("=> Processing:", msg.get('subject'))
    classifier = process_message.classifier
    out = classifier.predict(msg.get('subject',''), msg.get('text',''))
    msg['category'] = out['category']
    msg['category_confidence'] = out['confidence']

    # Attachments: base64 içerik varsa MinIO'ya yükle
    processed_attachments = []
    for a in msg.get('attachments', []):
        filename = a.get('filename') or ('file-' + str(int(os.times()[4]*1000)))
        content_b64 = a.get('content')
        if not content_b64:
            processed_attachments.append({"filename": filename, "s3": None, "sandbox": {"verdict": "no_content"}})
            continue
        file_bytes = base64.b64decode(content_b64)
        s3_path = upload_to_minio(file_bytes, filename)
        sandbox_result = submit_to_sandbox_stub(s3_path)
        processed_attachments.append({"filename": filename, "s3": s3_path, "sandbox": sandbox_result})

    msg['attachments_processed'] = processed_attachments

    # Basit threat score kuralları
    threat_score = 0.0
    if out['confidence'] < 0.5:
        threat_score += 0.2
    # eğer sandbox 'malicious' deseydi:
    for ap in processed_attachments:
        if ap['sandbox'].get('verdict') == 'malicious':
            threat_score += 1.0

    msg['threat_score'] = threat_score
    msg['status'] = 'quarantine' if threat_score >= 0.8 else 'delivered'

    print("   Category:", msg['category'], "conf:", msg['category_confidence'])
    print("   Status:", msg['status'], "threat:", msg['threat_score'])
    # burada gerçek sistemde DB'ye kaydedebilirsin
    ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    params = pika.URLParameters(RABBIT_URL)
    conn = pika.BlockingConnection(params)
    ch = conn.channel()
    ch.queue_declare(queue=QUEUE_NAME, durable=True)
    ch.basic_qos(prefetch_count=1)
    process_message.classifier = MailClassifier()
    ch.basic_consume(queue=QUEUE_NAME, on_message_callback=process_message)
    print(" [*] Waiting for messages. To exit press CTRL+C")
    ch.start_consuming()

if __name__ == "__main__":
    main()
