class _Unset:
    def __repr__(self):
        return "<Unset>"

    def __eq__(self, other):
        return isinstance(other, _Unset)


Unset = _Unset()
