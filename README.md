# RenalView CKD Record Review Website

A conventional HTML/CSS/JavaScript website with a FastAPI backend. It uses the saved CKD model from the college project, suggests values from text-based PDFs, lets the user review/edit the measurements, and returns the model's CKD / Not CKD class.

## Run locally on Windows

Open PowerShell in this folder, then run:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn server:app --reload
```

Open http://127.0.0.1:8000 in a browser. Press Ctrl+C in PowerShell to stop the site.

## Share a hosted link

1. Create a GitHub repository. Unzip this package and upload its contents to the repository root, including `render.yaml` and the `assets` folder.
2. In Render, choose **New > Blueprint**, connect your GitHub repository, and follow the prompt to deploy the service described in `render.yaml`.
3. When deployment completes, Render will show the site's public `onrender.com` link. Share that link with your college.

A hosted website sends uploaded PDFs to the app server for processing. Use only the included fictional sample for a hosted college demonstration; do not upload real patient records.

The PDF parser reads selectable text and looks for labels with values on the same line. Scanned/image-only PDFs are not supported.
