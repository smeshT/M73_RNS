# M73CallsignInterface.py
#
# A Reticulum CustomInterface that adds an M73 callsign envelope to
# MODEM73 traffic, by subclassing Modem73Interface.
#
# Why
# ---
# modem73 identifies a station in two ways only:
#   1. a base40 callsign in the OFDM metadata block  (OFDM modes only)
#   2. an "M73:<call>:" text envelope parsed out of received payloads
#
# Its encoder is called with no callsign argument at all on the MFSK and
# ROBUST paths (kiss_tnc_impl.hh:1071 and :1176), so a station running
# RDM-300, RDM-600 or MFSK transmits nothing a receiver can attribute to a
# station. That is the identification gap this class closes.
#
# It does so inside the frame it identifies: one transmission, one CSMA
# gate, one fate. There is no separate identification burst, so nothing is
# added to the channel and no new collision window opens on a half-duplex
# link.
#
# Install
# -------
# Drop this file next to Modem73Interface.py in ~/.reticulum/interfaces/ and
# use:
#
#   [[MODEM73]]
#     type = M73CallsignInterface
#     enabled = yes
#     callsign = KJ5FQT
#     envelope = yes
#     target_host = 127.0.0.1
#     target_port = 8001
#     control_host = 127.0.0.1
#     control_port = 8073
#
# Modem73Interface must be importable from that directory. Reticulum exec's
# external interfaces rather than importing them, and injects only
# `Interface` and `RNS` into the namespace, so the import below has to find
# its sibling file on its own.
#
# Interoperability
# ----------------
# Both ends must run this wrapper. A stock Reticulum peer receives
# "M73:KJ5FQT:<rns bytes>" where it expects a Reticulum header and drops it.
# strict = yes (the default) logs on the receive side rather than letting a
# mismatched pair look like a dead link.
#
# Never claim this is legal. Whether an unauthenticated in-frame callsign
# satisfies an identification requirement is a reading of the rules, not a
# settled fact. Use at your own risk.

import os
import sys
import time

import RNS

# Reticulum exec's this file, it does not import it. Consequences that bit:
#   - `__file__` is NOT defined in the exec namespace, so any path built from
#     it raises NameError at load time and the interface is dropped.
#   - Only `Interface` and `RNS` are pre-injected.
#   - sys.path is not consulted for the config type name.
#
# The sibling Modem73Interface.py lives in the same directory as this file, so
# that directory has to be made importable before the import below. The
# directory is recovered from this module's own spec once the module exists,
# and falls back to Reticulum's conventional external-interface directory.
def _interface_dir():
    try:
        here = os.path.dirname(os.path.abspath(__file__))  # set when imported
        if here and os.path.isdir(here):
            return here
    except NameError:
        pass
    return os.path.expanduser("~/.reticulum/interfaces")


_HERE = _interface_dir()
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from Modem73Interface import Modem73Interface  # stock interface, ships with the modem setup

PREFIX = b"M73:"
SEP = b":"
MAX_CALL = 12
MIN_CALL = 3

# The receive side is deliberately looser than transmit. modem73 accepts any
# printable callsign of 1-12 characters, so a peer may legitimately send
# "M73:AB:". Refusing to strip that would hand RNS raw bytes for a frame the
# modem had already attributed correctly. Transmit is strict because a
# well-formed callsign is what we owe the channel; receive is permissive
# because dropping a valid peer is worse than accepting a short one.
RX_MIN_CALL = 1


def encode_envelope(callsign, payload):
    """Return b"M73:<callsign>:<payload>".

    The callsign is validated rather than trusted: modem73 requires printable
    ASCII and 5-12 characters before it will attribute a payload to a station,
    so anything outside that would be transmitted but never parsed.
    """
    if isinstance(callsign, bytes):
        call = callsign
    else:
        call = str(callsign).encode("ascii", "strict")
    if not (MIN_CALL <= len(call) <= MAX_CALL):
        raise ValueError(
            "callsign must be %d-%d chars, got %d: %r"
            % (MIN_CALL, MAX_CALL, len(call), call)
        )
    if not all(32 < c < 127 for c in call):
        raise ValueError("callsign must be printable ASCII: %r" % (call,))
    if SEP in call:
        # The parser splits on the first colon, so a colon inside the callsign
        # shifts the boundary and misattributes the payload.
        raise ValueError("callsign must not contain ':': %r" % (call,))
    return PREFIX + call + SEP + payload


def decode_envelope(data):
    """Split a payload into (callsign, stripped_payload).

    Returns (None, data) when the frame carries no envelope.
    """
    if not data or not data.startswith(PREFIX):
        return None, data
    rest = data[len(PREFIX):]
    idx = rest.find(SEP)
    if idx < 0:
        return None, data
    call = rest[:idx]
    if not (RX_MIN_CALL <= len(call) <= MAX_CALL):
        return None, data
    if not all(32 < c < 127 for c in call):
        return None, data
    # Decoded to str: the return value only feeds accounting and log output
    # (seen_callsigns, the strict-mode warning), where a bytes key would
    # render as b'KJ5FQT' and read as a bug.
    return call.decode("ascii"), rest[idx + 1:]


