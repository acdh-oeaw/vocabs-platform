# Build context: repository root.
# Pass a Debian base image pinned by digest.
ARG DEBIAN_BASE_IMAGE

FROM ${DEBIAN_BASE_IMAGE} AS build

ARG VINYL_VERSION
ARG VINYL_SHA256

USER root

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      ca-certificates \
      curl \
      build-essential \
      autoconf \
      automake \
      autotools-dev \
      autoconf-archive \
      cpio \
      libedit-dev \
      libjemalloc-dev \
      libncurses-dev \
      libpcre2-dev \
      libtool \
      pkg-config \
      python3-docutils \
      python3-sphinx \
 && rm -rf /var/lib/apt/lists/*

RUN test -n "$VINYL_VERSION" \
 && test -n "$VINYL_SHA256" \
 && curl --fail --location --retry 3 \
      "https://vinyl-cache.org/downloads/vinyl-cache-${VINYL_VERSION}.tgz" \
      -o /tmp/vinyl-cache.tgz \
 && echo "${VINYL_SHA256}  /tmp/vinyl-cache.tgz" | sha256sum -c - \
 && mkdir -p /src/vinyl-cache \
 && tar -xzf /tmp/vinyl-cache.tgz \
      --strip-components=1 \
      -C /src/vinyl-cache

WORKDIR /src/vinyl-cache

RUN ./configure \
      --prefix=/usr/local \
      --with-statedir=/var/lib/vinyl-cache \
 && make -j"$(nproc)" \
 && make DESTDIR=/out install

FROM ${DEBIAN_BASE_IMAGE}

ARG VINYL_VERSION
ENV VINYL_VERSION=${VINYL_VERSION}

USER root

# A C compiler is intentionally present at runtime because Vinyl compiles VCL.
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      ca-certificates \
      gcc \
      libc6-dev \
      libedit2 \
      libjemalloc2 \
      libncurses6 \
      libpcre2-8-0 \
 && rm -rf /var/lib/apt/lists/*

COPY --from=build /out/ /

RUN ldconfig \
 && mkdir -p /var/lib/vinyl-cache \
 && chown -R 10001:10001 /var/lib/vinyl-cache

USER 10001:10001

EXPOSE 6081

ENTRYPOINT ["/usr/local/sbin/vinyld"]
