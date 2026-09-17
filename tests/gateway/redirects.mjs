// Execute the exact shipped njs functions with an Nginx request stub.
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
const source=await readFile('chart/vocabs/files/gateway-redirects.js','utf8');
const {default:redirects}=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
function request(uri,vars={}) {
  return {variables:{request_uri:uri,vocabs_public_url:'https://vocabs.example.org/',vocabs_concept_status:'302',...vars},
          return(status,location){this.result={status,location};}};
}
for (const path of ['/archecategory/example','/iso6393/deu','/archecategory/a%2Fb','/archecategory/a%20b','/archecategory/ümlaut','/archecategory/a?format=ttl&x=1']) {
  const r=request(path); redirects.concept(r);
  assert.equal(r.result.status,302);
  const target=new URL(r.result.location);
  assert.equal(target.pathname,'/entity');
  assert.equal(target.searchParams.size,1);
  assert.equal(target.searchParams.get('uri'),'https://vocabs.example.org'+path);
}
let r=request('/archecategory/example');redirects.concept(r);
assert.equal(r.result.location,'https://vocabs.example.org/entity?uri=https%3A%2F%2Fvocabs.example.org%2Farchecategory%2Fexample');
for (const prefix of ['tadirah','invocation-type','bbt']) {
  for (const suffix of ['', '/', '/foo', '/a%2Fb?x=1&y=2', '?x=1']) {
    const r=request('/'+prefix+suffix,{vocabs_external_prefix:prefix,vocabs_external_target:'https://vocabs.dariah.eu/'+prefix,vocabs_external_status:'301'});
    redirects.external(r);assert.deepEqual(r.result,{status:301,location:'https://vocabs.dariah.eu/'+prefix+suffix});
  }
}
r=request('/%74adirah/foo',{vocabs_external_prefix:'tadirah',vocabs_external_target:'https://vocabs.dariah.eu/tadirah',vocabs_external_status:'301'});
redirects.external(r);assert.equal(r.result.status,400);
console.log('njs redirect logic: URI encoding, query isolation, Unicode and external suffix cases passed');
