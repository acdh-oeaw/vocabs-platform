# Build context: repository root. Pass a verified Java 21 JDK image pinned by digest.
ARG JAVA_BASE_IMAGE
FROM ${JAVA_BASE_IMAGE} AS download
ARG JENA_VERSION
ARG JENA_SHA512
ARG FUSEKI_SHA512
USER root
# This recipe requires a Debian/Ubuntu based Java image with apt-get.
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl && rm -rf /var/lib/apt/lists/*
RUN test -n "$JENA_VERSION" && test -n "$JENA_SHA512" \
 && curl --fail --location --retry 3 "https://archive.apache.org/dist/jena/binaries/apache-jena-${JENA_VERSION}.tar.gz" -o /tmp/jena.tar.gz \
 && echo "${JENA_SHA512}  /tmp/jena.tar.gz" | sha512sum -c - \
 && mkdir /opt/jena && tar -xzf /tmp/jena.tar.gz --strip-components=1 -C /opt/jena
RUN test -n "$FUSEKI_SHA512" \
 && curl --fail --location --retry 3 "https://archive.apache.org/dist/jena/binaries/apache-jena-fuseki-${JENA_VERSION}.tar.gz" -o /tmp/fuseki.tar.gz \
 && echo "${FUSEKI_SHA512}  /tmp/fuseki.tar.gz" | sha512sum -c - \
 && mkdir /opt/fuseki && tar -xzf /tmp/fuseki.tar.gz --strip-components=1 -C /opt/fuseki
FROM ${JAVA_BASE_IMAGE}
ARG JENA_VERSION
ENV JENA_VERSION=${JENA_VERSION}
COPY --from=download /opt/jena /opt/jena
COPY --from=download /opt/fuseki /opt/fuseki
USER root
RUN mkdir -p /fuseki/databases /fuseki/logs && chown -R 1000:1000 /fuseki
WORKDIR /fuseki
ENV JENA_HOME=/opt/jena
ENV PATH=/opt/jena/bin:$PATH
RUN test -x /opt/jena/bin/riot && test -x /opt/jena/bin/tdbloader \
 && test -x /opt/jena/bin/tdb2.tdbloader && test -x /opt/jena/bin/tdb1.xloader \
 && test -x /opt/jena/bin/tdb2.xloader
COPY --chmod=755 images/jena-tools/load.sh /usr/local/bin/load.sh
USER 1000:1000
ENTRYPOINT ["/usr/local/bin/load.sh"]
