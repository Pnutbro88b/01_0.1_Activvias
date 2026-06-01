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
            base += 6
        return max(1, base)

    def play_round(
        self,
        duel: ACT_DuelSlot,
        actor_wallet: str,
        stance: ACT_Stance,
        confidence: int,
    ) -> ACT_RoundLog:
        if duel.phase != ACT_DuelPhase.LIVE:
            raise ACT_DuelNotLive()
        rnd = duel.rounds_played + 1
        dmg = self._roll(duel.duel_id, rnd, actor_wallet, stance)
        crit = (confidence % 1000) > (1000 - CRIT_BPS // 10)
        dodge = (confidence % 500) < (DODGE_BPS // 2)
        if crit:
            dmg = int(dmg * 1.5)
        if dodge:
            dmg = max(1, dmg // 3)
        is_challenger = actor_wallet.lower() == duel.challenger.lower()
        if is_challenger:
            duel.defender_hp = max(0, duel.defender_hp - dmg)
            hp_after = duel.defender_hp
        else:
            duel.challenger_hp = max(0, duel.challenger_hp - dmg)
            hp_after = duel.challenger_hp
        duel.rounds_played = rnd
        log = ACT_RoundLog(
            round_no=rnd,
            actor=actor_wallet,
            stance=stance,
            damage=dmg,
            crit=crit,
            dodge=dodge,
            hp_after=hp_after,
        )
        self._logs.setdefault(duel.duel_id, []).append(log)
        if duel.challenger_hp <= 0 or duel.defender_hp <= 0:
            duel.phase = ACT_DuelPhase.RESOLVING
        if rnd >= MAX_ROUNDS_PER_DUEL and duel.phase == ACT_DuelPhase.LIVE:
            duel.phase = ACT_DuelPhase.RESOLVING
        return log

    def logs_for(self, duel_id: int) -> List[ACT_RoundLog]:
        return list(self._logs.get(duel_id, []))

    def winner_wallet(self, duel: ACT_DuelSlot) -> Optional[str]:
        if duel.challenger_hp <= 0 and duel.defender_hp > 0:
            return duel.defender
        if duel.defender_hp <= 0 and duel.challenger_hp > 0:
            return duel.challenger
        if duel.challenger_hp > duel.defender_hp:
            return duel.challenger
        if duel.defender_hp > duel.challenger_hp:
            return duel.defender
        return None


class ActivviasPlatform:
    """Main AI gaming PvP battle platform orchestrator."""

    def __init__(self, genesis_block: int = 19_200_000) -> None:
        self._warden = WARDEN_SEAT
        self._pending_warden: Optional[str] = None
        self._auditor = POLICY_AUDITOR
        self._genesis = genesis_block
        self._block = genesis_block
        self._lane_paused = False
        self._fighters: Dict[str, ACT_FighterRecord] = {}
        self._duels: Dict[int, ACT_DuelSlot] = {}
        self._tranches: Dict[int, ACT_StakeTranche] = {}
        self._epochs: Dict[int, ACT_EpochMeta] = {}
        self._proposals: Dict[int, ACT_ProposalRecord] = {}
        self._next_duel = 1
        self._next_tranche = 1
        self._next_proposal = 1
        self._current_epoch = 0
        self._meter = ActivviasInferenceMeter()
        self._rating = ActivviasRatingOracle()
        self._router = ActivviasQueueRouter()
        self._resolver = ActivviasDuelResolver()
        self._open_duel_count = 0

    @property
    def warden(self) -> str:
        return self._warden

    def _require_warden(self, caller: str) -> None:
        if caller.lower() != self._warden.lower():
            raise ACT_NotWarden()

    def _require_auditor(self, caller: str) -> None:
        if caller.lower() != self._auditor.lower():
            raise ACT_NotAuditor()

    def _tick_block(self, delta: int = 1) -> int:
        self._block += delta
        return self._block

    def propose_warden(self, caller: str, next_warden: str) -> None:
        self._require_warden(caller)
        if _act_zero_addr(next_warden):
            raise ACT_ZeroValue()
        self._pending_warden = next_warden

    def accept_warden(self, caller: str) -> None:
        if not self._pending_warden:
            raise ACT_PendingWarden()
        if caller.lower() != self._pending_warden.lower():
            raise ACT_NotWarden()
        self._warden = self._pending_warden
        self._pending_warden = None

    def set_lane_paused(self, caller: str, paused: bool) -> None:
        self._require_warden(caller)
        self._lane_paused = paused
        self._router.set_paused(paused)

    def register_fighter(
        self,
        caller: str,
        wallet: str,
        tier: ACT_AgentTier,
        stake_wei: int,
    ) -> str:
        self._require_warden(caller)
        if _act_zero_addr(wallet):
            raise ACT_ZeroValue()
        if stake_wei < MIN_ENTRY_WEI:
            raise ACT_EntryTooLow()
        if wallet in self._fighters:
            raise ACT_FighterExists()
        if len(self._fighters) >= MAX_FIGHTER_SLOTS:
            raise ACT_CapExceeded()
        fid = str(uuid.uuid4())
        rating = self._rating.score(fid, CONF_MIN + 100, stake_wei)
        rec = ACT_FighterRecord(
            fighter_id=fid,
            wallet=wallet,
            tier=tier,
            stake_wei=stake_wei,
            inference_spent=0,
            rating_ema=rating,
            registered_block=self._block,
            active=True,
            lane_mask=0,
            wins=0,
            losses=0,
        )
        self._fighters[wallet] = rec
        return fid

    def run_inference(
        self,
        caller: str,
        fighter_id: str,
        tokens: int,
        confidence: int,
    ) -> ACT_InferenceReceipt:
        if caller.lower() != DUEL_ORACLE.lower():
            raise ACT_NotAuditor()
        rec = next((f for f in self._fighters.values() if f.fighter_id == fighter_id), None)
        if not rec:
            raise ACT_FighterMissing()
        rcpt = self._meter.consume(fighter_id, rec.tier, tokens, confidence, self._block)
        rec.inference_spent += tokens
        return rcpt

    def open_duel(
        self,
        challenger: str,
        defender: str,
        lane: ACT_QueueLane,
        pot_wei: int,
        confidence: int,
    ) -> int:
        if self._lane_paused:
            raise ACT_LanePaused()
        if challenger.lower() == defender.lower():
            raise ACT_SelfChallenge()
        if pot_wei < MIN_ENTRY_WEI:
            raise ACT_EntryTooLow()
        if self._open_duel_count >= MAX_OPEN_DUELS:
            raise ACT_CapExceeded()
        if challenger not in self._fighters or defender not in self._fighters:
            raise ACT_FighterMissing()
        did = self._next_duel
        self._next_duel += 1
        h_a, h_b = _act_split_digest([did, challenger, defender, pot_wei])
        digest = _act_pack_digest(h_a, h_b)
        slot = ACT_DuelSlot(
            duel_id=did,
            challenger=challenger,
            defender=defender,
            lane=lane,
            phase=ACT_DuelPhase.LOBBY,
            pot_wei=pot_wei,
            accrued_fee=DUEL_FEE_WEI,
            rating_delta_bps=0,
            confidence=confidence,
            created_block=self._block,
            last_tick_block=self._block,
            model_digest=digest,
            rounds_played=0,
            challenger_hp=DEFAULT_HP,
            defender_hp=DEFAULT_HP,
        )
        self._duels[did] = slot
        self._open_duel_count += 1
