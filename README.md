To setup certbot: 

1. move temp-compose.yaml and nginx-temp.conf to BiotechBin directory and run 'docker compose up --build'
2. move to a new terminal
3. run:
   docker compose exec certbot certbot certonly -f temp-compose.yaml \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email biotechbin@gmail.com \
    --agree-tos \
    --no-eff-email \
    -d biotechbin.com
4. move temporary files back to CertbotSetup
