# M73_RNS

**An operating mode for Reticulum on the amateur bands.**

> Looking for something specific: [Register a station](REGISTER.md) · [Registry](REGISTRY.md) · [Decoding](DECODE.md) · [Ratchets](RATCHETS.md) · [Reasoning](PURPOSE.md) · [Why no plaintext](WHY-NO-PLAINTEXT.md)

---
## Requirements

### 1. Interface file

The interface lives in its own repository: **https://github.com/smeshT/M73CallsignInterface.py**

Copy `M73CallsignInterface.py` from there into your Reticulum interfaces directory:

```
~/.reticulum/interfaces/M73CallsignInterface.py
```

You also need the stock `Modem73Interface.py` from https://github.com/RFnexus/modem73interface/blob/master/Modem73Interface.py in the same directory. 
The M73CallsignInterface subclasses the stock Modem73Interface not replaces it.

### 2. Turn ratchets off

A station that publishes its private key cannot ratchet, because a peer holding a cached ratchet will encrypt to a key your published key cannot open. See the ratchets documentation on the Reticulum Callsign Registry for the one-line change and the identity consequences.

This is a prerequisite, not an option.

### 3. Configure the interface

In `~/.reticulum/config`:

```ini
[[Modem73 Callsign]]
    type = M73CallsignInterface
    enabled = true
    envelope = true
    callsign = YOURCALL
    operator_log = ~/.reticulum/m73log
    target_host = 127.0.0.1
    target_port = 8001
    control_host = 127.0.0.1
    control_port = 8073
    mode = internal
    kiss_framing = true
    recursive_prs = no
    announces_from_internal = yes
    announces_to_internal = yes
```

**If you already have a `[[Modem73]]` block in that config, disable it.** Two blocks pointing at the same KISS and control ports will contend for the connection and neither will work.

### Notes on the config keys

- `callsign` — your station callsign. Validated at startup; the interface refuses to load if it is missing or malformed, rather than transmit a placeholder.
- `envelope` — `true` turns wrapping on. With `false` the interface behaves as the stock one.
- `strict` — defaults to `true`, logs a warning when frames arrive without an envelope. Noise only, not a failure.
- `operator_log` — Path to the station log written by the interface.---optional but recommended for the ham bands, this will supplement your operator log. 

### 4. Publish your Callsign and Reticulum Identity Private Key 


---

## Keeping the radio quiet until it is needed

A station with a radio interface and a faster connection to the rest of the network should not spend HF
time on lookups the fast link can do. Reticulum has a stock answer for this, and it is not an interface
mode switch.

### What generates traffic on HF

Two different things put path requests on the radio, and they need opposite treatment:

| Traffic | Origin | Want it? |
|---|---|---|
| A client radio asks for a destination it has no current path to | Arrives on the radio | **Yes.** This is the radio doing its job. A client radio rarely has an announce current enough to already be in your path table. |
| A local TCP client asks for an unknown destination, so Transport searches on every other interface | Generated locally, swept out | No. The fast link can answer this. |

### The settings

```ini
    mode = internal
    recursive_prs = yes
    egress_control = yes
    ec_pr_freq = 1
```

- `recursive_prs = yes` lets the interface carry path requests received from client radios. Leave it on.
  `internal` mode already enables recursive path requests, but stating it makes the intent visible.
- `egress_control = yes` turns on a hard outbound path request limit for this interface. Only discovery
  sweeps are affected; a request relayed on behalf of a client radio is never rate-limited by it.
- `ec_pr_freq = 1` allows one sweep per second at most. On a slow mode, `0.2` (one every five seconds)
  is kinder to the channel. Default is 5.

The limiter needs a few observations before it engages, so the first sweep or two after a quiet period
will still go out. That is the correct shape: it responds to sustained pressure, not to one request.

### Why not just disable discovery on the radio

Because the case you want to keep is the one that most often looks like the case you want to block.
A path request from a client radio and a sweep generated for a TCP client produce byte-identical frames.
At the level of the interface, they cannot be told apart: the difference lives in Transport's call path,
not in the packet. Any modem-side filter that drops one drops both.

The stock controls work upstream of that, where the distinction still exists, which is why this section
uses them.

## RX/TX Matrix for modified and unmodified stations

| Sender | Receiver | Result |
|---|---|---|
| Stock | Stock | Works. Normal Reticulum. |
| Stock | M73_RNS | **Works completely.** Frame passes through unchanged, logged as `rx_noenv`. |
| M73_RNS | Stock | **Broken.** Prefix is added and never removed. Peer logs a protocol violation. |
| M73_RNS | M73_RNS | Works. Full operation. |

Adopting this does not cut you off.** An M73_RNS station receives from every stock station on the network with no loss at all. You can turn this on and keep working with everyone.

...but your own transmissions are only readable by other stations running the mode.** A stock peer receives your frames, attributes them to your callsign, and then discards them, because the frame no longer starts with a valid Reticulum header.



---

## Verifying it works

The interface writes a log you can read while it runs. You can see this in Modem73 under the 'Utils' tab. There you will see a log like;
```
01:57:42 <- NOCALL: <followed by gibberish>
```
The gibberish is the RNS packet contents but transformed and mangled. You cannot decode from this. The RNS packet is still sent over KISS for normal decode.

If you set a path in the [[M73CallsignInterface]] - `operator_log` the following data will be shown there;

```
2026-11-19T14:42:55Z   tx         <your-callsign>       194B
2026-11-19T16:53:47Z   rx         <other's- callsign>   183B
2026-11-19T16:54:01Z   rx_noenv   -                     241B
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

The difference is the prefix: four bytes for `M73:`, one for the colon, and the callsign length. `NOCALL/2` is eight characters, so 13 bytes. `NOCALL` is six, so 11B.

**The overhead formula is `len(callsign) + 5`.**

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

**No warranty. Not legal advice. Offered for use and argument.**

One reading of the rules, offered for testing. The identification argument is untested. If you transmit on the amateur bands you are the control operator and the decision is yours.

---

## The rest of the documentation

| Page | What is in it |
|---|---|
| [REGISTER.md](REGISTER.md) | How to get your station listed, and what publishing your key costs you |
| [REGISTRY.md](REGISTRY.md) | The list of stations. Also [registry.csv](registry.csv) for machines |
| [DECODE.md](DECODE.md) | How a third party reads a captured transmission, step by step |
| [RATCHETS.md](RATCHETS.md) | The one-line patch, why the new identity is not optional, how to check any station |
| [PURPOSE.md](PURPOSE.md) | Why publish a key at all. The argument, and its opponents |
| [WHY-NO-PLAINTEXT.md](WHY-NO-PLAINTEXT.md) | Why Reticulum cannot simply send plaintext |

---

## Licence

MIT. See `LICENSE`.
