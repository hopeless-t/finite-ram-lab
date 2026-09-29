from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .controlled_spawn_transaction_bridge import (
    packet_from_touch,
    target_bundle_packet,
)
from .transaction_trace_observer import (
    apply_and_enrich_v2,
    observer_receipt_for_window,
)
from .transactional_reprime import Event, State, Transaction, reduce


@dataclass
class EpochArchive:
    tx: Transaction
    owner_counter: str | None = None
    verified_at_ns: int | None = None
    next_touch_index_since_verified: int | None = None
    packets: list[dict[str, Any]] = field(default_factory=list)
    control_events: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def start(cls, *, max_reprimes: int = 2) -> "EpochArchive":
        tx = reduce(Transaction(max_reprimes=max_reprimes), Event.ADMIT)
        return cls(tx=tx)

    def _assert_epoch(self, epoch: int) -> None:
        if int(epoch) != self.tx.epoch:
            raise ValueError(
                f"archive epoch={self.tx.epoch} cannot accept epoch={epoch}"
            )

    def apply_touch(
        self,
        *,
        epoch: int,
        phase: str,
        touch_number: int,
        touch: dict[str, Any],
        window: dict[str, Any],
        stock_cpu: int,
    ) -> dict[str, Any]:
        self._assert_epoch(epoch)
        receipt = observer_receipt_for_window(
            window,
            owner_counter=self.owner_counter,
            stock_cpu=stock_cpu,
            phase=phase,
        )
        packet = packet_from_touch(
            epoch=epoch,
            phase=phase,
            touch_number=touch_number,
            touch=touch,
            observer=receipt,
            stock_cpu=stock_cpu,
        )

        candidate_owner = receipt.get("discovered_owner_counter")
        owner_for_packet = self.owner_counter or candidate_owner

        tx_after, packet_v2, verified_at, next_index = apply_and_enrich_v2(
            self.tx,
            packet,
            owner_counter=owner_for_packet,
            marker_pre_ns=receipt.get("marker_pre_ns"),
            marker_post_ns=receipt.get("marker_post_ns"),
            verified_at_ns=self.verified_at_ns,
            touch_index_since_verified=self.next_touch_index_since_verified,
            unknown_emission_count=int(
                receipt.get("unknown_emission_count", 0)
            ),
        )

        if (
            self.tx.state is State.NORMALIZING
            and tx_after.state is State.VERIFIED
        ):
            if candidate_owner is None:
                raise ValueError("VERIFIED without epoch owner counter")
            self.owner_counter = candidate_owner

        self.tx = tx_after
        self.verified_at_ns = verified_at
        self.next_touch_index_since_verified = next_index
        self.packets.append(packet_v2)
        return packet_v2

    def apply_target_bundle(
        self,
        *,
        epoch: int,
        arm_id: str,
        touch_number: int,
        touches: list[dict[str, Any]],
        windows: list[dict[str, Any]],
        stock_cpu: int,
    ) -> dict[str, Any]:
        self._assert_epoch(epoch)
        if self.owner_counter is None:
            raise ValueError("TARGET requires epoch-local owner counter")
        if len(touches) != len(windows):
            raise ValueError("target touches/windows length mismatch")

        receipts = [
            observer_receipt_for_window(
                window,
                owner_counter=self.owner_counter,
                stock_cpu=stock_cpu,
                phase="TARGET",
            )
            for window in windows
        ]
        packet = target_bundle_packet(
            epoch=epoch,
            arm_id=arm_id,
            touches=touches,
            observers=receipts,
            stock_cpu=stock_cpu,
            touch_number=touch_number,
        )

        marker_pre_values = [
            int(r["marker_pre_ns"])
            for r in receipts
            if r.get("marker_pre_ns") is not None
        ]
        marker_post_values = [
            int(r["marker_post_ns"])
            for r in receipts
            if r.get("marker_post_ns") is not None
        ]
        marker_pre_ns = min(marker_pre_values) if marker_pre_values else None
        marker_post_ns = max(marker_post_values) if marker_post_values else None
        unknown = sum(
            int(r.get("unknown_emission_count", 0))
            for r in receipts
        )

        tx_after, packet_v2, verified_at, next_index = apply_and_enrich_v2(
            self.tx,
            packet,
            owner_counter=self.owner_counter,
            marker_pre_ns=marker_pre_ns,
            marker_post_ns=marker_post_ns,
            verified_at_ns=self.verified_at_ns,
            touch_index_since_verified=self.next_touch_index_since_verified,
            unknown_emission_count=unknown,
        )

        self.tx = tx_after
        self.verified_at_ns = verified_at
        self.next_touch_index_since_verified = next_index
        self.packets.append(packet_v2)
        return packet_v2

    def reprime(self, *, mode: str = "HARD_NEW_WORKER_CGROUP") -> None:
        before_epoch = self.tx.epoch
        self.tx = reduce(self.tx, Event.REPRIME)
        self.control_events.append(
            {
                "event": "REPRIME",
                "mode": mode,
                "from_epoch": before_epoch,
                "to_epoch": self.tx.epoch,
                "result_state": self.tx.state.value,
            }
        )

        # Epoch-local observer authority must never cross the boundary.
        self.owner_counter = None
        self.verified_at_ns = None
        self.next_touch_index_since_verified = None

    def commit(self) -> None:
        before = self.tx.state.value
        self.tx = reduce(self.tx, Event.COMMIT)
        self.control_events.append(
            {
                "event": "COMMIT",
                "epoch": self.tx.epoch,
                "from_state": before,
                "result_state": self.tx.state.value,
            }
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "transaction-epoch-archive-v1",
            "state": self.tx.state.value,
            "epoch": self.tx.epoch,
            "reprimes": self.tx.reprimes,
            "max_reprimes": self.tx.max_reprimes,
            "owner_counter": self.owner_counter,
            "verified_at_ns": self.verified_at_ns,
            "next_touch_index_since_verified": (
                self.next_touch_index_since_verified
            ),
            "packets": list(self.packets),
            "control_events": list(self.control_events),
        }
