#!/usr/bin/env bash

set -e # break on error
set -u # warn against undefined variables
set -o pipefail
set -x # echo statements before executing

# When calling this script, set $WALLET_REACHABLE_ADDRESS to a domain or IP address
# that the wallet can reach.
export WALLET_REACHABLE_ADDRESS=${WALLET_REACHABLE_ADDRESS:-127.0.0.1}

DIR="$(cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd -P)"

# Fetch the NL Wallet at its `main` branch
if [ ! -d $DIR/nl-wallet ]; then
    git clone https://github.com/MinBZK/nl-wallet
fi

# Compile and setup nl-wallet verification_server
cargo build --manifest-path $DIR/nl-wallet/wallet_core/Cargo.toml --package verification_server --no-default-features --features "allow_insecure_url,postgres" --bin verification_server
cp $DIR/nl-wallet/wallet_core/target/debug/verification_server $DIR/nl-wallet-setup/

# Compile wallet-web
if [ ! -f $DIR/nl-wallet/wallet_web/dist/nl-wallet-web.iife.js ]; then
    export VITE_HELP_BASE_URL="https://example.com"
    pushd $DIR/nl-wallet/wallet_web
    npm ci && npm run build
    popd
fi

# Generate private key and certificate for `verification_server`
cargo run --manifest-path "$DIR/nl-wallet/wallet_core/Cargo.toml" \
    --bin wallet_ca reader \
    --ca-key-file "$DIR/nl-wallet-setup/ca.regelrecht.reader.key.pem" \
    --ca-crt-file "$DIR/nl-wallet-setup/ca.regelrecht.reader.crt.pem" \
    --common-name "regelrecht.example.com" \
    --reader-auth-file "$DIR/nl-wallet-setup/housing_reader_auth.json" \
    --file-prefix "$DIR/nl-wallet-setup/housing_reader" \
    --force

# generate verification_server config file
BASE64="openssl base64 -e -A"
export ISSUER_CA_CRT=$(openssl x509 -in $DIR/nl-wallet-setup/ca.issuer.crt.pem -inform pem -outform der | ${BASE64})
export CA_CRT=$(openssl x509 -in $DIR/nl-wallet-setup/ca.regelrecht.reader.crt.pem -inform pem -outform der | ${BASE64})
export HOUSING_CRT=$(openssl x509 -in $DIR/nl-wallet-setup/housing_reader.crt.pem -inform pem -outform der | ${BASE64})
export HOUSING_KEY=$(openssl pkcs8 -topk8 -inform PEM -outform DER -in "$DIR/nl-wallet-setup/housing_reader.key.pem" -nocrypt | ${BASE64})
export EPHEMERAL_ID_SECRET=$(dd if=/dev/urandom bs="64" count=1 2>/dev/null | xxd -p | tr -d '\n')
envsubst < $DIR/nl-wallet-setup/verification_server.toml.template > $DIR/nl-wallet-setup/verification_server.toml

# Setup issuer javascript and CSS
mkdir -p $DIR/nl-wallet-files
WALLET_FILES=(
    $DIR/nl-wallet/wallet_core/demo/demo_utils/assets/css/button-reset.css
    $DIR/nl-wallet/wallet_core/demo/demo_utils/assets/css/reset.css
    $DIR/nl-wallet/wallet_core/demo/demo_index/assets/css/nav.css
    $DIR/nl-wallet/wallet_core/demo/demo_utils/assets/css/common.css
    $DIR/nl-wallet/wallet_core/demo/demo_utils/assets/css/page.css
    $DIR/nl-wallet/wallet_core/demo/demo_utils/assets/css/buttons-after.css
    $DIR/nl-wallet/wallet_web/dist/nl-wallet-web.iife.js
)
cp ${WALLET_FILES[@]} $DIR/nl-wallet-files/

# Start postgres for the verification_server
sh $DIR/nl-wallet/scripts/start-devenv.sh postgres

# (Re)start the verification_server
killall verification_server || true
pushd $DIR/nl-wallet-setup
RUST_LOG=debug ./verification_server
popd
