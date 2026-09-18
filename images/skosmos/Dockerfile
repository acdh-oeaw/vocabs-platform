# Build context: repository root. Upstream web root verified at Skosmos v3.3.
ARG SKOSMOS_UPSTREAM_TAG
FROM quay.io/natlibfi/skosmos:${SKOSMOS_UPSTREAM_TAG}
COPY branding/custom-templates/ /var/www/html/custom-templates/
COPY branding/plugins/ /var/www/html/plugins/
COPY branding/css/ /var/www/html/resource/css/acdh/
COPY branding/images/ /var/www/html/resource/pics/acdh/
