# The registry

One entry per station. Sorted by callsign.

| Callsign | Identity hash | Date entered |
|---|---|---|
| KJ5FQT | `5bd78f7937f93fc57cf860e2a3244dc3` | 2026-11-16 |
| KJ5FQT/2 | `1e0c7c9c4b44f0f2a40d87aa9d9e2c16` | 2026-11-16 |
| KF0YRY | `43dea67e8b5fce996e906f9c94f47fcd` | 2026-11-16 |

*(Seed data migrated from the NomadNet registry. Entries and key material to be completed by the maintainer.)*

---

## Machine-readable copy

`registry.csv` is the canonical source: one row per station with the hash tied to the callsign.

---

## Getting your key

See [REGISTER.md](REGISTER.md) for the full procedure, the paths for each piece of software, and the one command that turns an identity file into hex.

---

## A note on what this table does and does not contain

The identity hash above is enough to *find* a station's traffic on the air. The key material needed to *read* it belongs with each entry and is published deliberately — see [PURPOSE.md](PURPOSE.md) for why, and [DECODE.md](DECODE.md) for the consequence that follows.

**Read [DECODE.md](DECODE.md) before registering.** A published key makes traffic readable and forgeable, and neither can be undone.

---

[Register a station](REGISTER.md) · [The mode](README.md) · [Decoding](DECODE.md) · [Ratchets](RATCHETS.md) · [Reasoning](PURPOSE.md)

**No warranty. Not legal advice. An unproven theory, offered for use and argument.**
