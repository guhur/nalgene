from typing import List, Dict, Optional

node_types = {
    '%': 'phrase',
    '@': 'ref',
    '~': 'synonym',
    '$': 'value',
}

class Node:
    def __init__(self, key):
        self.type: str = 'word'
        self.passthrough: bool = False
        self.optional: bool = False
        self.position: bool = None

        # Parse type and options
        if not isinstance(key, str):
            import pdb; pdb.set_trace()
        if len(key) > 0:
            if key.endswith('='):
                self.passthrough = True
                key = key[:-1]
            type_key = key[0]
            if type_key in node_types:
                self.type = node_types[type_key]
        else:
            self.type = 'root?'
        self.key: str = key

        self.parent: Optional[Node] = None
        self.children: List[Node] = []
        self.children_by_key: Dict[str, Node] = {}

    @property
    def printable_key(self):
        if self.type == 'word':
            return self.parent.key + '.' + self.key
        else:
            return self.key

    def __str__(self):
        return self.str(0)

    def __getitem__(self, key) -> "Node":
        # print('[__getitem__]', self, key)
        if isinstance(key, list):
            return self.descend(key)
        elif isinstance(key, str):
            if key in self.children_by_key:
                return self.children_by_key[key]
            else:
                # return None
                return Node(key)
 
        else:
            return self.children[key]

    def __setitem__(self, key, value):
        self.add(Node(key).add(value))

    def __contains__(self, key):
        keys = list(self.children_by_key.keys()) 
        #keys = [k.split('.')[-1] for k in keys]
        return key in keys

    def __len__(self):
        return len(self.children)

    def __iter__(self):
        self.iter_c = 0
        return self

    def __next__(self):
        if self.iter_c >= len(self.children):
            raise StopIteration
        else:
            child = self.children[self.iter_c]
            self.iter_c += 1
            return child

    @property
    def value(self):
        str = ""
        for child in self.children:
            str += child.key + " "
        return str

    def split(self, split):
        return self.key.split(split)

    def descend(self, keys):
        child = self[keys[0]]
        if len(keys) == 1:
            return child
        else:
            return child.descend(keys[1:])

    @property
    def is_root(self):
        return self.parent == None

    @property
    def is_leaf(self):
        return len(self.children) == 0

    @property
    def is_leaf_word(self):
        return self.type == 'word' and self.is_leaf

    def str(self, indent=0):
        if self.is_leaf_word:
            s = ' '
        else:
            s = (' ' * indent * 4)
            s += '( '
        s += str(self.key)
        if self.position != None:
            s += ' ' + str(self.position)
        ci = 0
        for child in self.children:
            if self.in_flat or not child.is_leaf_word:
                s += "\n"
            if self.in_flat:
                s += str(ci)
            ci += 1
            s += child.str(indent + 1)
        if not self.is_leaf_word: s += ' )'
        return s

    @property
    def in_flat(self):
        return self.key == '>'

    def to_json(self):
        children = []
        for child in self.children:
            if child.is_leaf_word:
                children += [child.key]
            else:
                children += [child.to_json()]
        return {
            'key': self.key,
            'position': self.position,
            'children': children
        }

    @property
    def raw_str(self):
        s = ""
        if self.is_leaf:
            return self.key
        elif self.type == 'seq':
            return ' '.join([c.key for c in self.children])
        for child in self.children:
            s += child.raw_str + " "
        return s.strip()

    def add(self, child, type=None):
        if not isinstance(child, Node):
            child = Node(child)
        if type != None:
            child.type = type
        self.children.append(child)
        self.children_by_key[child.key] = child
        child.parent = self

    def merge(self, child, type=None):
        if not isinstance(child, Node):
            child = Node(child)
        for child_child in child.children:
            if type != None:
                child_child.type = type
            self.children.append(child_child)
            self.children_by_key[child_child.key] = child_child
        return self

    def add_at(self, child, indexes):
        if len(indexes) == 1:
            return self.add(child)
        else:
            return self[indexes[0]].add_at(child, indexes[1:])

    @property
    def is_array(self):
        if len(self.children) == 0:
            return False
        for child in self.children:
            if not child.is_leaf:
                return False
        return True

    def map_leaves(self, f):
        for child in self.children:
            if child.is_leaf:
                f(child)
            else:
                child.map_leaves(f)

    def has_parent(self, type, parent_line=[]):
        if self.parent == None:
            return False, None
        elif self.parent.type == type:
            parent_line = [self.parent.key, self.key] + parent_line
            return True, parent_line
        else:
            parent_line = [self.key] + parent_line
            return self.parent.has_parent(type, parent_line)

