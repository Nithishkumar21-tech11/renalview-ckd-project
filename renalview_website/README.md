# RenalView CKD Record Review Website

This college-project website uses your kidney illustration, a sign-in/create-account screen, text-based PDF value suggestions, editable measurements, and the saved CKD model's class output.

## Start on Windows

Open PowerShell in this folder and run:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:RENALVIEW_SESSION_SECRET = "replace-this-with-a-long-random-secret"
.\.venv\Scripts\python.exe -m uvicorn server:app --reload
```

Open http://127.0.0.1:8000. Create an account with your email or mobile number and a password (at least 8 characters), then sign in. Accounts are stored in a local SQLite file named `renalview_users.sqlite3`. Passwords are stored as salted hashes. This demo does not send email or SMS verification codes.

The included `sample_ckd_record.pdf` is fictional and can be used to try PDF extraction. The PDF reader needs selectable text; scanned/image-only PDFs are not supported. Review all suggested measurements before generating the model class.

## Hosting notes

A hosted website processes uploaded PDFs on the app server. Do not upload real patient records to a public demo. For internet deployment, set a strong persistent `RENALVIEW_SESSION_SECRET`, enable HTTPS cookies with `RENALVIEW_HTTPS_ONLY=1`, and configure durable private storage and a production-grade authentication/privacy setup before accepting real users.
