import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
const source = readFileSync(new URL('../branding/custom-templates/html-head/30-acdh-landing-search.twig', import.meta.url), 'utf8').match(/<script>([\s\S]*?)<\/script>/)[1];
for (const landing of [true, false]) {
  let ready, moves = 0, logoMoves = 0;
  const classes = new Set(['collapse']);
  const bodyClasses = new Set(landing ? ['frontpage-logo'] : []);
  const headerbar = {};
  const logo = { parentElement: headerbar };
  const topbar = { insertBefore(node, sibling) {
    assert.equal(node, logo);
    assert.equal(sibling, nav);
    node.parentElement = this;
    logoMoves++;
  } };
  const nav = { parentElement: topbar };
  const mountedComponent = {}; // Must remain on the same node, not a clone.
  const bar = { mountedComponent, parentElement: null, classList: {
    remove(...names) { names.forEach(n => classes.delete(n)); },
    add(name) { classes.add(name); },
  } };
  const attributes = new Map([['aria-controls', 'global-search-bar'], ['data-bs-toggle', 'collapse']]);
  const toggle = { hidden: false, setAttribute(k, v) { attributes.set(k, v); }, removeAttribute(k) { attributes.delete(k); } };
  const target = { appendChild(node) { assert.equal(node, bar); node.parentElement = this; moves++; } };
  vm.runInNewContext(source, { document: {
    body: { classList: {
      contains(name) { return bodyClasses.has(name); },
      add(name) { bodyClasses.add(name); },
    } },
    addEventListener(name, callback) { assert.equal(name, 'DOMContentLoaded'); ready = callback; },
    getElementById(id) { return { 'topbar-nav': nav, 'acdh-landing-search': target, 'global-search-bar': bar, 'global-search-toggle': toggle }[id]; },
    querySelector(selector) {
      assert.equal(selector, '#headerbar-top-slot .acdh-header-logo');
      return logo.parentElement === headerbar ? logo : null;
    },
  } });
  ready(); ready();
  assert.equal(logoMoves, landing ? 1 : 0);
  assert.equal(logo.parentElement, landing ? topbar : headerbar);
  assert.equal(bodyClasses.has('acdh-logo-in-topbar'), landing);
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
console.log('Landing logo and search: original nodes, idempotent relocation, focus order, ARIA and non-landing behavior passed');
