# Organisation root CA (local only)

Place a PEM export of your organisation's root CA here when nada-ai runs behind a TLS-inspecting proxy. Do not commit
`.pem` or `.crt` files; git ignores them in this folder.

Symptom: `SSL: CERTIFICATE_VERIFY_FAILED ... self-signed certificate in certificate chain` when the container calls
the NADA host or Hugging Face.

Docker:

1. Export the root CA as a PEM file into `certs/` (from the OS certificate store, or ask IT).
2. In `docker-compose.opensearch.yml`, uncomment `SSL_CERT_FILE`, `REQUESTS_CA_BUNDLE` and the `./certs/...` volume
   line, and make the file name match yours.
3. `docker compose -f docker-compose.opensearch.yml up -d`

Host: `ai4data` installs `truststore`, so Python uses the operating system's certificate store. A host that already
trusts the NADA URL in a browser usually needs nothing here.

See [TLS / corporate proxies](../docs/GUIDE.md#tls--corporate-proxies) in the developer guide.
