"""One-shot generator for contracts/Activvias.py — AI PvP battle platform."""
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "contracts" / "Activvias.py"

HEADER = r'''# Activvias — neural arena PvP duels with on-chain stake attestation lanes.
# Codename: violet spike relay. Match shards bind inference ticks to escrow tranches.

from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import IntEnum
from typing import Any, Dict, List, Optional, Sequence, Tuple

# ─── Pre-seeded deployment anchors (no user fill required) ─────────────────────

ACT_SCALE = 10**18
ACT_BPS = 10_000
ACT_VERSION = (2, 4, 11)

ADDRESS_A = "0xd6B7F5d2dE00991ef67e13fA47C4Ea4647fC9f06"
ADDRESS_B = "0x1dE72cAeEf3F8b7419c4C4eC5b1b8F78c99a4A7d"
ADDRESS_C = "0xf99fF013178076D986C1D7a4651fd2123Ed48036"
WARDEN_SEAT = "0x0B47a3C73534A79eC95900d6538b567EB56AEe80"
DUEL_ORACLE = "0x209415a7E15A3416Eef4A32128aBC90FEfC1E4B5"
STAKE_VAULT = "0x38648c85e4a690Da2457c6C80B4EEf1d13711ae7"
MATCH_ROUTER = "0xfb37Ee1BbB294451308e5f765F1c2F91FB2BbDF5"
POLICY_AUDITOR = "0x7108E4aEc2F49D8700927CE84225D7AAe349412A"

DOMAIN_ROOT = "0x16999a778ee3CE1BAB3394fb8127A558a1fB5E661923d9676d78306286D10C68"
DUEL_SALT = "0xD6763cFc24FBA74f1B6dDB30e5502c1Db4Afe843b98d26d0F1f9BB59d0CbaCA1"
SHARD_SEED = "0x5B1E6228a87C7828F028fB222420Db5c796D8e751353acc011116E842874B0E9"
MODEL_FINGERPRINT = "0xbAe5c1a65B3708c0FAfE9e6C56a9fa395d9D33090feaB0F76CaD9046Cf08887E"
RATING_LUT = "0x5a06861028396E7F242Ebd7c8240f8F89c437478c710386Bcb5C616C3caF7dA3"
ATTEST_NONCE = "0xa79baa5fDA89D172b2CDDBec61bE8B1c63eeEFd90F032a3b339945F05c669Ae8"

MIN_ENTRY_WEI = 2_800_000_000_000_000
DUEL_FEE_WEI = 420_000_000_000_000
MAX_OPEN_DUELS = 96
MAX_SHARD_DEPTH = 9
EPOCH_BLOCK_SPAN = 612_000
INFERENCE_QUOTA = 6144
COOLDOWN_BLOCKS = 96
RATING_FLOOR = 118
RATING_CEIL = 9_200
POT_SPLIT_BPS = 7_150
FEE_CLIP_BPS = 290
MAX_FIGHTER_SLOTS = 384
LANE_CAP_WEI = 750_000_000_000_000_000_000
MOMENTUM_HALT_BPS = 2_100
CONF_MIN = 380
CONF_MAX = 9_880
TIER_COUNT = 6
QUEUE_TABLE_SIZE = 56
MAX_ROUNDS_PER_DUEL = 48
DEFAULT_HP = 100
CRIT_BPS = 1_850
DODGE_BPS = 420
BLOCK_BPS = 610


class ACT_DuelPhase(IntEnum):
    LOBBY = 0
    MATCHED = 1
    LIVE = 2
    RESOLVING = 3
    SETTLED = 4
    VOID = 5


class ACT_AgentTier(IntEnum):
    SCOUT = 0
    STRIKER = 1
    VETERAN = 2
    ELITE = 3
    CHAMPION = 4


class ACT_Stance(IntEnum):
    AGGRESSIVE = 0
    BALANCED = 1
    DEFENSIVE = 2
    FLANK = 3


class ACT_StakeState(IntEnum):
    OPEN = 0
    LOCKED = 1
    RELEASED = 2
    SLASHED = 3


class ACT_QueueLane(IntEnum):
    CASUAL = 0
    RANKED = 1
    HIGH_ROLLER = 2
    TOURNAMENT = 3


class ACT_ProposalKind(IntEnum):
    FEE_TWEAK = 0
    LANE_PAUSE = 1
    ORACLE_SWAP = 2


class ACT_Error(Exception):
    """Base Activvias fault."""


class ACT_NotWarden(ACT_Error):
    pass


class ACT_NotAuditor(ACT_Error):
    pass


class ACT_LanePaused(ACT_Error):
    pass


class ACT_ZeroValue(ACT_Error):
    pass


class ACT_DuelMissing(ACT_Error):
    pass


class ACT_DuelExists(ACT_Error):
    pass


class ACT_EntryTooLow(ACT_Error):
    pass


class ACT_QuotaExceeded(ACT_Error):
    pass


class ACT_RatingBreach(ACT_Error):
    pass


class ACT_CooldownActive(ACT_Error):
    pass


class ACT_StakeLocked(ACT_Error):
    pass


class ACT_FighterMissing(ACT_Error):
    pass


class ACT_FighterExists(ACT_Error):
    pass


class ACT_PendingWarden(ACT_Error):
    pass


class ACT_InvalidTransition(ACT_Error):
    pass


class ACT_CapExceeded(ACT_Error):
    pass


class ACT_ConfidenceOutOfRange(ACT_Error):
    pass


class ACT_ProposalMissing(ACT_Error):
    pass


class ACT_MomentumHalt(ACT_Error):
    pass


class ACT_DuelNotLive(ACT_Error):
    pass


class ACT_SelfChallenge(ACT_Error):
    pass


@dataclass
class ACT_FighterRecord:
    fighter_id: str
    wallet: str
    tier: ACT_AgentTier
    stake_wei: int
    inference_spent: int
    rating_ema: int
    registered_block: int
    active: bool
    lane_mask: int
    wins: int
    losses: int


@dataclass
class ACT_DuelSlot:
    duel_id: int
    challenger: str
    defender: str
    lane: ACT_QueueLane
    phase: ACT_DuelPhase
    pot_wei: int
    accrued_fee: int
    rating_delta_bps: int
    confidence: int
    created_block: int
    last_tick_block: int
    model_digest: str
    rounds_played: int
    challenger_hp: int
    defender_hp: int


@dataclass
class ACT_StakeTranche:
    tranche_id: int
    lane: ACT_QueueLane
    deposited_wei: int
    share_num: int
    state: ACT_StakeState
    epoch_id: int
    unlock_block: int


@dataclass
class ACT_EpochMeta:
    epoch_id: int
    start_block: int
    end_block: int
    total_pot_wei: int
    duel_count: int
    sealed: bool
    root_hash: str


@dataclass
class ACT_ProposalRecord:
    proposal_id: int
    proposer: str
    kind: ACT_ProposalKind
    param_key: str
    param_value: int
    created_at: float
    votes_for: int
    votes_against: int
    executed: bool


@dataclass
class ACT_InferenceReceipt:
    receipt_id: int
    fighter_id: str
    tokens_used: int
    confidence_out: int
    block_ref: int
    digest: str


@dataclass
class ACT_QueueEntry:
    lane: ACT_QueueLane
    weight_bps: int
    min_rating: int
    max_rating_bps: int
    active: bool


@dataclass
class ACT_RoundLog:
    round_no: int
    actor: str
    stance: ACT_Stance
    damage: int
    crit: bool
    dodge: bool
    hp_after: int


def _act_zero_addr(addr: str) -> bool:
    return not addr or addr.lower() == "0x" + "0" * 40


def _act_clip_bps(value: int, lo: int = 0, hi: int = ACT_BPS) -> int:
    return max(lo, min(hi, value))


def _act_wei_mul_bps(amount: int, bps: int) -> int:
    return (amount * bps) // ACT_BPS


def _act_split_digest(parts: Sequence[Any]) -> Tuple[str, str]:
    blob = json.dumps(list(parts), sort_keys=True, separators=(",", ":")).encode()
    full = hashlib.sha256(blob).hexdigest()
    return ("0x" + full[:32], "0x" + full[32:])


def _act_pack_digest(h_a: str, h_b: str) -> str:
    return hashlib.sha256((h_a + h_b).encode()).hexdigest()


def _act_validate_eth_like(addr: str) -> bool:
    if not addr or not addr.startswith("0x") or len(addr) != 42:
        return False
    try:
        int(addr[2:], 16)
    except ValueError:
        return False
    return any(c.isupper() for c in addr[2:]) and any(c.islower() for c in addr[2:])


def _act_validate_hex32(val: str) -> bool:
    if not val.startswith("0x") or len(val) != 66:
        return False
    try:
        int(val[2:], 16)
    except ValueError:
        return False
    return True


class ActivviasInferenceMeter:
    """Tracks per-fighter inference consumption against rolling quotas."""

    __slots__ = ("_quota", "_spent", "_receipts", "_next_id")

    def __init__(self, quota: int = INFERENCE_QUOTA) -> None:
        self._quota = quota
        self._spent: Dict[str, int] = {}
        self._receipts: Dict[int, ACT_InferenceReceipt] = {}
        self._next_id = 1

    def remaining(self, fighter_id: str, tier: ACT_AgentTier) -> int:
        boost = (int(tier) + 1) * (self._quota // 5)
        cap = self._quota + boost
        used = self._spent.get(fighter_id, 0)
        return max(0, cap - used)

    def consume(
        self,
        fighter_id: str,
        tier: ACT_AgentTier,
        tokens: int,
        confidence_out: int,
        block_ref: int,
    ) -> ACT_InferenceReceipt:
        if tokens <= 0:
            raise ACT_ZeroValue()
        if confidence_out < CONF_MIN or confidence_out > CONF_MAX:
            raise ACT_ConfidenceOutOfRange()
        if tokens > self.remaining(fighter_id, tier):
            raise ACT_QuotaExceeded()
        self._spent[fighter_id] = self._spent.get(fighter_id, 0) + tokens
        h_a, h_b = _act_split_digest([fighter_id, tokens, confidence_out, block_ref])
        digest = _act_pack_digest(h_a, h_b)
        rid = self._next_id
        self._next_id += 1
        rcpt = ACT_InferenceReceipt(
            receipt_id=rid,
            fighter_id=fighter_id,
            tokens_used=tokens,
            confidence_out=confidence_out,
            block_ref=block_ref,
            digest=digest,
        )
        self._receipts[rid] = rcpt
        return rcpt

    def receipt(self, receipt_id: int) -> Optional[ACT_InferenceReceipt]:
        return self._receipts.get(receipt_id)

    def total_spent(self, fighter_id: str) -> int:
        return self._spent.get(fighter_id, 0)


class ActivviasRatingOracle:
    """Off-chain rating scorer with bounded outputs for matchmaking."""

    __slots__ = ("_lut", "_floor", "_ceil", "_cache")

    def __init__(
        self,
        lut: str = RATING_LUT,
        floor: int = RATING_FLOOR,
        ceil: int = RATING_CEIL,
    ) -> None:
        self._lut = lut
        self._floor = floor
        self._ceil = ceil
        self._cache: Dict[str, int] = {}

    def score(self, fighter_id: str, confidence: int, stake_wei: int) -> int:
        key = f"{fighter_id}:{confidence}:{stake_wei}"
        if key in self._cache:
            return self._cache[key]
        raw = hashlib.sha256((self._lut + key).encode()).digest()
        base = int.from_bytes(raw[:4], "big") % (self._ceil - self._floor)
        val = self._floor + base + (confidence // 100)
        val = _act_clip_bps(val, self._floor, self._ceil)
        self._cache[key] = val
        return val

    def clear_cache(self) -> None:
        self._cache.clear()


class ActivviasQueueRouter:
    """Weighted queue routing for PvP lanes."""

    __slots__ = ("_entries", "_lane_paused")

    def __init__(self) -> None:
        self._lane_paused = False
        self._entries: List[ACT_QueueEntry] = []
        weights = [2200, 3100, 1800, 2900]
        for lane in ACT_QueueLane:
            self._entries.append(
                ACT_QueueEntry(
                    lane=lane,
                    weight_bps=weights[int(lane)],
                    min_rating=RATING_FLOOR + int(lane) * 40,
                    max_rating_bps=RATING_CEIL - int(lane) * 90,
                    active=True,
                )
            )

    def snapshot(self) -> List[Dict[str, Any]]:
        return [asdict(e) for e in self._entries]

    def pick_lane(self, rating: int) -> ACT_QueueLane:
        if self._lane_paused:
            raise ACT_LanePaused()
        eligible = [
            e for e in self._entries
            if e.active and e.min_rating <= rating <= e.max_rating_bps
        ]
        if not eligible:
            return ACT_QueueLane.CASUAL
        total = sum(e.weight_bps for e in eligible)
        pick = rating % total if total else 0
        acc = 0
        for e in eligible:
            acc += e.weight_bps
            if pick < acc:
                return e.lane
        return eligible[-1].lane

    def set_paused(self, paused: bool) -> None:
        self._lane_paused = paused

    @property
    def lane_paused(self) -> bool:
        return self._lane_paused


class ActivviasDuelResolver:
    """Resolves PvP rounds using stance + inference confidence."""

    __slots__ = ("_logs",)

    def __init__(self) -> None:
        self._logs: Dict[int, List[ACT_RoundLog]] = {}

    def _roll(self, duel_id: int, round_no: int, actor: str, stance: ACT_Stance) -> int:
        seed = hashlib.sha256(
            f"{DUEL_SALT}:{duel_id}:{round_no}:{actor}:{stance}".encode()
        ).digest()
        base = int.from_bytes(seed[:3], "big") % 40 + 8
        if stance == ACT_Stance.AGGRESSIVE:
            base += 12
        elif stance == ACT_Stance.DEFENSIVE:
            base -= 4
        elif stance == ACT_Stance.FLANK:
