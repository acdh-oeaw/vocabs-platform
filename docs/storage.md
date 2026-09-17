# Storage and retention

Prefer Ceph RBD (RWO, or RWOP where supported) for Jena/TDB databases. RBD provides
block storage and clearer attachment ownership than a shared filesystem. The
chart is provider agnostic: there is no hardcoded Ceph StorageClass. Verify the
CSI driver's filesystem locking, fsync, attach/detach, expansion and snapshot
behavior with Jena and your cluster. RWO permits multiple pods on the same node;
it is not a database writer lock. Never run two JVMs against one claim.

`data.activeClaim` is an explicit claim name in the release namespace. It may be
managed outside Helm or included in `data.managedClaims`. Candidate claims are
ordinary PVCs, too. Claims have mandatory retention and `helm.sh/resource-policy:
keep`; disabling retention fails rendering. Removing a managed entry or
uninstalling the release leaves the claim behind. Kept objects can become
orphaned from Helm, and reinstall/re-adoption may require operator reconciliation
of Helm ownership metadata. Keep an inventory; do not assume uninstall cleans
storage or that a PV's reclaim policy is a substitute for claim retention.

An empty `storageClassName` omits the field and uses the cluster default. `-`
renders an explicit empty string for pre-provisioned volumes. A nonempty name
selects that environment's class. Omit environment placeholders before actual
installation. PVC sizes are Kubernetes quantity strings, and claims cannot be
shrunk. Helm arrays replace rather than append: list all revisions you wish to
continue managing when overriding `managedClaims`.

Use an existing shared CephFS/RWX source claim for RDF dumps. It mounts read-only
at `/data` in the importer and never in Fuseki. Source and target must differ.
The target mount path is identical in importer and runtime; database files live
in its `db` child and text index in `text`. A new candidate must have neither.
Custom assemblers must use those same paths, dataset engine, and text fields.

Keep at least two prior accepted revisions or 14–30 days of rollback history,
adjusted for capacity and release frequency. This is guidance, not automated
cleanup. Explicit deletion requires verifying no active workload or import uses
the claim, the retention window has elapsed, and backup/rebuild sources exist.
Never delete old data as part of activation or automatically remove TDB locks.
