# Why a published key at all

The reasoning behind this registry, offered for use and argument.

---

## Reticulum has no plaintext mode

This is the fact everything else follows from. Reticulum cannot transmit without encryption. Its encryption *is* the addressing system: a destination is a hash of a public key, and a link is an ephemeral key exchange. There is no switch to turn it off, because turning it off would mean having no addresses.

Every link is authenticated and encrypted — ephemeral X25519 plus Fernet. Every destination is a hash. There is no "readable on the air" mode for links, and there is no version of the protocol that has one.

So a station that wants to use the amateur bands with Reticulum faces a question the protocol does not answer for them: the traffic is not readable by a listener, and no configuration makes it so.

---

## What the registry does

It does the one thing that makes the system legible: **it publishes the keys.**

Anyone who fetches a registry entry can read traffic addressed to that station. Not by breaking anything, not by escrow, not with the station's cooperation at the time of the transmission. By the station having said, in advance and in public, "here is my key."

That is the entire mechanism. It is not clever, and it is not new. It is what publishing a key has always meant.

---

## Why this is offered as an argument, not a claim

Two readings of the rules are possible here and I am not going to pretend only one exists.

**The reading I am offering:** encryption used as addressing is not encryption used to obscure meaning. The meaning is available — to anyone who looks. A station that publishes its key has removed the obstacle a listener would otherwise face, and has done so before transmitting, not after being asked.

**The reading against it:** the traffic is still not readable without fetching a key, and §97.113(a)(4) does not obviously care whether the key is available elsewhere. Encryption is encryption.

I think the first reading is defensible. I do not think it has been tested, and I am not claiming it as settled.

**What is claimed is narrower than what people usually assume.** This registry does not argue that encrypted traffic is transparent in general. It argues that a *particular* configuration — published key, ratchets off, link traffic excluded — is legible, and that the argument is testable by anyone who wants to test it.

---

## The three-part argument

For a station operating under this profile, the claim rests on three parts, and all three have to hold:

**1. The encoding is addressing, not concealment.** The destination hash is not a hidden address; it is a published one, and the registry is where it is published.

**2. The technical characteristics are publicly documented.** Not a black box. The frame layout, the key derivation, the decode chain — all of it is in [DECODE.md](DECODE.md), and all of it is checkable against RNS source.

**3. Publication is corroborating, not primary.** The keys being available is evidence for the argument. It is not the argument. The argument is about purpose, and purpose is about design.

If part 2 fails — if a station operates something undocumented and calls it this profile — the argument fails for that station regardless of whether the key is published.

---

## Where the argument has real opponents

Any significant effort here faces opposition from operators, from the ARRL, and from the FCC's reading of US ITU treaty commitments. That is not a reason to be wrong; it is a reason to be careful, and to state the claim narrowly enough that it survives disagreement.

Markqvist, the author of Reticulum, declines to make this argument. That is worth knowing before adopting it. He is not wrong to decline: the protocol works without this profile, and a protocol author has more to lose than a single station testing a reading.

---

## The honest summary

The profile is fully legible to any third party who looks, and that legibility is total — including the ability to forge. Both were chosen. An argument that states both in the same breath is stronger than one that argues only the first.

---

[Register a station](REGISTER.md) · [The mode](README.md) · [Decoding](DECODE.md) · [Ratchets](RATCHETS.md)

**No warranty. Not legal advice. An unproven theory, offered for use and argument.**
