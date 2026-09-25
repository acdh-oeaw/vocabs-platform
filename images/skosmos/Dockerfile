# Build context: repository root. Upstream web root verified at Skosmos v3.3.
ARG SKOSMOS_UPSTREAM_TAG
FROM quay.io/natlibfi/skosmos:${SKOSMOS_UPSTREAM_TAG}
COPY images/skosmos/apply-entity-accept.php /tmp/apply-entity-accept.php
RUN php /tmp/apply-entity-accept.php \
    && php -l /var/www/html/src/controller/EntityController.php \
    && rm /tmp/apply-entity-accept.php
COPY branding/custom-templates/ /var/www/html/custom-templates/
COPY branding/plugins/ /var/www/html/plugins/
COPY branding/css/ /var/www/html/resource/css/acdh/
COPY branding/images/ /var/www/html/resource/pics/acdh/
COPY branding/assets/fonts/ /var/www/html/resource/fonts/acdh/
