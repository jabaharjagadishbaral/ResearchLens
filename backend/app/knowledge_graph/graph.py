"""Knowledge graph: extraction from PaperAnalysis + in-memory store + Neo4j adapter (Neo4j untested here)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.analysis.paper import PaperAnalysis


@dataclass(frozen=True)
class Node:
    kind: str
    name: str


@dataclass(frozen=True)
class Edge:
    src: Node
    rel: str
    dst: Node
    page: int | None = None


def build_graph(papers: list[PaperAnalysis]) -> tuple[set[Node], set[Edge]]:
    nodes: set[Node] = set()
    edges: set[Edge] = set()
    for p in papers:
        pn = Node("Paper", p.title)
        nodes.add(pn)
        for a in p.authors:
            n = Node("Author", a); nodes.add(n); edges.add(Edge(pn, "AUTHORED_BY", n))
        for f in p.models:
            n = Node("Model", f.value); nodes.add(n); edges.add(Edge(pn, "USES_MODEL", n, f.page))
        for f in p.datasets:
            n = Node("Dataset", f.value); nodes.add(n); edges.add(Edge(pn, "USES_DATASET", n, f.page))
        for name, f in p.metrics.items():
            n = Node("Metric", name); nodes.add(n); edges.add(Edge(pn, "EVALUATES_ON", n, f.page))
    return nodes, edges


class GraphStore(ABC):
    @abstractmethod
    def write(self, nodes: set[Node], edges: set[Edge]) -> None: ...

    @abstractmethod
    def neighbors(self, node: Node) -> list[Edge]: ...


class InMemoryGraphStore(GraphStore):
    def __init__(self) -> None:
        self.nodes: set[Node] = set()
        self.edges: set[Edge] = set()

    def write(self, nodes, edges) -> None:
        self.nodes |= nodes
        self.edges |= edges

    def neighbors(self, node: Node) -> list[Edge]:
        return [e for e in self.edges if e.src == node or e.dst == node]


class Neo4jGraphStore(GraphStore):  # pragma: no cover - needs a running Neo4j
    def __init__(self, uri: str, user: str, password: str) -> None:
        from neo4j import GraphDatabase
        self._driver = GraphDatabase.driver(uri, auth=(user, password))

    def write(self, nodes, edges) -> None:
        with self._driver.session() as s:
            for n in nodes:
                s.run(f"MERGE (:{n.kind} {{name: $name}})", name=n.name)
            for e in edges:
                s.run(f"MATCH (a:{e.src.kind} {{name:$a}}), (b:{e.dst.kind} {{name:$b}}) "
                      f"MERGE (a)-[:{e.rel}]->(b)", a=e.src.name, b=e.dst.name)

    def neighbors(self, node: Node) -> list[Edge]:
        raise NotImplementedError("use Cypher queries from the API layer")
