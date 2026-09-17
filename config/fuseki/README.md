# Fuseki assembler

`assembler.ttl.example` is the default TDB1 read-only query/JenaText model, without
Helm expressions. The chart generates the same model from the selected profile;
TDB2 testing profiles change both the assembler and loader. The text index maps
preferred, alternative, hidden labels and notation using lower-case keyword
analyzers, matching the upstream Skosmos-oriented fields. Validate real search
behavior, including multi-word queries, before accepting this configuration.

Production can supply `fuseki.config.existingConfigMap` containing assembler.ttl.
It is mounted into both server and importer, with the same database/index paths.
Change `fuseki.config.revision` to roll the server after external config changes.
Custom assemblers must agree with the profile engine, data directory and importer
text index directory. The chart cannot inspect an external ConfigMap at render
time. Enabling write endpoints or changing paths requires a separate security
and operational review; the supplied service is query-only.

The default assembler keeps `unionDefaultGraph false`: Jena's union graph excludes
the physical default graph, so enabling it would hide a Turtle/RDF/XML import
from queries without GRAPH clauses. For named-graph sources, configure explicit
vocabulary sparqlGraph values; enable union semantics only after testing the
intended dataset layout.
