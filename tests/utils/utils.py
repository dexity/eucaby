

def assert_object(obj, **kwargs):
    for k, v in kwargs.items():
        value = getattr(obj, k)
        try:
            assert v == value
        except AssertionError:
            raise ValueError('Value {} does not match {}'.format(v, value))
