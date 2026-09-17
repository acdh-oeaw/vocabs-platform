// njs shipped in the full nginx-unprivileged alpine image (not alpine-slim).
// Encode the raw URI as ONE query value, retaining existing percent escapes.
function queryValue(value) {
    return encodeURIComponent(value).replace(/[!'()*]/g, function (c) {
        return '%' + c.charCodeAt(0).toString(16).toUpperCase();
    });
}
function concept(r) {
    var original = r.variables.request_uri;
    var canonical = r.variables.vocabs_public_url + original.slice(1);
    r.return(Number(r.variables.vocabs_concept_status),
             r.variables.vocabs_public_url + 'entity?uri=' + queryValue(canonical));
}
function external(r) {
    // Match against raw request_uri, not nginx's decoded $uri. Escaped slashes,
    // UTF-8 and query delimiters must survive the redirect unchanged.
    var original = r.variables.request_uri;
    var prefix = '/' + r.variables.vocabs_external_prefix;
    if (original.slice(0, prefix.length) !== prefix) {
        r.return(400); // Ambiguous percent-encoded namespace spelling; never guess.
        return;
    }
    r.return(Number(r.variables.vocabs_external_status),
             r.variables.vocabs_external_target + original.slice(prefix.length));
}
export default {concept, external};
