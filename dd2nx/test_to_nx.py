from functools import reduce

try:
    from dd.cudd import BDD
except ImportError:
    from dd.autoref import BDD


from dd2nx.to_nx import to_nx


def xor(x, y):
    return (x | y) & ~(x & y)


def test_to_nx():
    levels = {'x': 0, 'y': 1, 'z': 2, 'w': 3}
    manager = BDD()
    manager.declare(*levels.keys())
    manager.reorder(levels)

    x, y, z, w = map(manager.var, "xyzw")
    bexpr = reduce(xor, [x, y, z, w])

    g, negated = to_nx(bexpr, pydot=True)
    assert len(g.nodes) == 4 + 2
    assert len(g.edges) == 2*4 + 1
