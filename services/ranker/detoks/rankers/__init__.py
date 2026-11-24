"""Ranker registry. To add a ranker variant (e.g. an ablation), subclass Ranker and register it here."""
from ..catalog import Catalog
from .base import FeedStatus, RankContext, Ranked, Ranker, Term
from .baseline import BaselineRanker
from .detoks import DetoksRanker

RANKERS: dict[str, type[Ranker]] = {
    BaselineRanker.name: BaselineRanker,
    DetoksRanker.name: DetoksRanker,
}


def make_rankers(catalog: Catalog) -> dict[str, Ranker]:
    return {name: cls(catalog) for name, cls in RANKERS.items()}


__all__ = ["RANKERS", "make_rankers", "Ranker", "Ranked", "RankContext", "Term", "FeedStatus",
           "BaselineRanker", "DetoksRanker"]
