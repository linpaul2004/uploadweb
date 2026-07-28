import json
import datetime
import os
import functions_framework
from google.cloud import storage
import google.auth
import google.auth.transport.requests

# 初始化 GCS 用戶端
storage_client = storage.Client()

# 取得執行環境的服務帳戶憑證（Cloud Run 會自動注入，用於簽名下載連結）
credentials, project = google.auth.default()

# GCS Bucket 名稱（由環境變數 BUCKET_NAME 提供）
BUCKET_NAME = os.environ['BUCKET_NAME']

# 下載連結維持時間
DOWNLOAD_LINK_LAST_MIN = 5

# 上傳檔案大小上限（32 MB）
MAX_UPLOAD_BYTES = 32 * 1024 * 1024

def get_html_content():
    with open('index.html', 'r', encoding='utf-8') as f:
        return f.read()

def upload_bytes_to_gcs(bucket, filename, file_bytes):
    blob = bucket.blob(filename)
    blob.upload_from_string(file_bytes)
    return {
        'message': '檔案已成功上傳！',
        'filename': filename,
        'gcs_uri': f'gs://{BUCKET_NAME}/{filename}'
    }

@functions_framework.http
def main(request):
    bucket = storage_client.bucket(BUCKET_NAME)

    if request.method == 'GET':
        # ?action=list → 回傳 JSON 檔案清單；否則回傳上傳頁面
        if request.args.get('action') == 'list':
            try:
                # 簽名 URL 需要有效的 access token
                if not credentials.valid:
                    credentials.refresh(google.auth.transport.requests.Request())

                blobs = bucket.list_blobs()
                file_list = []
                service_account_email = credentials.service_account_email

                for blob in blobs:
                    # 產生有時效的下載連結，無需將 bucket 設為公開
                    download_url = blob.generate_signed_url(
                        version="v4",
                        expiration=datetime.timedelta(minutes=DOWNLOAD_LINK_LAST_MIN),
                        method="GET",
                        service_account_email=service_account_email,
                        access_token=credentials.token
                    )

                    file_list.append({
                        'name': blob.name,
                        'size': blob.size,
                        'updated': blob.updated.isoformat() if blob.updated else None,
                        'download_url': download_url
                    })

                # 依上傳時間排序，最新的在最前面
                file_list.sort(key=lambda f: f['updated'] or '', reverse=True)

                return (json.dumps({'files': file_list}), 200, {'Content-Type': 'application/json'})

            except Exception as e:
                return (json.dumps({'error': f'無法讀取檔案清單: {str(e)}'}), 500, {'Content-Type': 'application/json'})

        return (get_html_content(), 200, {'Content-Type': 'text/html; charset=utf-8'})

    elif request.method == 'POST':
        # 接收 multipart/form-data 上傳
        uploaded_file = request.files.get('file')
        filename = (request.form.get('filename') or '').strip()

        if not uploaded_file:
            return (json.dumps({'error': '缺少上傳檔案'}), 400, {'Content-Type': 'application/json'})

        if not filename:
            filename = uploaded_file.filename or ''

        if not filename:
            return (json.dumps({'error': '缺少檔案名稱'}), 400, {'Content-Type': 'application/json'})

        try:
            file_bytes = uploaded_file.read()

            if len(file_bytes) > MAX_UPLOAD_BYTES:
                return (json.dumps({'error': '檔案大小不得超過 32 MB'}), 400, {'Content-Type': 'application/json'})

            result = upload_bytes_to_gcs(bucket, filename, file_bytes)
            return (json.dumps(result), 200, {'Content-Type': 'application/json'})
        except Exception as e:
            return (json.dumps({'error': f'處理失敗: {str(e)}'}), 500, {'Content-Type': 'application/json'})

    return ('Method Not Allowed', 405)
