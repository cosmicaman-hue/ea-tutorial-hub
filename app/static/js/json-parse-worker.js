/**
 * Web Worker for offloading heavy JSON.parse() calls off the main thread.
 * The scoreboard data can be ~34 MB raw; parsing it on the main thread
 * blocks UI for 200-500 ms. This worker performs the parse in a
 * background thread and posts the deserialized object back.
 *
 * Usage (from main thread):
 *   const worker = new Worker('/static/js/json-parse-worker.js');
 *   worker.postMessage({ id: 'myParse', raw: largeJsonString });
 *   worker.onmessage = (e) => { const { id, data, error } = e.data; ... };
 */
self.onmessage = function (e) {
    const { id, raw } = e.data || {};
    try {
        const data = JSON.parse(raw);
        self.postMessage({ id, data });
    } catch (err) {
        self.postMessage({ id, error: err.message || String(err) });
    }
};
