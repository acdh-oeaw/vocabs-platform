# Fuseki server runtime

Downloads the official Apache Fuseki distribution using the profile's version
and SHA512. Supply a Debian/Ubuntu Java 21 JDK base image pinned by digest via
`make images JAVA_BASE_IMAGE=...`; there is deliberately no unverified Java image
tag default. The image includes no import entrypoint. UID/GID 1000 owns the
runtime working directory; Kubernetes fsGroup grants the PVC permissions.

The final shell entrypoint uses `exec java -jar /opt/jena/fuseki-server.jar`, so
Java is PID 1 and receives SIGTERM. No lock files are deleted. `JAVA_TOOL_OPTIONS`
sets heap independently from Kubernetes memory limits. Config is mounted at
`/config/assembler.ttl`; data at `/fuseki/databases` by default. Runtime and tools
versions come from the same profile/build invocation. Build/startup, real storage
shutdown, JenaText and readiness acceptance are production gates, not claims
based solely on a rendered StatefulSet.
