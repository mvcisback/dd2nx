from typing import Hashable, List, Set, TypeVar, Optional

import attr
import dd
import networkx as nx

Node = TypeVar("Node")


def leaf(node: Node) -> bool:
    return node.var is None


def node_name(node):
    idx = int(node)
    if isinstance(node, dd.autoref.Function):
        idx = abs(idx)
    else:
        idx &= -1 << 1
    return node.var, idx


@attr.s(repr=False)
class Queue:
    _visited: Set[Hashable] = attr.ib(factory=set)
    _stack: List[Node] = attr.ib(factory=list)

    def visited(self, node) -> bool:
        return node_name(node) in self._visited

    def push(self, node: Node):
        if not self.visited(node):
            self._visited.add(node_name(node))
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


def add_node_to_graph(g, node, pydot=False):
    if leaf(node):
        return

    curr_name = node_name(node)

    g.add_node(curr_name, var=node.var, lvl=node.level)

    for child, val in [(node.low, 0), (node.high, 1)]:
        add_edge(g, curr_name, child, decision=val, pydot=pydot)


def add_edge(g, curr_name, child, decision=None, pydot=False):
    payload = {"decision": decision, "negated": child.negated}
    if pydot:
        if decision is None:
            decision = True
        payload["style"] = "solid" if decision else "dashed"
        payload["arrowhead"] = "dot" if child.negated else "normal"

    g.add_edge(curr_name, node_name(child), **payload)


def to_nx(bexpr, pydot=False):
    """Convert BDD to `networkx.MultiDiGraph`.
    The resulting graph has:
      - nodes labeled with:
        - `level`: `int` from -1 to depth of the bdd, where
           -1 is a dummy start node.
        - `var`: `str` representing which variable this corresponds
           to.
      - edges labeled with:
        - `value`: `False` for low/"else", `True` for high/"then"
        - `negated`: `True` if target node is negated
    """
    g = nx.MultiDiGraph()
    g.add_node("<START>", var=None, level=-1)
    add_edge(g, "<START>", bexpr, pydot)

    queue = Queue()
    queue.push(bexpr)

    while not queue.empty:
        node = queue.pop()
        queue.push_unvisited_children(node)
        add_node_to_graph(g, node, pydot)

    return g
