"""Tamper-evident outcome ledger: hash chain, verifier, signed daily head, evidence bundle.

No Slotback imports, so any per-outcome deployment can reuse it.
"""

from slotledger.bundle import BundleInvalid, read_bundle, write_bundle
from slotledger.chain import GENESIS, Event, append, seal, snapshot_hash
from slotledger.sign import SignedHead, SigningKeyMissing, sign_head
from slotledger.verify import Report, verify

__version__ = "0.1.0"
__all__ = [
    "GENESIS",
    "BundleInvalid",
    "Event",
    "Report",
    "SignedHead",
    "SigningKeyMissing",
    "append",
    "read_bundle",
    "seal",
    "sign_head",
    "snapshot_hash",
    "verify",
    "write_bundle",
]
