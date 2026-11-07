from collections.abc import Callable

type Maybe[T] = T | None


def just[T](value: T) -> Maybe[T]:
    return value


def none[T]() -> Maybe[T]:
    return None


def map[T, U](f: Callable[[T], U], x: Maybe[T]) -> Maybe[U]:
    if x is None:
        return None
    else:
        return f(x)


def flatten[T](x: Maybe[Maybe[T]]) -> Maybe[T]:
    if x is None:
        return None
    else:
        return x


def or_else[T](x: Maybe[T], y: Maybe[T]) -> Maybe[T]:
    if x is None:
        return y
    else:
        return x


def fold[T](x: list[Maybe[T]]) -> Maybe[list[T]]:
    if any(v is None for v in x):
        return None
    else:
        return [v for v in x if v is not None]


def is_just[T](x: Maybe[T]) -> bool:
    return x is not None


def is_none[T](x: Maybe[T]) -> bool:
    return x is None
