# Registering a station

Anyone can list a station in this registry. You do not need a NomadNet node, and you do not need to know git.

There are two fields you send us — your callsign and your **private** identity key. The rest we work out or you can leave blank.

---

## What you are agreeing to

Publishing a private key is not like publishing a public one. Before you send it, understand exactly what it costs.

**Anyone who has your key can read every message addressed to that identity.** That is the point. It is what makes the transparency claim testable.

**Anyone who has your key can also forge messages that appear to come from you.** This is the part people do not expect. Signatures made with the published key verify against your published identity. A forger's message is indistinguishable from yours — to the recipient, and to any audit later.

**You cannot undo it.** GitHub issues are permanent, public, indexed by search engines, and frequently mirrored by third parties. Deleting the issue later does not remove copies.

**Log File** It is therefor highly recommended to configure the `operator_log` in ~.reticulum/config under the [[M73CallsignInterface]]


If authorship matters to your use of the network, do not register. The identification side of M73_RNS does not require publishing anything; only the transparency claim does.

[Read the full reasoning before deciding](PURPOSE.md)

---

## How to submit

[Open a registration issue](../../issues/new?template=register.yml)

Fill in the form. A maintainer will add your entry to `REGISTRY.md` and reply on the issue to confirm.

If you would rather not use the web form, you can open a plain issue and paste the same information, or send a pull request editing `REGISTRY.md` directly.

---

## What happens next

| Step | Who |
|---|---|
| You open the issue | You |
| Callsign format checked, identity hash computed | Maintainer or automated action |
| Entry added to `REGISTRY.md` | Maintainer |
| Issue closed with a link to your entry | Maintainer |

Your entry will contain:

| Field | Meaning |
|---|---|
| Callsign | As you gave it |
| Identity hash | The 16-byte truncated hash of your identity, computed from your public key |
| Delivery hash | The hash used to address LXMF messages to you |
| Date entered | The date the entry was added |
| Public key | Derived from your private key, published for verification |
| Private key | As you gave it |

---

## Getting your key

You need the **identity file** from your Reticulum installation.

| Software | Path |
|---|---|
| MeshChatX | `~/.reticulum-meshchatx/identities/<hash>/identity` |
| NomadNet | `~/.nomadnetwork/storage/identity` |
| Reticulum | `~/.reticulum/storage/identities/<hash>/identity` |

The file is 64 bytes of binary. To turn it into the hex form the registry uses, run one command:

```
python3 -c "print(open('path/to/identity','rb').read().hex())"
```

That prints 128 hex characters. That is your private key, and that is what the form asks for.

The public key can be derived from it, so you only need to send the one value.

---

## Before you register: turn ratchets off

A station that publishes its key but leaves ratchets enabled is still unreadable. Peers that heard you while you were ratcheting stored a ratchet and will keep encrypting to it, and your published key will not open those messages.

This is not optional and it is not obvious. [Read the procedure](RATCHETS.md) before you register, because the order matters: patch first, then create the identity, then publish.

If you publish first and patch later, your entry will look correct and work for nobody.

---

## If you change your mind

You cannot retract a key, but you can retire an identity:

1. Create a new identity, with ratchets already off.
2. Register the new one.
3. Ask for the old entry to be marked retired rather than deleted, so the record of when the exposure began survives.

Deleting the old row would destroy the only defence the profile offers — the ability to say when a key became public.
