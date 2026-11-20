# Decoding a captured transmission

The lookup chain, step by step.

This page describes how a third party who captures a transmission resolves it to a callsign and reads it. Nothing here is a new capability. It is the procedure the published key was always meant to enable.

---

## Overview

Five steps. Steps 1 and 2 need only the captured frame. Steps 3 and 4 need the registry. Step 5 is what you write down afterward.

1. Read the destination hash from the packet header.
2. Identify the delivery class from the header.
3. Look the hash up in the registry.
4. Decrypt, then attribute the author.
5. Record what was not obtained.

---

## Step 1 — read the destination hash

`Packet.pack()` writes the destination hash into the header in the clear. In the `HEADER_1` branch it is the only address field; in `HEADER_2` it follows the transport ID:

```python
self.header += self.destination.hash
# HEADER_2:
self.header += self.transport_id
self.header += self.destination.hash
```

This applies to announces and to opportunistic LXMF packets. The hash is

```
sha256(name_hash + identity.hash)[:16]
```

sixteen bytes, truncated from the identity.

---

## Step 2 — identify the delivery class

The destination type bits of the flags byte tell you what you are looking at:

| Type | Name | What it carries |
|---|---|---|
| `SINGLE` | Single destination | Announces, LXMF delivery |
| `PLAIN` | Plain destination | Unencrypted, rarely used |
| `GROUP` | Group | Shared-key |

For LXMF you want `SINGLE`. Anything else and the rest of this chain does not apply.

---

## Step 3 — look the hash up

Find the sixteen-byte hash in `REGISTRY.md`. One lookup returns:

- the callsign
- the identity public key
- the private key
- a validity window

This single step is what turns an opaque 16-byte address into something attributable and legible. It requires no cryptanalysis, no escrow breach, and no cooperation from the station. It requires only that the station published an entry.

---

## Step 4 — decrypt, then attribute

The published private key opens any payload sealed to that identity. Inside the plaintext the LXMF layout is:

```
[ destination_hash ][ source_hash ][ signature ][ payload ]
```

You have the destination hash from the header. The source hash tells you who sent it. The signature verifies against the sender's public key, which you also have from the registry.

**Do not read more into the signature than it can bear.** It verifies that the message was signed by the holder of the sender's private key. Since that key is published, it verifies that *someone* holding it signed — which is not the same as the station's operator. See the caveat below.

---

## Step 5 — record what was not obtained

The honest summary: the profile is fully legible to any third party who looks, and that legibility is total — **including the ability to forge**. Both were chosen.

A decode report that claims readability without noting forgeability is not a complete report.

---

## What stays closed

Two things resist the published key, and both matter.

**Link-session traffic stays closed.** NomadNet page fetches, `Link.request()` calls and anything carried as a Resource over an established link use a key derived from an ephemeral X25519 exchange. That key never passes through the registry. A listener who captured the session but not the handshake still cannot decrypt it. The identity key is not a skeleton key for recorded sessions.

**Ratchet-rotated traffic may stay closed.** A sender who rotated ratchets away from the published identity key produces packets the identity key does not open.

---

## The forgery problem

A published private key is compromised by definition. One consequence follows directly from the decode chain and deserves its own heading.

An observer holding the published private key can produce an LXMF message whose Ed25519 signature verifies against the published public key, **with any source hash they choose**. To the recipient, and to any later auditor, it is indistinguishable from a genuine message under that identity.

The profile gives away **authorship verification along with confidentiality**. Readability and forgeability are the same property seen from two sides: it is not merely that the key leaks, but that the same key which enables the transparency claim also destroys the only cryptographic means by which a recipient could have told a real message from a forged one.

---

## Mitigations

1. **Record publication time.** A forgery can be dated any time after publication, so the only defence is knowing when the key became public.
2. **Prefer link-based transfer for anything that needs provenance.** Session traffic is unforgeable by a key holder who was not in the handshake.
3. **Do not treat a signature as proof of authorship.** It is proof that the key holder signed, and the key holder is everyone.

---

[Register a station](REGISTER.md) · [The mode](README.md) · [Ratchets](RATCHETS.md) · [Reasoning](PURPOSE.md)

**No warranty. Not legal advice. An unproven theory, offered for use and argument.**
