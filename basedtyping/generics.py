"""unlike the generics in other modules, these ones are meant to be imported to save you from the boilerplate"""

from typing import TypeVar

from basedtyping.callables import AnyFunction

T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)
T_cont = TypeVar("T_cont", contravariant=True)
Fn = TypeVar("Fn", bound=AnyFunction)
Self = TypeVar("Self")
