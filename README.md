# M73_RNS

**An operating mode for Reticulum on the amateur bands, with the station callsign carried in every frame.**

---

## Why this exists

Reticulum transmits frames with no station identification inside them. On most transports that does not matter, because the modem puts the callsign in the waveform. On the slow modes it does matter, because the modem does not.

Verified from Modem73's source, the encoder dispatch is:

| `modem_type` | Encoder call | Receives `call_sign`? |
|---|---|---|
| 1 — MFSK | `mfsk_encoder_->encode(framed, size, center_freq, mfsk_mode)` | **No** |
| 2 — RDM / Robust | `robust_encoder_->encode(framed, size, center_freq, robust_mode)` | **No** |
| 0 — OFDM and others | `encoder_->encode(..., call_sign, oper_mode, postamble)` | **Yes** |

So a stock station sending Reticulum over **RDM-300, RDM-600 or MFSK** transmits frames that carry no station identification at all. That is not a setting anyone chose; it is how those encoders are written.

M73_RNS closes that gap by prepending a plain-text callsign to every frame:

```
M73:KJ5FQT:<the original frame>
```

Eleven bytes for a six-character callsign. ASCII, unencrypted, visible to anyone listening.

**The purpose is station identification under 47 CFR §97.119.** Not concealment, and not transparency. The mode turns a transmission that was previously anonymous into one that carries a station's identity.

---

## What works, and what does not

This is the part nobody tells you, so it is first.

| Sender | Receiver | Result |
|---|---|---|
| Stock | Stock | Works. Normal Reticulum. |
| Stock | M73_RNS | **Works completely.** Frame passes through unchanged, logged as `rx_noenv`. |
| M73_RNS | Stock | **Broken.** Prefix is added and never removed. Peer logs a protocol violation. |
| M73_RNS | M73_RNS | Works. Full operation. |

**The good news: adopting this does not cut you off.** An M73_RNS station receives from every stock station on the network with no loss at all. You can turn this on and keep working with everyone.

**The bad news: your own transmissions are only readable by other stations running the mode.** A stock peer receives your frames, attributes them to your callsign, and then discards them, because the frame no longer starts with a valid Reticulum header.

### The failure is not silent

It would be nicer if it were. A stock station receiving your wrapped frame does not quietly discard it. It parses it as a malformed announce, fails signature verification, and writes this to its log:

```
Received invalid announce for <hash>: Invalid signature.
Protocol violation on TCPInterface[Modem73/...]
```

**To that station you look like a spoofing attempt**, not like a station running an unfamiliar mode. That is a real cost of adopting this. If you are transmitting to a network you do not own, decide about it before you start.

---

## Installation

### 1. Place the interface file

Copy `M73CallsignInterface.py` into your Reticulum interfaces directory:

```
~/.reticulum/interfaces/M73CallsignInterface.py
```

The filename **must** be exactly `M73CallsignInterface.py`. Reticulum derives the file to load from
the `type` value in your config, so `type = M73CallsignInterface` looks for a file of precisely that
name.

There are two different ways this goes wrong, and they behave very differently:

| Mistake | What you see |
|---|---|
| `type` value does not match the filename | **Nothing.** Reticulum starts normally, the interface is simply absent, and no error is logged. |
| The file is present but fails to load | `External interface initialisation failed` with a traceback pointing into `Reticulum.py` |

The first is the dangerous one. A dotted module path such as `type = m73.M73CallsignInterface` also
lands here: Reticulum does not treat it as a module, it looks for a *file* with that literal name,
finds none, and carries on silently. If your interface seems not to exist, check that the `type`
value and the filename are character-for-character identical before looking anywhere else.

**You do not need to download anything else.** `M73CallsignInterface.py` subclasses the stock
`Modem73Interface`, which is already present in `~/.reticulum/interfaces/` on any machine that has
been running Modem73. Leave it where it is — do not delete or rename it. The import would fail
without it, and Reticulum would report the failure as `External interface initialisation failed`
with a traceback pointing into `Reticulum.py` rather than at this file.

One consequence worth knowing: this interface inherits from whatever copy of `Modem73Interface.py`
you have installed. It relies on several of that class's internal attributes (`_short_mtu`,
`_short_policy`, `_handshake_x2`, `_proof_x2`). They are stable, but they are not a published
interface, so a future change to the stock file could break this one. If you see unexpected
behaviour after updating Modem73, that is the first thing to check.

### 2. Turn ratchets off

A station that publishes its private key cannot afford ratchets, because a peer holding a cached ratchet will encrypt to a key your published key cannot open. See the ratchets documentation on the Reticulum Callsign Registry for the one-line change and the identity consequences.

This is a prerequisite, not an option.

### 3. Configure the interface

In `~/.reticulum/config`:

