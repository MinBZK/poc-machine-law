#!/bin/bash
set -e
set -o pipefail
set -x

echo "Starting verification_server entrypoint..."

# Check if required certificate files exist
echo "Checking for required certificate files..."
for file in ca.issuer.crt.pem ca.regelrecht.reader.crt.pem housing_reader.crt.pem housing_reader.key.pem; do
    if [ ! -f "/app/$file" ]; then
        echo "ERROR: Required file /app/$file does not exist!"
        ls -la /app/
        exit 1
    fi
done

echo "All required certificate files found."

# Generate base64-encoded certificates
echo "Generating base64-encoded certificates..."
export ISSUER_CA_CRT=$(openssl x509 -in /app/ca.issuer.crt.pem -inform pem -outform der | openssl base64 -e -A)
export CA_CRT=$(openssl x509 -in /app/ca.regelrecht.reader.crt.pem -inform pem -outform der | openssl base64 -e -A)
export HOUSING_CRT=$(openssl x509 -in /app/housing_reader.crt.pem -inform pem -outform der | openssl base64 -e -A)
export HOUSING_KEY=$(openssl pkcs8 -topk8 -inform PEM -outform DER -in /app/housing_reader.key.pem -nocrypt | openssl base64 -e -A)

# Generate ephemeral ID secret if not provided
if [ -z "$EPHEMERAL_ID_SECRET" ]; then
    echo "Generating ephemeral ID secret..."
    export EPHEMERAL_ID_SECRET=$(dd if=/dev/urandom bs=64 count=1 2>/dev/null | xxd -p | tr -d '\n')
else
    echo "Using provided EPHEMERAL_ID_SECRET"
fi

# Substitute environment variables in template
echo "Generating verification_server.toml from template..."
envsubst < /app/verification_server.toml.template > /app/verification_server.toml

echo "Configuration generated successfully."
echo "Starting verification_server..."

# verification_server is pedantic about the postgres uri, find/replace on the default cloudnative uri.
export VERIFICATION_SERVER__STORAGE__URL="${VERIFICATION_SERVER__STORAGE__URL/postgresql:\/\//postgres:\/\/}"

# Run migrations
DATABASE_URL="${VERIFICATION_SERVER__STORAGE__URL}" /app/verification_server_migrations up

# Start verification_server
exec /app/verification_server
