import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

const source = readFileSync(
  new URL('../branding/custom-templates/html-head/40-acdh-navigation-config.twig', import.meta.url),
  'utf8',
).match(/<script>([\s\S]*?)<\/script>/)[1];

for (const [config, expected] of [
  [{editorUrl:'https://editor.example.org/', apiUrl:'https://api-dev.example.org/'}, true],
  [{}, false],
  [{apiUrl:'javascript:alert(1)'}, false],
  [{apiUrl:'https://user:pass@example.org/'}, false],
  [null, false],
]) {
  let ready;
  const editor = {href:'/de/about#editor', hidden:true};
  const api = {href:undefined, hidden:true};

  const fetch = async (url, options) => {
    assert.equal(url.href, 'https://vocabs.example.org/resource/acdh-navigation.json');
    assert.equal(options.cache, 'no-store');
    if (config === null) throw new Error('unavailable');
    return {ok:true, json:async()=>config};
  };

  vm.runInNewContext(source, {
    URL,
    fetch,
    document: {
      baseURI:'https://vocabs.example.org/',
      addEventListener(type, cb) {
        assert.equal(type, 'DOMContentLoaded');
        ready = cb;
      },
      querySelectorAll(selector) {
        return {
          '[data-acdh-editor]':[editor],
          '[data-acdh-api]':[api],
        }[selector];
      },
    },
  });

  await ready();

  if (expected) {
    assert.equal(editor.href, config.editorUrl);
    assert.equal(api.href, config.apiUrl);
    assert.equal(editor.hidden, false);
    assert.equal(api.hidden, false);
  } else {
    assert.equal(editor.href, '/de/about#editor');
    assert.equal(api.href, undefined);
    assert.equal(editor.hidden, true);
    assert.equal(api.hidden, true);
  }
}

console.log('Navigation config: About service links, missing config, unsafe schemes, credentials and fetch failure passed');
