# Ratchets: a fixable problem

A station that publishes its private key can still be unreadable. This page explains why, and what to do about it.

**Short version: turn ratchets off, then create a new identity.**

---

## The problem

LXMF rotates keys on the receiving side. These are called **ratchets**. When a ratchet is active, a sender does *not* encrypt to the published identity key. It encrypts to a key derived on the receiver's side.

The published private key is the **base** key. Reticulum tries stored ratchets first, and only falls back to the base key when there is nothing else to try.

So a peer that holds a cached ratchet for your station will encrypt to it, and **your published key will not open the message**.

Nothing about this is a bug in publishing. It is ratchets doing exactly what they were designed to do, defeating exactly the property we want.

---

## The fix

### 1. Disable ratchets

Find the line in `LXMF/LXMRouter.py` that calls `enable_ratchets` and comment it out. There is one, at line 423, and it looks like this:

```python
    delivery_destination.enable_ratchets(
        os.path.join(self.storagepath, "ratchets")
    )
```

Put a `#` at the start of each line. Save.

**Patch the right installation.** A machine can have several LXMF copies. Find out which one your software actually imports before you edit:

```bash
ps aux | grep -i meshchat
```

The binary path tells you the venv. On a MeshChatX host that is usually `~/.local/pipx/venvs/reticulum-meshchatx/`, **not** `~/.local/pipx/venvs/lxmf/`. Editing the wrong one looks identical to "the patch did not stick".

### 2. Create a brand new identity

This is the step people skip, and it is the step that matters.

### 3. Announce it, then publish it

A new identity is readable with its published key from its very first announce.

---

## Why the new identity is not optional

You might expect that disabling ratchets is enough. It is not.

Every peer that heard your station while it was ratcheting **stored that ratchet** and will keep it for about 30 days. Disabling ratchets on your side does not reach into anyone else's storage and delete it. Those peers will keep encrypting to the old ratchet, and your key will keep failing.

A **new identity has never announced a ratchet**, so there is nothing stored anywhere to go stale. The problem does not exist for it, from the first minute.

This is why the order matters: **patch first, then create the identity**. Do it the other way round and you get a new identity that has already ratcheted, and you are back where you started.

> An old identity that has been seen by other stations cannot be repaired. Retire it and start a new one. That is the whole cost.

---

## How to check any station

Request its announce and look at the `context_flag`:

```
  0   no ratchet, the published key will work
  1   a ratchet is active, the published key may fail
```

A ratcheted announce is also exactly **32 bytes longer** than a bare one, which confirms it if you can measure the packet.

Do **not** rely on the station's own `latest_ratchet_id` field. It reads empty on an idle destination even when ratchets are enabled.

---

## It works: three installs, tested

The same one-line change was applied to three separate installs, each with a fresh identity created afterwards, and each verified by taking the published key, building a message, and decrypting what came out.

**Linux, Raspberry Pi** — two Raspberry Pi stations running MeshChatX under pipx, Python 3.11. Same Python file, same line in both. Both announce without a ratchet, both decrypt with the published key, both returned delivery proofs.

**Linux, cross-check** — the same sender that failed against the old sbitx identity succeeded against the new one twenty minutes later. Same code, same network, only the identity and the patch changed.

**Android, Columba** — Columba runs its LXMF stack in Python, not Kotlin, so the same line lives in the same file. The APK was rebuilt with that one line commented out, installed on a test phone, and verified on the device:

```
  identity announced        no ratchet
  outgoing packet           ratchet_id None (base key)
  payload                   still encrypted
  delivery                  DELIVERED, proof returned
```

The message displays in the app. The station is readable with its published key, and its traffic is still encrypted in transit.

> Columba is an unreleased test build. The released app still ratchets.
>
> MeshChatX on Linux needs the same one-line edit by hand.

---

## What this means for the profile

The transparency profile is supposed to make a station's traffic readable by anyone who fetches the registry. Ratchets are the one mechanism that breaks that promise without anyone noticing.

Turning them off costs nothing the profile wanted. Ratchets give forward secrecy to a receiver that publishes nothing. A station that has already published its key has given that up deliberately. Ratchets on top of a published key protect nothing and silently defeat the whole point.

**Turn them off, start a new identity, publish that.**

---

[Register a station](REGISTER.md) · [The mode](README.md) · [Decoding](DECODE.md) · [Reasoning](PURPOSE.md)

**No warranty. Not legal advice. An unproven theory, offered for use and argument.**
