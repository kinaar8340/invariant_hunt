# Milestone: Expanded multi-event Gate P + PE posterior draws

**Commands:**
```bash
python scripts/premerger_expand_events.py --plot --n-draws 10
python scripts/premerger_mass_scale.py --events GW150914,GW170608,GW170814,GW170818
```

## Expanded multi-event (7 GWTC-1 BBHs, H1+L1)

| Event | M_f | α_hat | Δχ² | Gate P | Notes |
|-------|-----|-------|-----|--------|-------|
| GW150914 | 63.1 | +6.93e-5 | 30.4 | **PASS** | H1-driven |
| GW170104 | 48.9 | +1.13e-4 | 27.3 | fail | H1/L1 opposite signs |
| GW151226 | 20.5 | −1.20e-4 | 339 | fail | H1/L1 opposite signs |
| **GW170608** | 17.8 | **+1.04e-4** | 1316 | **PASS** | Both det same sign |
| **GW170814** | 53.2 | **+7.45e-5** | 16.0 | **PASS** | Both det same sign |
| **GW170818** | 59.4 | **+5.49e-4** | 279 | **PASS** | Both det same sign |
| GW170823 | 65.4 | −4.34e-4 | 172 | fail | H1/L1 opposite signs |

**Gate P pass: 4/7**  
**Gate P-D (≥2 pass, same sign): PASS**  
(passing set: GW150914, GW170608, GW170814, GW170818 — all **positive** α)

### Caveats (do not over-claim)

1. Three events still fail on **detector sign consistency** despite large Δχ² → residual systematics remain common.  
2. GW170608 / GW170818 Δχ² are **very large** — could include PE mismatch; needs PE-draw checks per event.  
3. α magnitudes span ~7e-5 to 5e-4 (factor ~8) — not yet a tight universal coupling.  
4. No form tweaks applied; this is still the original \(\Delta\phi=\alpha W_g\Phi_{\mathrm{orb}}\cos\phi_b\).

## PE posterior draws (GW150914, n=10)

| Metric | Value |
|--------|-------|
| Gate P pass | **9/10** |
| Median α (all draws) | **+7.88e-5** |
| Sign majority | **100% positive** among passes |
| One fail | draw with lighter m1+m2 (Δχ²=6.2, just below / weak) |

**Conclusion:** The GW150914 excess is **not an artifact of PE medians** — it persists across random posterior draws with stable sign.

## Mass scaling (passers only)

Re-run `premerger_mass_scale.py` on the four Gate-P passers for exploratory β consistency (see JSON if generated).

## Updated gate status

| Gate | Status |
|------|--------|
| B-P (injections, GW150914) | Pass |
| PE approximant robust (GW150914) | Pass (provisional) |
| PE posterior draws (GW150914) | **9/10 pass** |
| P-D multi-event (expanded) | **PASS** (4/7, same + sign) |

**Still not a discovery claim.** It is the first time multi-event sign-consistent Gate P clears under pre-registered rules. Required follow-ups: PE draws on GW170608/814/818, injection recovery on at least one more event, and scrutiny of high-Δχ² light systems.
