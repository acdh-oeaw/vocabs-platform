import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
const source = readFileSync(new URL('../branding/custom-templates/html-head/30-acdh-landing-search.twig', import.meta.url), 'utf8').match(/<script>([\s\S]*?)<\/script>/)[1];
for (const landing of [true, false]) {
  let ready, moves = 0;
  const classes = new Set(['collapse']);
  const mountedComponent = {}; // Must remain on the same node, not a clone.
  const bar = { mountedComponent, parentElement: null, classList: {
    remove(...names) { names.forEach(n => classes.delete(n)); },
    add(name) { classes.add(name); },
  } };
  const attributes = new Map([['aria-controls', 'global-search-bar'], ['data-bs-toggle', 'collapse']]);
  const toggle = { hidden: false, setAttribute(k, v) { attributes.set(k, v); }, removeAttribute(k) { attributes.delete(k); } };
  const target = { appendChild(node) { assert.equal(node, bar); node.parentElement = this; moves++; } };
  vm.runInNewContext(source, { document: {
    body: { classList: { contains(name) { assert.equal(name, 'frontpage-logo'); return landing; } } },
    addEventListener(name, callback) { assert.equal(name, 'DOMContentLoaded'); ready = callback; },
    getElementById(id) { return { 'acdh-landing-search': target, 'global-search-bar': bar, 'global-search-toggle': toggle }[id]; },
  } });
  ready(); ready();
  assert.equal(moves, landing ? 1 : 0);
  assert.equal(bar.mountedComponent, mountedComponent);
  assert.equal(toggle.hidden, landing);
  assert.equal(classes.has('collapse'), !landing);
  assert.equal(classes.has('show'), landing);
  assert.equal(attributes.get('aria-controls'), 'global-search-bar');
  if (landing) {
    assert.equal(attributes.get('aria-expanded'), 'true');
    assert.equal(attributes.has('data-bs-toggle'), false);
  } else assert.equal(attributes.get('data-bs-toggle'), 'collapse');
}
console.log('Landing search: same node, idempotent relocation, ARIA, no focus calls and non-landing behavior passed');
