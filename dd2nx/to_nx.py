from functools import partial
from typing import Hashable, List, Set, TypeVar, Optional, Callable

import attr
import dd
import networkx as nx

Node = TypeVar("Node")
BDD = TypeVar("BDD")


def leaf(node: Node) -> bool:
    return node.var is None


def node_name(node, merge_negated=True):
    idx = int(node)
    if merge_negated:
        if isinstance(node, dd.autoref.Function):
            idx = abs(idx)
        else:
            idx &= -1 << 1

    return node.var, idx


@attr.s(repr=False, auto_attribs=True)
class Queue:
    node_name: Callable[[Node], Hashable] = node_name
    _visited: Set[Hashable] = attr.ib(factory=set)
    _stack: List[Node] = attr.ib(factory=list)

    def visited(self, node) -> bool:
        return self.node_name(node) in self._visited

    def push(self, node: Node):
        if not self.visited(node):
            self._visited.add(self.node_name(node))
            self._stack.append(node)

    def pop(self) -> Optional[Node]:
        if not self.empty:
            return self._stack.pop()

    def push_unvisited_children(self, node: Node):
        if leaf(node):
            return

        for child in [node.low, node.high]:
            self.push(child)

    def __len__(self) -> int:
        return len(self._stack)

    @property
    def empty(self) -> bool:
        return len(self) == 0

    def __repr__(self):
        return f"Visited: {self._visited}\nStack: {self._stack}"


@attr.s(auto_attribs=True)
class Graph:
    g: nx.MultiDiGraph = attr.ib(factory=nx.MultiDiGraph)
    node_name: Callable[[Node], Hashable] = node_name
    pydot: bool = False

    def add(self, node: Node):
        if leaf(node):
            return

        curr_name = self.node_name(node)

        self.g.add_node(curr_name, var=node.var, lvl=node.level)

        for child, val in [(node.low, 0), (node.high, 1)]:
            self.add_edge(curr_name, child, decision=val)

    def add_edge(self, curr_name, child, decision=None):
        payload = {"decision": decision, "negated": child.negated}
        if self.pydot:
            if decision is None:
                decision = True
            payload["style"] = "solid" if decision else "dashed"
            payload["arrowhead"] = "dot" if child.negated else "normal"

        self.g.add_edge(curr_name, node_name(child), **payload)


def to_nx(bexpr, pydot=False, merge_negated=True):
    """Convert BDD to `networkx.MultiDiGraph`.
    The resulting graph has:
      - nodes labeled with:
        - `level`: `int` from 0 to depth of the bdd.
        - `var`: `str` representing which variable this corresponds
           to.
      - edges labeled with:
        - `value`: `False` for low/"else", `True` for high/"then"
        - `negated`: `True` if target node is negated
      - A dummy initial node called "<START>". The edge from this
        node to the first decision indicates if the entire BDD
        should be negated.
    """
    _node_name = partial(node_name, merge_negated=merge_negated)
    graph = Graph(pydot=pydot, node_name=_node_name)

    queue = Queue(node_name=_node_name)
    queue.push(bexpr)

    while not queue.empty:
        node = queue.pop()
        queue.push_unvisited_children(node)
        graph.add(node)

    # Add dummy node to make algorithms easier.
    graph.add_edge("<START>", bexpr)
    return graph.g
