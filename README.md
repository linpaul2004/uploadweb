# uploadweb

A file upload tool for personal use. It allows users to upload files through a web page to Google Cloud Storage (GCS) and provides temporary download links.

## Features

- Upload files directly from the browser using `multipart/form-data`
- Optional custom filename on upload, or keep the original filename
- List all files in the GCS bucket
- Generate time-limited download links (default 5 minutes)
- Supports deployment to **Google Cloud Run** via Docker

## Project structure

```
uploadweb/
├── main.py           # Backend API (functions-framework)
├── index.html        # Upload interface
├── requirements.txt
├── Dockerfile
├── .dockerignore
├── .gitignore
└── LICENSE
```

## Prerequisites

1. A Google Cloud project
2. A GCS bucket
3. A service account with `Service Account Token Creator` permission

### Optional bucket lifecycle rule

If you want files older than 7 days to be deleted automatically, add a lifecycle rule to the bucket:

- Condition: object age ≥ 7 days
- Action: delete

## Configuration

Update the following constants in `main.py`:

| Constant | Description | Default |
|----------|-------------|---------|
| `BUCKET_NAME` | GCS bucket name | Environment Variable |
| `DOWNLOAD_LINK_LAST_MIN` | Download link expiration in minutes | `5` |

## Local development

```bash
pip install -r requirements.txt

# Make sure Application Default Credentials are set first
# gcloud auth application-default login

functions-framework --target=main --port=8080
```

Open http://localhost:8080 to use the app.

## API

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Returns the upload page |
| `GET` | `/?action=list` | Retrieves the file list with signed download URLs |
| `POST` | `/` | Uploads a file using `multipart/form-data` |

### Upload request format

- `file`: file content
- `filename`: storage filename (optional; if omitted, the original filename is used)

## License

[MIT License](LICENSE)