```ini
[[Modem73 Callsign]]
    type = M73CallsignInterface
    enabled = true
    envelope = true
    callsign = YOURCALL
    operator_log = ~/.reticulum/operator.log
    target_host = 127.0.0.1
    target_port = 8002
    control_host = 127.0.0.1
    control_port = 8073
    mode = internal
    kiss_framing = true
    recursive_prs = no
    announces_from_internal = yes
    announces_to_internal = yes
```

**If you already have a `[[Modem73]]` block in that config, disable it.** Two blocks pointing at ports 8002 and 8073 will contend for the connection and neither will work.

### Notes on the config keys

- `callsign` — your station callsign. Validated at startup; the interface refuses to load if it is missing or malformed, rather than transmit a placeholder.
- `envelope` — `true` turns wrapping on. With `false` the interface behaves as the stock one.
- `strict` — defaults to `true`, logs a warning when frames arrive without an envelope. Noise only, not a failure.
- `operator_log` — optional. Path to the station log written by the interface.

---

## Verifying it works

The interface writes a log you can read while it runs:

```
2026-11-19T14:42:55Z   tx         KJ5FQT     194B
2026-11-19T16:53:47Z   rx         KF0YRY/2   183B
2026-11-19T16:54:01Z   rx_noenv   -          241B
```

- A `tx` line means your own transmission went out with your callsign on it.
- An `rx` line means you received an identified frame from another station running the mode.
- An `rx_noenv` line means you received a normal frame from a station not running it. **This is not an error.**

No message content is ever written to this log. Timestamp, direction, callsign and byte count only.

---

## The numbers, from real transmissions

Measured between two stations over a day of ordinary operation. Every frame reconciled:

| Sent | Received | Difference |
|---|---|---|
| 209 B | 196 B | 13 B |
| 270 B | 257 B | 13 B |
| 221 B | 208 B | 13 B |
| 194 B | 183 B | 11 B |

The difference is the prefix: four bytes for `M73:`, one for the colon, and the callsign length. `KJ5FQT/2` is eight characters, so 13 bytes. `KJ5FQT` is six, so 11.

**The overhead formula is `len(callsign) + 5`.**

If your own numbers do not reconcile that way, something is wrong.

---

## What this does not do

- **It does not make your traffic readable.** It makes it attributable. Reading it requires the published key and ratchets turned off, which are separate things.
- **It does not make the operation lawful.** It satisfies the identification obligation on modes that cannot otherwise carry identification. That is a narrower and more defensible claim than the one people usually make, but it is still a claim, not a ruling.
- **It does not work to stock stations.** See the table above.
- **It does not provide forward secrecy.** That comes from the ratchet change, not from this interface.

---

## Should you run it?

Run it if you transmit Reticulum on RDM-300, RDM-600 or MFSK and you want your frames to carry your callsign. The identification benefit is real and it is not available any other way.

Run it if you are willing to accept that stock stations will log your transmissions as protocol violations.

Do not run it expecting it to make anything lawful. It does not.

Do not run it on a network you do not own without telling the other operators first. They will see errors and think something is wrong.

---

## Implementation notes

The interface subclasses `Modem73Interface` and touches only three methods:

| Method | Purpose |
|---|---|
| `__init__` | Reads `callsign`, `envelope`, `strict`, `operator_log`; validates the callsign at construction |
| `process_outgoing` | Prepends the envelope, after handshake/proof classification |
| `process_incoming` | Strips the envelope, counts rejects, writes the operator log |

Everything else — the control port, mode-aware bitrate, short frames, CSMA accounting — is inherited unchanged. The stock interface remains untouched and remains usable.

### Two things that will bite anyone modifying this

**Reticulum `exec`s external interface files; it does not import them.** `__file__` is undefined inside the file, only `Interface` and `RNS` are injected, and the file must bind a global named `interface_class`. Any path built from `__file__` raises `NameError` at load and the interface is dropped with a traceback pointing at `Reticulum.py`, not at your file.

**Classification must happen before wrapping.** `_is_handshake()` and `_is_proof()` read Reticulum header bytes at fixed offsets. Prepending the envelope shifts every offset, which silently disables `handshake_x2` and `proof_x2`. The implementation classifies the raw frame, then applies the copy count to the wrapped bytes.

---

## Status

- Verified on air, both directions, across multiple payload sizes.
- Verified that stock receivers attribute the frame but reject it, as documented above.
- Not yet verified: stock sender to M73_RNS receiver over the air (behaviour is implemented and unit-tested).

---

## Disclaimer

**No warranty. Not legal advice. An unproven theory, offered for use and argument.**

One reading of the rules, offered for testing. The identification argument is untested. If you transmit on the amateur bands you are the control operator and the decision is yours.

---

## Licence

MIT. See `LICENSE`.
