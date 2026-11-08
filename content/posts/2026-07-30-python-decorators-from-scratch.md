---
title: "Python Decorators, Built From Scratch"
description: "What a decorator actually is under the hood, built up in four small steps from a plain function wrapper to a parameterized decorator with functools.wraps."
category: "Python"
tags: [Python, Programming]
type: tutorial
---

Decorators look like magic syntax until you see that `@decorator` is just sugar for `func = decorator(func)`. This tutorial builds that understanding in four small, runnable steps.

## Step 1 — A function that wraps a function

```python
def loud(func):
    def wrapper(*args, **kwargs):
        print(f"calling {func.__name__}")
        return func(*args, **kwargs)
    return wrapper

def add(a, b):
    return a + b

add = loud(add)
print(add(2, 3))
# calling add
# 5
```

That's the entire mechanism. `loud` takes a function and returns a new function that does something extra around it.

## Step 2 — The `@` syntax

```python
@loud
def add(a, b):
    return a + b
```

is exactly equivalent to `add = loud(add)` from Step 1. The `@` symbol doesn't add any new capability — it's purely a more readable way to write the same reassignment.

## Step 3 — Preserving metadata with `functools.wraps`

Without help, the wrapped function loses its original name and docstring:

```python
print(add.__name__)  # 'wrapper' — not what you'd expect
```

::: note
This matters more than it looks — tools that inspect `__name__` or `__doc__` (debuggers, API documentation generators, `help()`) will show the wrapper's identity instead of the original function's, which makes debugging confusing.
:::

```python
from functools import wraps

def loud(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print(f"calling {func.__name__}")
        return func(*args, **kwargs)
    return wrapper

@loud
def add(a, b):
    return a + b

print(add.__name__)  # 'add'
```

## Step 4 — Decorators that take arguments

A decorator with parameters needs one more layer of nesting — a function that returns a decorator:

```python
def retry(times=3):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(times):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    print(f"attempt {attempt + 1} failed: {e}")
            raise last_error
        return wrapper
    return decorator

@retry(times=3)
def flaky_call():
    import random
    if random.random() < 0.7:
        raise ConnectionError("simulated failure")
    return "ok"
```

`retry(times=3)` runs first and returns `decorator`, which then wraps `flaky_call` exactly like `loud` did in Step 1 — the extra layer is only there to close over the `times` argument.

::: example
Class-based decorators follow the same idea but implement `__call__` instead of returning a nested function — useful when the decorator needs to hold state across calls, like a hit counter.
:::

## A quick reference

| Form | Expands to |
|---|---|
| `@loud` <br> `def f(): ...` | `f = loud(f)` |
| `@retry(times=3)` <br> `def f(): ...` | `f = retry(times=3)(f)` |

Once you can read `@decorator` as "reassign this name to the return value of a function call," the rest of the ecosystem — Flask's `@app.route`, pytest's `@pytest.fixture`, dataclasses' `@dataclass` — stops looking like special syntax and starts looking like ordinary functions.
