# Migration, one namespace at a time

1. Inventory the existing namespace and responsible maintainers.
2. Record hostname, canonical URI behavior, Skosmos config, original RDF sources,
   graph names, Jena version and TDB engine, JenaText analyzer/index configuration,
   PVC usage, resource peaks, ACDH theme/plugin differences and proxy/redirect rules.
3. Build reviewed images and deploy the chart in parallel, using an isolated
   namespace/hostname and no production traffic. Verify external ConfigMaps point
   to the new Vinyl Cache service. Keep the original deployment intact.
4. Create a new candidate block-storage PVC using the environment's RBD class.
5. Import the original immutable RDF dump with the selected Jena tools version.
6. Build a fresh JenaText index with matching engine, graph and analyzer settings.
7. Run the compatibility checklist, compare counts and representative multilingual
   results to production, and test shutdown/startup, backup restore and rollback.
8. Coordinate a brief traffic cutover/maintenance window. Switch ingress/DNS after
   the new stack and cache are ready; preserve concept URI and redirect behavior.
9. Keep the previous deployment, configuration, images and data for rollback,
   with a documented retention window and a tested reverse traffic switch.
10. Migrate the next namespace only after the current one is stable.

Do not copy an old TDB1 database into an incompatible TDB2 runtime. RDF is the
portable source of truth. Prefer fresh imports even for version upgrades unless
physical compatibility is explicitly established and tested. ACDH-specific theme
and plugin changes move into `branding/`; do not fork the full upstream source.
