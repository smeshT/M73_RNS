# Why Reticulum cannot simply send plaintext

A question people ask first, and the answer shapes everything else on this site.

---

## The short version

Reticulum has no unencrypted mode. Not as a policy, not as a default — as an architectural fact. Encryption is not a feature applied to the traffic; it is how destinations are addressed.

---

## Destinations *are* hashes

A Reticulum destination is not an address like an IP address. It is a truncated hash of a public key:

```
destination_hash = sha256(name_hash + identity.hash)[:16]
```

You cannot send to a destination without knowing the key that produces it, and you cannot route without the hash. There is no namespace where a plaintext address could live, because the address **is** the key material condensed.

This is why "just turn encryption off" is not a setting that could be added. It would mean having no addresses.

---

## Links are key exchanges

A link is established by an ephemeral X25519 exchange. Both ends derive a shared secret; every packet on that link is encrypted with it. The key exists only for the life of the link and never appears on the wire.

That is why a captured session cannot be decrypted later even with a station's long-term key — the session key was never transmitted.

---

## What this means for the amateur bands

Part 97 §97.113(a)(4) prohibits messages "encoded for the purpose of obscuring their meaning." A protocol that cannot transmit an unencoded message is therefore in a difficult position on the ham bands, and no amount of configuration moves it.

Three responses are possible:

1. **Do not use Reticulum on the amateur bands.** Defensible, and many operators choose it.
2. **Argue that addressing is not obscuring.** This is the argument this registry is built on. See [PURPOSE.md](PURPOSE.md).
3. **Make the traffic legible by publishing the keys.** This is what the registry actually does.

The profile does 2 and 3 together. Neither alone is sufficient: publishing a key without an argument leaves the purpose unaddressed, and making an argument without publishing leaves it untestable.

---

## The comparison worth making

Winlink takes the opposite position: transparency is the legal default, and access-control crypto is bolted on at the edges. Its RF layer is demodulable by anyone with an SDR and the right software, and its content is plaintext as far as the air goes.

Reticulum cannot do that. It is encrypted end to end because its addressing requires it, and there is no path back.

So the question is not "which is more transparent." The question is whether a protocol whose architecture forecloses plaintext can still satisfy a rule written for protocols where plaintext was the norm. That is the open question, and this registry is an attempt to make one answer testable.

---

[Register a station](REGISTER.md) · [The mode](README.md) · [Reasoning](PURPOSE.md) · [Decoding](DECODE.md)

**No warranty. Not legal advice. An unproven theory, offered for use and argument.**
