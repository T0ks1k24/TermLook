"""Binary split trees: leaves are pane IDs, branches own direction and ratio."""
def branch(axis, first, second, ratio=0.5):
    return {'axis': axis, 'ratio': ratio, 'first': first, 'second': second}


def leaves(tree):
    if isinstance(tree, str):
        return [tree]
    return leaves(tree['first']) + leaves(tree['second'])


def replace(tree, pane_id, replacement):
    if isinstance(tree, str):
        return replacement if tree == pane_id else tree
    return branch(tree['axis'], replace(tree['first'], pane_id, replacement),
                  replace(tree['second'], pane_id, replacement), tree['ratio'])


def remove(tree, pane_id):
    if isinstance(tree, str):
        return None if tree == pane_id else tree
    first, second = remove(tree['first'], pane_id), remove(tree['second'], pane_id)
    if first is None:
        return second
    if second is None:
        return first
    return branch(tree['axis'], first, second, tree['ratio'])


def default_tree(ids):
    if len(ids) == 1:
        return ids[0]
    if len(ids) == 2:
        return branch('horizontal', *ids)
    return branch('vertical', branch('horizontal', ids[0], ids[1]), default_tree(ids[2:]))


def encode(tree, ids):
    if isinstance(tree, str):
        return ids.index(tree)
    return branch(tree['axis'], encode(tree['first'], ids), encode(tree['second'], ids), tree['ratio'])


def decode(data, ids):
    """Validate bounded persisted trees and map indices to fresh session IDs."""
    def visit(node, depth=0):
        if depth > 3:
            raise ValueError('Split tree too deep')
        if type(node) is int and 0 <= node < len(ids):
            return ids[node]
        if not isinstance(node, dict) or node.get('axis') not in ('horizontal', 'vertical'):
            raise ValueError('Invalid split')
        ratio = node.get('ratio', 0.5)
        if type(ratio) not in (int, float) or not 0.05 <= ratio <= 0.95:
            raise ValueError('Invalid split ratio')
        return branch(node['axis'], visit(node.get('first'), depth + 1),
                      visit(node.get('second'), depth + 1), ratio)
    try:
        tree = visit(data)
        if sorted(leaves(tree)) != sorted(ids):
            raise ValueError('Split leaves do not match panes')
        return tree
    except (ValueError, TypeError):
        return default_tree(ids)
