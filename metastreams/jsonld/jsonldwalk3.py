## begin license ##
#
# "Metastreams Json LD" provides utilities for handling json-ld data structures
#
# Copyright (C) 2022, 2024 Seecr (Seek You Too B.V.) https://seecr.nl
#
# This file is part of "Metastreams Json LD"
#
# "Metastreams Json LD" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# "Metastreams Json LD" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with "Metastreams Json LD"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

from inspect import isfunction, currentframe
from operator import attrgetter
from functools import reduce
from pprint import pformat
from copy import copy
import sys

"""
         13669367 function calls (10903180 primitive calls) in 3.850 seconds

   Ordered by: internal time

   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
2946891/180704    1.900    0.000    3.640    0.000 jsonldwalk3.py:84(handle)
  6154520    0.422    0.000    0.422    0.000 {method 'get' of 'dict' objects}
   180704    0.235    0.000    2.067    0.000 jsonldwalk3.py:76(handle)
   391657    0.216    0.000    0.334    0.000 didl.py:25(map_predicate_to_ids_fn)
   180704    0.189    0.000    0.264    0.000 didl.py:100(literal_mainEntityOfPage)
   115554    0.173    0.000    0.181    0.000 didl.py:40(literal_workExample)
   500201    0.161    0.000    0.196    0.000 didl.py:129(<lambda>)
   391657    0.118    0.000    0.118    0.000 didl.py:26(<listcomp>)
   180704    0.077    0.000    3.717    0.000 jsonldwalk3.py:93(walk_fn)
   180704    0.075    0.000    0.075    0.000 didl.py:101(<listcomp>)
  1042350    0.071    0.000    0.071    0.000 jsonldwalk3.py:108(ignore_assert_fn)
   180704    0.066    0.000    3.783    0.000 didl.py:201(didl2schema)
   180704    0.046    0.000    0.067    0.000 cProfile.py:117(__exit__)
   500201    0.036    0.000    0.036    0.000 jsonldwalk3.py:115(ignore_silently)
   180704    0.022    0.000    0.022    0.000 jsonldwalk3.py:133(map_predicate_fn)
   180704    0.021    0.000    0.021    0.000 jsonldwalk3.py:128(identity)
   180704    0.021    0.000    0.021    0.000 {method 'disable' of '_lsprof.Profiler' objects}


LAST: 13f6f29c-09d0-11ed-8d25-9f009bfa3105
RECORDS: 191787
RATE: 8417.154533366092
"""


def iterate(f, v):
    while v:
        yield v
        v = f(v)


def trace(locals_from_stack):
    return "".join(
        f"\n{n*'-'}> {p}"
        for n, p in enumerate(lokals["__key__"] for lokals in locals_from_stack)
    )


def locals_with_key():
    return [
        fl
        for fl in (
            tb.tb_frame.f_locals
            for tb in iterate(attrgetter("tb_next"), sys.exc_info()[2])
        )
        if "__key__" in fl
    ]


def compile(rules):

    # recursively compile everything
    rules = copy(rules)
    for predicate, subrule in rules.items():
        if type(subrule) is dict:
            rules[predicate] = compile(subrule)

    get = rules.get
    if "*" in rules:
        default = rules["*"]
    else:
        keys = set(rules.keys()) if rules else {}

        def default(a, s, p=None, os=None, **opts):
            e = LookupError(f"No rule for '{p}' in {keys}")
            e.subject = (
                s if s is not None else os[0]
            )  # called by __switch__ without subject
            raise e

    all_rule = get("__all__")

    if "__key__" in rules:
        key_fn = rules["__key__"]

        def handle(accu, subject, predicate, objects, **opts):
            if all_rule is not None:
                accu = all_rule(accu, subject, predicate, objects, **opts)
            for subject in objects:
                for predicate in subject:
                    objects = subject[predicate]
                    __key__ = key_fn(accu, subject, predicate, objects)
                    accu = get(__key__, default)(
                        accu, subject, predicate, objects, **opts
                    )
            return accu

    elif "__switch__" in rules:
        switch_fn = rules["__switch__"]

        def handle(accu, subject, predicate, objects, **opts):
            if all_rule is not None:
                accu = all_rule(accu, subject, predicate, objects, **opts)
            for subject in objects:
                __key__ = switch_fn(accu, subject)
                accu = get(__key__, default)(accu, None, None, (subject,), **opts)
            return accu

    else:
        # this is the thinnest bottleneck
        def handle(accu, subject, predicate, objects, **opts):
            if (
                all_rule is not None
            ):  # TODO move this check to compile time (use exec to dynamically compile handle with/out all_rule)
                accu = all_rule(accu, subject, predicate, objects, **opts)
            for subject in objects:
                for __key__ in subject:
                    accu = get(__key__, default)(
                        accu, subject, __key__, subject[__key__], **opts
                    )
            return accu

    return handle


