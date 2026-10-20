# Mitchell Tech V120.2 — five distinct arithmetic cross-checks

The Bot Traffic bench packages five **nonrepeating** integer expressions drawn from its synthetic economics model (200 arrivals, fixed seed 7, adoption fractions 0%, 25%, 50%, 75%, 100%). They verify the arithmetic identity

`net_model_utility = accepted * 5 - registration_cost`

using the `window.MitchellTech.calculate(expression)` local browser API described by the separate [Mitchell Tech repository](https://github.com/mitchell-d00/Mitchell-Tech-V120.2-A-self-teaching-scientific-and-graphing-calculator-/blob/main/JAVASCRIPT-API.md).

The test builder checks all five expression strings are unique. **We have not executed these checks inside the actual Mitchell Tech browser origin in this release environment.** The scenario ledger reports them as `PENDING`, not passing. The Python reference expectations come from `economics_simulation`, not from independent observation of machine traffic.

## iPad workflow

1. In Bot Traffic → **Scenario ledger**, select **Copy calculator batch script**.
2. Open the Mitchell Tech public calculator in its own tab. In that page's JavaScript console, paste the script and run it. The script looks for the page-local `window.MitchellTech` API, calculates each expression, prints JSON and attempts to copy JSON to the clipboard.
3. Return to Bot Traffic. Paste the JSON into **Paste JSON output from Mitchell Tech** and select **Validate five calculator answers**.
4. Observe five per-scenario statuses. Export the test evidence JSON for your own records.

This is **operator-submitted** evidence, not authenticated external execution: copied JSON can be edited. Passing arithmetic tests does not validate the adoption economics beyond its fixed assumptions. Browsers cannot access each other's `localStorage` or page APIs merely by linking URLs.
