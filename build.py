from __future__ import annotations

from setuptools import Extension


def build(setup_kwargs):
    print("Put your build code here!")
    setup_kwargs["ext_modules"] = [
        Extension(
            name="basedtyping.type_alias_value_getter", sources=["c/type_alias_value_getter.c"]
        )
    ]
