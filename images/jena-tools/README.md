# Offline Jena tools

`load.sh destination yourdatadump.rdf` preserves the old two-argument interface.
Set STORAGE_ENGINE from the profile, not by inspecting/guessing existing files.
The destination is a new `db` child of an empty candidate PVC; an existing path,
even empty, is rejected. The wrapper does not erase data or lock files. Loader
and RIOT failures propagate their exit codes, and partially loaded candidates
remain for investigation. The default workflow validates RDF and builds text.

Verified in Apache Jena 5.4.0: `riot`, `tdbloader`, `tdb1.xloader`,
`tdb2.tdbloader`, `tdb2.xloader`. This wrapper uses the simpler TDB1/TDB2 loaders;
it does not assume external-sort xloader prerequisites are installed. RIOT uses
`--validate`. Jena CLI scripts honor JAVA_TOOL_OPTIONS via the JVM.

JenaText is NOT in the core apache-jena archive. The tools image includes the
same-version Fuseki server archive's text classes; see Dockerfile and load.sh for
the explicit classpath. The Java indexer takes `--desc=assembler.ttl`, verified
against the tagged Jena source. There is no invented `textindexer` executable.
Assembler, storage type, graph mapping and label analyzers must match runtime.
Use the same `/fuseki/databases/db` and `/fuseki/databases/text` paths when supplying
an external assembler. No live runtime PVC is mounted in the Job.

For local loader-only tests, `BUILD_TEXT_INDEX=false` explicitly skips indexing.
For full indexing supply ASSEMBLER and TEXT_INDEX_DIR. A successful load is not
an acceptance result: validate graph counts and Skosmos search before activation.
Read `docs/imports.md` for Job lifecycle, resource sizing and rollback.

For local smoke testing, FUSEKI_JAR may point to an extracted same-version
Fuseki server JAR; the image defaults to `/opt/fuseki/fuseki-server.jar`. Missing
indexer JARs fail preflight before loading any RDF.
