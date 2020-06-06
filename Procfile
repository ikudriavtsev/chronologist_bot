web: echo $GOOGLE_PRIVATE_KEY | base64 --decode > private_key.json && gunicorn app:app --log-file - --access-logfile -
