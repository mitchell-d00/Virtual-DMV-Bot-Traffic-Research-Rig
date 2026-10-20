# One HTML / Python / JavaScript API

`index.html` is generated from `browser/template.html`, `browser/style.css`, `browser/client.js`, and the canonical Python under `src/virtual_dmv/`. Do not edit only the generated page; rebuild with `python3 tools/build_browser.py` and commit the resulting source pins.

## Browser requirement

The source bundle itself is a single file. The interpreter **is not**: the app loads pinned `https://cdn.jsdelivr.net/pyodide/v0.27.7/full/pyodide.js` and its accompanying WebAssembly Python assets. A successful initial load requires internet access and a browser supporting WebAssembly; later offline reload is not guaranteed. No additional data service or paid LLM is used. The app runs Python code in the page's runtime after loading. Serving from GitHub Pages/HTTPS is recommended for iPad use.

## Local API

```js
await window.VirtualDMV.ready();
let audit=await window.VirtualDMV.command('audit');
let issue=await window.VirtualDMV.command('issue',{owner:'alice',role:'agentic',plate_id:'VDMV-EXTRA-03'});
let response=await window.VirtualDMV.command('request',{plate_id:'VDMV-EXTRA-03',owner:'alice',resource:'open-archive',action:'summarize'});
let checks=await window.VirtualDMV.command('bench');
console.log(response.allow, response.reason, response.receipt_hash);
```

The browser API accesses one mutable local demo state, saved in localStorage as `virtual-dmv-lab-state-v1` when available. Export/import copies the entire state **including demo secrets**. A separate connected AI application must operate the browser page with its own agent stack; simply knowing the URL cannot remotely call a particular user's browser state.

## Pure Python command bridge

```python
from virtual_dmv.engine import bridge
import json
print(json.loads(bridge(json.dumps({'op':'bench'})))['result'])
```

Errors return `{ok:false,error:...}`; normal calls return `{ok:true,state:...,result:...}`. `ok:true` means a command completed; it does *not* mean access was permitted. Inspect `result.allow` and `result.reason`. All test policies are local inventions.
