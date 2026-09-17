# Stack versioning

`compatibility.yaml` is the registry. The chart reads it with `.Files.Get` and
`fromYaml`, rejecting unknown profiles. Skosmos and Jena image tags combine the
resolved component version with a shared ACDH image revision. Runtime and tools
use the same Jena version; the build script supplies it and verified SHA512
archive hashes from the registry. Import pods also verify the image's embedded
JENA_VERSION against the selected profile. Independent Jena version values are
not supported.

`2026.09.0-dev` is a development candidate, not a tested production declaration.
Skosmos v3.3's Docker Compose specifies Jena 5.4.0, but its reference assembler
uses TDB2. This repository deliberately starts with requested TDB1 and JenaText;
that difference needs integration testing. Jena 5.4.0 is not preselected as the
final production version.

New Skosmos/Jena release → candidate profile → build candidate images → integration
tests → representative import → JenaText/search tests → staging → record ACDH
acceptance evidence → mark ACDH-tested → publish a new stack/chart version.
Maintain old profiles and image artifacts for supported rollbacks. Do not adopt
a new Jena simply because it exists. Record RDF fixture checksums, graph counts,
search results, image digests, cluster/storage test conditions and approvers.

For testing only:

```yaml
compatibility:
  allowUnsupported: true
  overrides:
    jenaVersion: "5.5.0"
    storageEngine: TDB2
```

This resolves BOTH Jena tags to the overridden version. Build matching test
images separately with verified checksums; this example does not claim those
images exist or that this combination works. A manual runtime image tag must
match the importer tag. This escape hatch never disables PVC safety, retention,
internal services or the single-replica rule. Changing engine or Jena requires a
fresh RDF import, never in-place format conversion. Custom assemblers and image
contents remain operator responsibilities; Helm cannot inspect their semantics.

Varnish/Swagger values are verified against the selected profile. New supported
profiles must update these dependency image defaults in the same chart release.
Production promotion additionally requires immutable registry tags or digests,
image scanning, SBOM/provenance publication and a tested disaster-recovery plan.
