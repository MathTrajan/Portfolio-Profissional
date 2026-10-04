# Imagem do portfolio no Fly.io.
#
# O site e um index.html com CSS e JS embutidos mais as capas .svg: nao ha
# etapa de build, nada para compilar, nenhuma dependencia. A imagem e so o
# Caddy com os arquivos estaticos dentro.
FROM caddy:2-alpine

COPY Caddyfile /etc/caddy/Caddyfile
COPY index.html /srv/
COPY Foto.png /srv/
COPY *.svg /srv/

EXPOSE 8080

CMD ["caddy", "run", "--config", "/etc/caddy/Caddyfile", "--adapter", "caddyfile"]
