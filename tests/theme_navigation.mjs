// Exercise the actual slot script without a browser or copied implementation.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
const template = readFileSync(new URL('../branding/custom-templates/html-head/20-acdh-navigation.twig', import.meta.url), 'utf8');
const script = template.match(/<script>([\s\S]*?)<\/script>/)[1];
for (const path of ['/en/', '/example/en/page/foo?clang=de', '/en/about#old']) {
  let ready, click, focused = false, scrolled = false, visible = false;
  const main = {
    id: 'main-container-row',
    focus() { focused = true; },
    scrollIntoView() { scrolled = true; },
  };
  const skip = {
    classList: { replace(from, to) {
      assert.equal(from, 'visually-hidden');
      assert.equal(to, 'visually-hidden-focusable');
      visible = true;
    } },
    addEventListener(type, callback) { assert.equal(type, 'click'); click = callback; },
  };
  vm.runInNewContext(script, {
    URL, window: { location: { href: `https://vocabs.example.org${path}` } },
    document: {
      addEventListener(type, callback) { assert.equal(type, 'DOMContentLoaded'); ready = callback; },
      getElementById(id) { return { skiptocontent: skip, 'main-container-row': main }[id]; },
    },
  });
  ready();
  const expected = new URL(`https://vocabs.example.org${path}`);
  expected.hash = main.id;
  assert.equal(skip.href, expected.href);
  assert.ok(visible);
  assert.equal(focused, false, 'Loading the page must not steal focus');
  let prevented = false;
  click({ preventDefault() { prevented = true; } });
  assert.ok(prevented && focused && scrolled, 'Skip activation focuses and scrolls to main');
}
for (const missing of ['skiptocontent', 'main-container-row']) {
  vm.runInNewContext(script, {
    document: {
      addEventListener(type, callback) { callback(); },
      getElementById(id) { return id === missing ? null : {}; },
    },
  });
}
console.log('Theme navigation: current-page targets, visible skip link, activation and missing elements passed');
