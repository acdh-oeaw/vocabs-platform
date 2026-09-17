# Backup and disaster recovery

The cluster already supplies Velero; this chart neither installs nor replaces it.
Blue/green PVC revisions provide operational deployment and fast rollback. Velero
backs up Kubernetes state and storage for disaster recovery. Immutable RDF dumps
plus versioned configuration and image profiles are the portable logical source
of truth. Prior revisions on the same storage cluster are not an off-site backup.

Storage snapshots of a running Jena database and its Lucene index need an
application-consistency plan. A crash-consistent snapshot is not proof that the
DB and index form a consistent pair. Coordinate with infrastructure maintainers
and test restore behavior. A future Velero procedure may quiesce traffic, stop
Fuseki gracefully, snapshot all required volumes, then restart and verify it.
No destructive or automatic backup hooks are installed here.

Maintain backups of namespace objects, ConfigMaps, external Secrets using the
cluster's secret policy, PVC contents, source dumps and the exact stack profile.
For recovery: restore into an isolated namespace with public ingress disabled;
verify claims and storage classes/CSI snapshot mappings; restore compatible
images/configuration; ensure no other JVM owns the DB; start one Fuseki replica;
check graphs, text search and Skosmos routes before enabling public traffic.
If physical restore is incompatible, rebuild from RDF into a new claim and index.
Document actual Velero CSI/file-system backup capabilities, RPO/RTO, retention,
backup encryption and a successful restore drill for each environment.
