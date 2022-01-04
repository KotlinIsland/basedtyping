# basedtyping

A collection of helpers and utilities to aid at dealing with types, both at static analysis and at runtime.

It's recommended to use [`basedmypy`](https://github.com/kotlinisland/basedmypy) when using `basedtyping`,
as there are specialised adaptations made to `basedmypy` to support some functionality of this package.


## Features
### `ReifiedGeneric`
A ``Generic`` where the type parameters are available at runtime and usable in ``isinstance`` and ``issubclass`` checks.

For example:
```py
class Foo(ReifiedGeneric[T]):
   def hi(self):
       print("Hi :)")

def foo(it: object):
    # no error, as the class is reified and can be checked at runtime
    if isinstance(it, Foo[int]): 
        print("wooow 😳")
```

### `assert_type`
A type-time function used for testing types:
```py
from typing import TYPE_CHECKING

if TYPE_CHECKING:
  assert_type[int](foo) # type error if `foo` isn't an `int`
```

### And many more!
