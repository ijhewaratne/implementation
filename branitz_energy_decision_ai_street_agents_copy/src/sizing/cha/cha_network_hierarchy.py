"""
Utility helpers to describe the DH network for sizing purposes.

The original CHA project maintains a fairly involved hierarchy.  For the
agent workflow we only need a light abstraction that keeps track of which
buildings feed which pipes so that flows can be aggregated.  The
``CHANetworkHierarchyManager`` below expects callers to provide the
associations directly (for example by walking ``dual_topology``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Mapping, Set


@dataclass
class NetworkPipeDescription:
    """Minimal pipe description used for flow aggregation and sizing."""

    pipe_id: str
    length_m: float
    pipe_type: str  # supply / return / service
    street_id: str | None = None
    connected_buildings: Set[str] = field(default_factory=set)


class CHANetworkHierarchyManager:
    """
    Lightweight hierarchy helper.

    Responsibilities:
      * keep a catalogue of pipes (length/type metadata),
      * remember which buildings are downstream of each pipe,
      * expose convenience mappings for flow aggregation.
    """

    def __init__(self) -> None:
        self._pipes: Dict[str, NetworkPipeDescription] = {}

    # ------------------------------------------------------------------ #
    # Pipe registration
    # ------------------------------------------------------------------ #

    def register_pipe(
        self,
        pipe_id: str,
        length_m: float,
        pipe_type: str,
        street_id: str | None = None,
        connected_buildings: Iterable[str] | None = None,
    ) -> None:
        description = self._pipes.get(pipe_id)
        if description is None:
            description = NetworkPipeDescription(
                pipe_id=pipe_id,
                length_m=length_m,
                pipe_type=pipe_type,
                street_id=street_id,
            )
            self._pipes[pipe_id] = description
        else:
            # Update existing metadata if we learn something new
            description.length_m = max(description.length_m, length_m)
            if description.street_id is None:
                description.street_id = street_id

        if connected_buildings:
            description.connected_buildings.update(str(b) for b in connected_buildings)

    def bulk_register(
        self,
        pipe_descriptions: Iterable[NetworkPipeDescription],
    ) -> None:
        for desc in pipe_descriptions:
            self.register_pipe(
                pipe_id=desc.pipe_id,
                length_m=desc.length_m,
                pipe_type=desc.pipe_type,
                street_id=desc.street_id,
                connected_buildings=desc.connected_buildings,
            )

    # ------------------------------------------------------------------ #
    # Accessors used by the flow/sizing engines
    # ------------------------------------------------------------------ #

    @property
    def pipes(self) -> Mapping[str, NetworkPipeDescription]:
        return self._pipes

    def pipe_building_map(self) -> Dict[str, List[str]]:
        """
        Returns a ``pipe_id -> [building_id, ...]`` mapping suitable for
        consumption by ``CHAFlowCalculationEngine.aggregate_network_flows``.
        """
        return {
            pipe_id: sorted(description.connected_buildings)
            for pipe_id, description in self._pipes.items()
        }

    # Convenience helper used during integration tests
    def clear(self) -> None:
        self._pipes.clear()

