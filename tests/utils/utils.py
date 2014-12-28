

def assert_object(obj, **kwargs):
    for k, v in kwargs.items():
        v2 = getattr(obj, k)
        try:
            assert v == v2
        except AssertionError:
            raise ValueError('Value {} does not match {}'.format(v, v2))