class M73CallsignInterface(Modem73Interface):
    """Modem73Interface with an M73 callsign envelope.

    Only three seams are touched: the constructor (to read the new config
    keys), process_outgoing (to wrap, after handshake/proof classification,
    and to hold back recursive path requests), and process_incoming (to
    strip). Everything else -- the control port, mode-aware bitrate, short
    frames, CSMA accounting -- stays with Modem73Interface.
    """

    def __init__(self, owner, configuration):
        cfg = dict(configuration)
        self.callsign = cfg.pop("callsign", None)
        self.envelope_enabled = _as_bool(cfg.pop("envelope", False))
        self.strict = _as_bool(cfg.pop("strict", True))
        # "discover" (default) leaves Transport's path-request behaviour
        # untouched. "passive" stops this interface from carrying recursive
        # path requests that other interfaces generated; see _block_path_request.
        self.path_discovery = str(cfg.pop("path_discovery", "discover")).lower()
        if self.path_discovery not in ("discover", "passive"):
            raise ValueError(
                "path_discovery must be 'discover' or 'passive', not %r"
                % self.path_discovery
            )
        self.oplog_path = cfg.pop("operator_log", None)
        self.seen_callsigns = {}
        self.envelope_rejects = 0
        self.oplog_fh = None
        self._oplog_warned = False

        # Refuse at construction rather than putting an unidentified station
        # on the air. A placeholder callsign would be worse than no interface:
        # it would transmit a false attribution.
        if self.envelope_enabled and not self.callsign:
            raise ValueError(
                "envelope is enabled but no callsign was configured for %s"
                % cfg.get("name", "modem73")
            )

        # Validate once, here, so a bad callsign fails at startup instead of
        # on the first transmit.
        if self.envelope_enabled:
            encode_envelope(self.callsign, b"")

        super().__init__(owner, cfg)

        if self.envelope_enabled and self.oplog_path:
            try:
                self.oplog_path = os.path.expanduser(str(self.oplog_path))
                parent = os.path.dirname(self.oplog_path)
                if parent and not os.path.isdir(parent):
                    os.makedirs(parent, exist_ok=True)
                # Append, line-buffered: the log must survive restarts and be
                # readable while the interface is running.
                self.oplog_fh = open(self.oplog_path, "a", buffering=1)
                RNS.log(
                    "Interface %s: operator log -> %s"
                    % (str(self), self.oplog_path),
                    RNS.LOG_INFO,
                )
            except Exception as e:
                self.oplog_fh = None
                RNS.log(
                    "Interface %s: could not open operator log %r: %s"
                    % (str(self), self.oplog_path, e),
                    RNS.LOG_WARNING,
                )

        if self.envelope_enabled:
            RNS.log(
                "Interface %s: M73_RNS envelope active (callsign %s)"
                % (str(self), self.callsign),
                RNS.LOG_DEBUG,
            )

    def process_outgoing(self, data):
        if self._block_path_request(data):
            return

        if not (self.envelope_enabled and data):
            return super().process_outgoing(data)

        # Classify BEFORE wrapping, not after. _is_handshake and _is_proof read
        # Reticulum header bytes at fixed offsets; a prepended envelope would
        # shift every offset and break both predicates, silently disabling
        # handshake_x2 and proof_x2.
        is_handshake = self._is_handshake(data)
        is_proof = self._is_proof(data)

        # Idempotence: never double-wrap. Covers a retransmit of already-
        # wrapped bytes and any future path that hands us a wrapped frame.
        if not data.startswith(PREFIX):
            data = encode_envelope(self.callsign, data)

        # Delegate with the copy logic Modem73Interface would have applied,
        # but on the wrapped payload. super().process_outgoing() re-runs its
        # own classification, which is now looking at "M73:..." and would
        # match nothing -- hence re-implementing the two-line copy rule here
        # rather than calling super() with the wrapped bytes.
        copies = 1
        if getattr(self, "ifac_identity", None) is None:
            if self._handshake_x2 and is_handshake:
                copies = 2
            elif self._proof_x2 and is_proof:
                copies = 2

        # One log line per logical frame, not per copy: handshake/proof
        # duplication is a link-layer retry, not two transmissions.
        if self.oplog_fh is not None:
            self._oplog("tx", self.callsign, len(data))

        for _ in range(copies):
            if (
                self._short_policy == "auto"
                and self.online
                and self._short_oper_mode is not None
                and len(data) <= self._short_mtu
                and self._send_short_frame(data)
            ):
                continue
            # Bypass Modem73Interface.process_outgoing (we already applied its
            # logic) and go straight to the KISS path.
            super(Modem73Interface, self).process_outgoing(data)

    # ------------------------------------------------------------------
    # Keep path discovery off the slow link.
    #
    # When a local client asks for an unknown destination, Transport puts a
    # path request on every other online interface -- this one included, if
    # its mode is one of DISCOVER_PATHS_FOR. The request is a single small
    # broadcast, but on HF it costs the channel, holds announces behind the
    # announce cap, and asks the far end for a lookup the TCP side can do
    # faster. No config key means "answer requests, never relay them".
    #
    # So: recognise a path request going out on this interface, and drop it
    # if it was a search for a destination this station does not yet know.
    # A path request for a destination already in the path table is a direct
    # answer to a specific peer, and is left alone.
    def _block_path_request(self, data):
        if self.path_discovery != "passive":
            return False

        destination_hash = self._path_request_destination(data)
        if destination_hash is None:
            return False

        try:
            known = destination_hash in RNS.Transport.path_table
        except Exception:
            return False

        if known:
            return False

        if RNS.sl(RNS.LOG_PATHING):
            RNS.log(
                "Not sending path discovery request for "
                + RNS.prettyhexrep(destination_hash)
                + " on "
                + str(self)
                + " (path_discovery = passive)",
                RNS.LOG_PATHING,
            )
        return True

    @staticmethod
    def _path_request_destination(data):
        # A path request is a HEADER_1 single-destination DATA packet sent to
        # the built-in "path.request" destination: dest hash, then the hash of
        # the destination actually being searched for. Match the destination
        # name at runtime rather than pinning a hash.
        try:
            if len(data) < 2 * (RNS.Identity.TRUNCATED_HASHLENGTH // 8):
                return None
            if (data[0] & 0x03) != (RNS.Packet.HEADER_1 | RNS.Packet.DATA):
                return None
            pr_hash = RNS.Destination.hash(
                None, RNS.Transport.APP_NAME, "path", "request"
            )
            if data[2:2 + len(pr_hash)] != pr_hash:
                return None
            # One-byte packet-context/traffic-class field sits between the
            # path-request destination hash and the hash being searched for.
            start = 2 + len(pr_hash) + 1
            return data[start:start + len(pr_hash)]
        except Exception:
            return None

    def process_incoming(self, data):
        if not data:
            return
        if self.envelope_enabled:
            call, payload = decode_envelope(data)
            if call is not None:
                self.seen_callsigns[call] = self.seen_callsigns.get(call, 0) + 1
                data = payload
                if self.oplog_fh is not None:
                    self._oplog("rx", call, len(payload))
            else:
                self.envelope_rejects += 1
                if self.oplog_fh is not None:
                    self._oplog("rx_noenv", None, len(data))
                if self.strict:
                    # Envelope expected but absent: the peer is probably not
                    # running the wrapper. Say so a few times rather than let
                    # the link look mysteriously dead.
                    if self.envelope_rejects in (1, 10, 100) or (
                        self.envelope_rejects % 1000 == 0
                    ):
                        RNS.log(
                            "Interface %s: received %d frame(s) without an M73 "
                            "envelope; peer may not run the wrapper"
                            % (str(self), self.envelope_rejects),
                            RNS.LOG_WARNING,
                        )
        super().process_incoming(data)

    # ------------------------------------------------------------------
    # Amateur-operator log
    #
    # Only interfaces running the envelope write here, which is the point: a
    # line in this file is evidence that a frame with a station identifier was
    # actually transmitted or received, and by whom. It supplements the
    # operator's station log rather than replacing it -- it records frame
    # counts and byte sizes, never message content.
    #
    # Format is one line per frame:
    #   2026-11-19T07:12:44Z  tx  KJ5FQT     158B
    #   2026-11-19T07:12:51Z  rx  KF0YRY/2   158B
    #   2026-11-19T07:13:02Z  rx_noenv      44B
    #
    # rx_noenv is the interesting one: a frame arrived from a peer that is not
    # wrapping, so the identifier is absent. Recording it rather than dropping
    # it silently is deliberate.
    # ------------------------------------------------------------------
    def _oplog(self, direction, call, size):
        try:
            stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            self.oplog_fh.write(
                "%-22s %-10s %-12s %dB\n"
                % (stamp, direction, call if call else "-", size)
            )
            self.oplog_fh.flush()
        except Exception as e:
            # Never let the operator log break the interface.
            if not self._oplog_warned:
                self._oplog_warned = True
                RNS.log(
                    "Interface %s: operator log write failed: %s"
                    % (str(self), e),
                    RNS.LOG_WARNING,
                )


def _as_bool(value):
    """Parse Reticulum-style config booleans.

    Reticulum's own interfaces accept yes/no, true/false and 1/0, and a bare
    bool() on the string "no" is True -- so the conversion has to be explicit.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ("yes", "true", "1", "on", "y")
    return bool(value)


# Reticulum reads the global `interface_class` after exec'ing this file when
# the config `type` does not match a built-in. Binding it here is what makes
# `type = M73CallsignInterface` resolve.
interface_class = M73CallsignInterface