def walk(rules, catch=True):
    w = compile(rules)

    def walk_fn(subject, accu=None, **opts):
        accu = {} if accu is None else accu
        try:
            return w(accu, None, None, (subject,), **opts)
        except Exception as e:
            if catch:
                locals_from_stack = locals_with_key()
                subject = locals_from_stack[-1].get("subject")
                raise Exception(
                    f"{e.__class__.__name__}: {str(e)} at:{trace(locals_from_stack)} while processing:\n{pformat(subject)}"
                ) from e
            raise e

    return walk_fn


""" Some auxilary rules (not tested here) on top of Walk, that are generic enough to place here. """


def do_assert(s, expected, param):
    if callable(expected) and expected(param) or expected == param:
        return True
    e = AssertionError(param)
    e.subject = s
    raise e


def ignore_assert(*, s=None, p=None, os=None):
    """ignores subtree, applying asserts when given"""
    assert s or p or os, "specify at least one assert, or use ignore_silently"

    def ignore_assert_fn(a, s_, p_, os_):
        # assert s is None or isfunction(s) and s(s_) or s == s_, s_A
        assert s is None or do_assert(s_, s, s_)
        assert p is None or do_assert(s_, p, p_)
        assert os is None or do_assert(s_, os, os_)
        return a

    return ignore_assert_fn


def ignore_silently(a, *_, **__):
    return a


def unsupported(_, __, p, ___):
    raise Exception(f"Unsupported predicate '{p}'")


def all_values_in(*values):
    vs = set(values)

    def all_values_in_fn(os):
        return all(o["@value"] in vs for o in os)

    return all_values_in_fn


def identity(a, _, p, os):
    a[p] = os
    return a


def map_predicate(p):
    def map_predicate_fn(a, _, __, os):
        a[p] = os
        return a

    return map_predicate_fn


def map_predicate2(p, normalize=tuple):
    def map_predicate_fn(a, _, __, os):
        old = a.setdefault(p, ())
        a[p] = old + normalize(os)
        return a

    return map_predicate_fn


def l2t_fn(a, s, p, os):
    a[p] = tuple(list2tuple(o) for o in os) if type(os) is list else os
    return a


l2t_walk = walk({"*": l2t_fn})


def list2tuple(d):
    return l2t_walk(d) if type(d) is dict else d


def t2l_fn(a, s, p, os):
    a[p] = list(tuple2list(o) for o in os) if isinstance(os, (tuple, list)) else os
    return a


t2l_walk = walk({"*": t2l_fn})


def tuple2list(d):
    return t2l_walk(d) if isinstance(d, dict) else d


### old stuff with index
def node_index(j):
    # from jsonld2document from metastreams.index
    """index all (top level) nodes by their @id"""
    if "@graph" in j:
        j = j["@graph"]
    return {m["@id"]: m for m in j if "@id" in m}


__all__ = [
    "walk",
    "ignore_assert",
    "ignore_silently",
    "unsupported",
    "map_predicate2",
    "map_predicate",
    "identity",
    "all_values_in",
    "list2tuple",
    "node_index",
    "tuple2list",
]
