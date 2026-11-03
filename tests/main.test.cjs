const { test } = require('node:test');
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { join } = require('node:path');
const vm = require('node:vm');

const source = readFileSync(join(__dirname, '../static/main.js'), 'utf8');

function element() {
    return {
        style: { setProperty() {} }, dataset: {}, children: [], handlers: {}, attrs: {},
        clientWidth: 800, clientHeight: 600,
        classList: { add() {}, remove() {} },
        addEventListener(name, handler) { this.handlers[name] = handler; },
        setAttribute(name, value) { this.attrs[name] = value; },
        removeAttribute() {},
        appendChild(child) { this.children.push(child); },
        querySelector() { return null; },
        querySelectorAll() { return []; },
        cloneNode() { return element(); },
        getBoundingClientRect() { return { left: 0, top: 0 }; },
    };
}

function run({ reducedMotion = false, finePointer = true, libraries = false } = {}) {
    const hero = element();
    const card = element();
    const verb = element();
    const frames = new Map();
    const timers = [];
    let nextFrame = 0;
    let focused = false;
    const nodes = { '.hero': hero, '.hero-card': card, '[data-tech-verb]': verb,
        '[data-error-summary]': { focus() { focused = true; } } };
    const document = {
        documentElement: element(),
        querySelector(selector) { return nodes[selector] || null; },
        querySelectorAll() { return []; },
        createElement: element,
        addEventListener(name, handler) { if (name === 'DOMContentLoaded') handler(); },
    };
    const window = {
        matchMedia(query) { return { matches: query.includes('reduced-motion') ? reducedMotion : finePointer }; },
        setInterval(handler) { timers.push(handler); },
        setTimeout() {},
    };
    if (libraries) {
        window.Lenis = class { constructor() { throw new Error('Smooth scrolling must stay disabled'); } };
        window.gsap = { registerPlugin() { throw new Error('Animation must stay disabled'); } };
        window.ScrollTrigger = {};
    }
    vm.runInNewContext(source, { document, window,
        requestAnimationFrame(callback) { frames.set(++nextFrame, callback); return nextFrame; },
        setTimeout() { return 1; }, clearTimeout() {},
    });
    return { hero, frames, timers, focused,
        tick() {
            const [id, callback] = frames.entries().next().value;
            frames.delete(id);
            callback();
        },
    };
}

test('reduced motion disables scrolling, reveals, rotating text, and the lens', () => {
    const page = run({ reducedMotion: true, libraries: true });
    assert.equal(page.hero.children.length, 0);
    assert.equal(page.frames.size, 0);
    assert.equal(page.timers.length, 0);
    assert.equal(page.focused, true);
});

test('the decorative lens cannot receive focus and does no work until the pointer moves', () => {
    const page = run();
    const lens = page.hero.children[0];
    assert.equal(lens.inert, true);
    assert.equal(lens.attrs['aria-hidden'], 'true');
    assert.equal(lens.style.opacity, 0);
    assert.equal(page.frames.size, 0);
    page.hero.handlers.pointermove({ clientX: 20, clientY: 30 });
    page.tick();
    assert.equal(lens.style.opacity, 1);
    page.hero.handlers.pointerleave();
    page.tick();
    assert.equal(lens.style.opacity, 0);
    assert.equal(page.frames.size, 0);
});

test('touch devices skip the decorative lens, and form errors focus without GSAP', () => {
    const page = run({ finePointer: false });
    assert.equal(page.hero.children.length, 0);
    assert.equal(page.focused, true);
});
