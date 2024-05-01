## begin license ##
#
# "Metastreams Json LD" provides utilities for handling json-ld data structures
#
# Copyright (C) 2024 Seecr (Seek You Too B.V.) https://seecr.nl
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

from .jsonldwalk3 import (
    walk,
    ignore_silently,
    ignore_assert,
    identity,
    list2tuple,
    node_index,
    tuple2list,
    map_predicate2,
)
import pytest


def test_simple_basics():
    r = []
    w = walk({"a": lambda *a: r.append(a)})
    w({"a": "whatever-is-here"})
    assert r.pop() == ({}, {"a": "whatever-is-here"}, "a", "whatever-is-here")
    w({"a": [42]})
    assert r.pop() == ({}, {"a": [42]}, "a", [42])


def test_nested_rule():
    r = []
    w = walk(
        {
            "a": {
                "b": {
                    "c": lambda *a: r.append(a),
                },
            },
        }
    )
    w({"a": [{"b": [{"c": 42}]}]})
    assert r.pop() == ({}, {"c": 42}, "c", 42)
    with pytest.raises(Exception) as e:
        w({"a": [{"b": 42}]})
    assert (
        str(e.value)
        == "TypeError: 'int' object is not iterable at:\n> a\n-> b while processing:\n{'b': 42}"
    )


def test_default_rule():
    r = []
    rules = {"*": lambda a, s, p, o: r.append((p, "default"))}
    j0 = {"a/a": 42, "a/b": 2}
    walk(rules)(j0)
    assert r.pop() == ("a/b", "default")
    assert r.pop() == ("a/a", "default")

    # should have same result
    w = walk({"a": rules})
    w({"a": [j0]})
    assert r.pop() == ("a/b", "default")
    assert r.pop() == ("a/a", "default")

    # should have same result
    w = walk({"*": rules})
    w({"a": [j0]})
    assert r.pop() == ("a/b", "default")
    assert r.pop() == ("a/a", "default")


def test_values():
    r = []
    rules = {
        "@value": lambda *a: r.append(a),  # returns None
        "*": lambda *a: r.append(a),
    }
    w = walk(rules)
    s = {"@value": "hello", "b/b": [{"id": "16"}]}
    w(s)
    assert r.pop() == (None, s, "b/b", [{"id": "16"}])
    assert r.pop() == ({}, s, "@value", "hello")

    # should have same result
    w = walk({"a": rules})
    w({"a": [s]})
    assert r.pop() == (None, s, "b/b", [{"id": "16"}])
    assert r.pop() == ({}, s, "@value", "hello")


def test_modifying_input_is_not_allowed():
    r = []
    rules = {
        "a/a": lambda a, s, p, o: r.append(s.pop("a/b") * o),
        "a/b": ignore_silently,
    }
    j0 = {"a/b": 2, "a/a": 42}
    with pytest.raises(Exception) as e:
        walk(rules)(j0)
    assert str(e.value).startswith(
        "RuntimeError: dictionary changed size during iteration at:"
    )


def test_reduce_returned_values():
    j = {"a": 42, "b": 16}
    r = walk({"a": lambda a, s, p, o: o, "*": lambda a, s, p, o: [42, (p, o)]})(j)
    assert r == [42, ("b", 16)]


def test_my_accu_plz():
    a = {}
    id_a = id(a)
    r = walk({"*": lambda a, s, p, os: a})({"a": 10}, accu=a)
    assert id(r) == id_a


def test_pass_kwargs():
    def accept_kwargs(a, s, p, os, **opts):
        return a | {p: {"os": os, "opts": opts}}

    w = walk(
        {
            "aap": accept_kwargs,
        }
    )
    r = w({"aap": ("AAP",)}, kwarg="something")
    assert r == {"aap": {"os": ("AAP",), "opts": {"kwarg": "something"}}}

    w = walk(
        {
            "__key__": lambda a, s, p, os: "key:" + p,
            "key:aap": accept_kwargs,
        }
    )
    r = w({"aap": ("AAP",)}, kwarg="something")
    assert r == {"aap": {"os": ("AAP",), "opts": {"kwarg": "something"}}}

    w = walk(
        {
            "__switch__": lambda a, s: "switched",
            "switched": {
                "aap": accept_kwargs,
            },
        }
    )
    r = w({"aap": ("AAP",)}, kwarg="something")
    assert r == {"aap": {"os": ("AAP",), "opts": {"kwarg": "something"}}}

    w = walk(
        {
            "__all__": lambda a, s, p, os, **opts: a | {"all_opts": opts},
            "aap": accept_kwargs,
        }
    )
    r = w({"aap": ("AAP",)}, kwarg="something")
    assert r == {
        "aap": {"os": ("AAP",), "opts": {"kwarg": "something"}},
        "all_opts": {"kwarg": "something"},
    }


def test_append_to_list():
    def append(a, s, p, os):
        a.setdefault(p, []).extend(os)
        return a

    w = walk({"*": append})
    r = w({"a": [1]})
    r = w({"a": [2]}, accu=r)
    assert r == {"a": [1, 2]}


def test_custom_key():
    r = []
    q = []
    rules = {
        "__key__": lambda *a: r.append(a),  # returns None
        None: lambda *a: q.append(a),
    }
    w = walk(rules)
    w({"a": 42})
    assert r.pop() == ({}, {"a": 42}, "a", 42)
    assert q.pop() == ({}, {"a": 42}, "a", 42)

    # should have same results
    w = walk({"b": rules})
    w({"b": [{"a": 42}]})
    assert r.pop() == ({}, {"a": 42}, "a", 42)
    assert q.pop() == ({}, {"a": 42}, "a", 42)

    # should have same results
    w = walk({"b": rules, "__key__": lambda a, s, p, os: p})
    w({"b": [{"a": 42}]})
    assert r.pop() == ({}, {"a": 42}, "a", 42)
    assert q.pop() == ({}, {"a": 42}, "a", 42)


def test_custom_key_with_subwalk():
    r = []
    w = walk({"__key__": lambda a, s, p, os: p, "a": {"b": lambda *a: r.append(a)}})
    w({"a": [{"b": "identiteit"}]})
    assert r.pop() == ({}, {"b": "identiteit"}, "b", "identiteit")


def test_switch_toplevel():
    r1 = []
    r2 = []
    rules = {
        "__switch__": lambda a, s: s["@type"][0],
        "numbers": lambda *a: r1.append(a),
        "strings": lambda *a: r2.append(a),
    }
    w = walk(rules)
    w(
        {
            "@type": ["numbers"],
            "a": [42],
        }
    )
    assert r1.pop() == ({}, None, None, ({"@type": ["numbers"], "a": [42]},))
    assert r2 == []
    w(
        {
            "@type": ["strings"],
            "a": ["42"],
        }
    )
    assert r1 == []
    assert r2.pop() == ({}, None, None, ({"@type": ["strings"], "a": ["42"]},))

    # should have same results
    w = walk({"z": rules})
    w(
        {
            "z": [
                {
                    "@type": ["numbers"],
                    "a": [42],
                }
            ]
        }
    )
    assert r1.pop() == ({}, None, None, ({"@type": ["numbers"], "a": [42]},))
    assert r2 == []
    w(
        {
            "z": [
                {
                    "@type": ["strings"],
                    "a": ["42"],
                }
            ],
        }
    )
    assert r1 == []
    assert r2.pop() == ({}, None, None, ({"@type": ["strings"], "a": ["42"]},))


def test_switch_with_dict():
    w = walk(
        {
            "__switch__": lambda a, s: s["base"][0]["@value"],
            2: {
                "base": ignore_silently,
                "x": lambda a, s, p, os: a
                | {"result": [{"@value": 2 ** o["@value"]} for o in os]},
            },
            8: {
                "base": ignore_silently,
                "x": lambda a, s, p, os: a
                | {"result": [{"@value": 8 ** o["@value"]} for o in os]},
            },
        }
    )
    r = w({"base": [{"@value": 2}], "x": [{"@value": 3}]})
    assert r == {"result": [{"@value": 8}]}
    r = w({"base": [{"@value": 8}], "x": [{"@value": 3}]})
    assert r == {"result": [{"@value": 512}]}


def test_swith_in_swith():
    w = walk(
        {
            "__switch__": lambda a, s: s["a"],
            "1": {
                "__switch__": lambda a, s: s["x"][0]["y"][0],
                "koel": {
                    "a": ignore_assert(os="1"),
                    "x": identity,
                },
            },
        }
    )
    r = w({"a": "1", "x": [{"y": ["koel"]}]})
    assert r == {"x": [{"y": ["koel"]}]}


def test_with_type():
    r = []
    w = walk(
        {
            "__switch__": lambda *a: r.append(a),
            None: {"@type": identity},
        }
    )
    w({"@type": ["whatever-is-here"]})
    assert r.pop() == ({"@type": ["whatever-is-here"]}, {"@type": ["whatever-is-here"]})


def test_subwalk_from_mods():
    w = walk(
        {
            "__switch__": lambda a, s: s["@type"][0],
            "personal": {"@type": lambda a, s, p, os: a | {"type is": os}},
        }
    )
    r = w(
        {
            "@type": ["personal"],
        }
    )
    assert r == {"type is": ["personal"]}


def test_builtin_subwalk():
    w = walk({"a": {"b": identity}})
    r = w({"a": [{"b": 41}]})
    assert r == {"b": 41}  # NB subwalk flattens


def test_builtin_subwalk_stack_for_errors():
    w = walk(
        {
            "a": {"b": identity},
            "b": {
                "c": identity,
                "d": {},
            },
        }
    )
    with pytest.raises(Exception) as e:
        w({"b": [{"d": [{"e": 42}]}]})
    assert (
        str(e.value)
        == "LookupError: No rule for 'e' in {} at:\n> b\n-> d\n--> e while processing:\n{'e': 42}"
    )
    with pytest.raises(Exception) as e:
        w({"a": [{"X": [{"e": 42}]}]})
    assert (
        str(e.value)
        == "LookupError: No rule for 'X' in {'b'} at:\n> a\n-> X while processing:\n{'X': [{'e': 42}]}"
    )


##### More elaborate tests from old processor #####

from pyld import jsonld

dcterms = "http://purl.org/dc/terms/"
foaf = "http://xmlns.com/foaf/0.1/"
schema = "http://schema.org/"


def expand(data):
    """test helper"""
    data["@context"] = {"dcterms": dcterms, "schema": schema, "foaf": foaf}
    return jsonld.expand(data)


def set_if_absent(a, s, p, os):
    if p not in a:
        a[p] = os
    return a


rules = {
    "@id": set_if_absent,
    "@value": lambda a, s, p, v: a | {"@value": v},
    "@type": lambda a, s, p, v: a | {"@type": v},
    "*": lambda a, s, p, os: a | {p: [walk_one(o) for o in os]},
}
more_rules = {
    # NB: "(lambda x=42: ...)()" betekent "(let [x 42] ...)" als in Clojure.
    dcterms + "name": lambda a, s, p, os: a
    | (
        lambda name=os[0]["@value"].split(): {
            foaf + "givenName": [{"@value": name[0]}],
            foaf + "familyName": [{"@value": name[1]}],
        }
    )(),
    dcterms + "creator": lambda a, s, p, os: a | {p: [walk_one(o) for o in os]},
    dcterms + "title": lambda a, s, p, os: a | {schema + "name": os},
    foaf + "familyName": lambda a, s, p, os: a
    | {
        schema
        + "name": [
            {"@value": s.get(foaf + "givenName")[0]["@value"] + " " + os[0]["@value"]}
        ]
    },
    foaf + "givenName": ignore_silently,
    dcterms + "publisher": lambda a, s, p, os: a
    | {
        schema
        + "publisher": [
            {schema + "name": [o]} if "@value" in o else walk_one(o) for o in os
        ]
    },
    foaf + "name": lambda a, s, p, os: a | {schema + "name": [walk_one(o) for o in os]},
}

walk_one = walk(rules | more_rules)


def walk_all(objects):
    w = walk(rules | more_rules)
    accu = {}
    for o in objects:
        accu = w(o, accu=accu)
    return accu


def test_title():
    objects = expand({"dcterms:title": "Titel van een document"})
    assert len(objects) == 1
    o = objects[0]
    assert o[dcterms + "title"][0]["@value"] == "Titel van een document"
    n = walk_all(objects)  # default accu is {}
    assert n == {"http://schema.org/name": [{"@value": "Titel van een document"}]}


def test_title_lang():
    objects = expand(
        {
            "dcterms:title": [
                {"@value": "Titel van een document", "@language": "nl"},
                {"@value": "Title of a document", "@language": "en"},
                {"@value": "Titre d'un document", "@language": "fr"},
                {"@value": "Titel eines Dokuments", "@language": "de"},
            ]
        }
    )
    n = walk_all(objects)
    vs = n["http://schema.org/name"]
    assert len(vs) == 4
    assert vs[0] == {"@value": "Titel van een document", "@language": "nl"}
    assert vs[1] == {"@value": "Title of a document", "@language": "en"}
    assert vs[2] == {"@value": "Titre d'un document", "@language": "fr"}
    assert vs[3] == {"@value": "Titel eines Dokuments", "@language": "de"}


def test_keep_first_id():
    """NB: using walk with a list accumulates everything in one accu !"""
    m = walk_all(
        [{"@id": "first"}, {"@id": "second", schema + "about": [{"@id": "third"}]}]
    )
    assert m == {"@id": "first", "http://schema.org/about": [{"@id": "third"}]}


def test_list_of_values():
    m = walk_one({schema + "name": [{"@value": "aap"}, {"@value": "noot"}]})
    assert m == {schema + "name": [{"@value": "aap"}, {"@value": "noot"}]}


def test_types():
    m = walk_one({"@type": ["atype:A"]})
    assert m == {"@type": ["atype:A"]}


def test_recur():
    m = walk_one(
        {dcterms + "publisher": [{foaf + "name": [{"@value": "Aap noot mies"}]}]}
    )
    assert m == {
        schema + "publisher": [{schema + "name": [{"@value": "Aap noot mies"}]}]
    }


def test_insert_predicate():
    m = walk_one({dcterms + "publisher": [{"@value": "Aap noot mies"}]})
    assert m == {
        schema + "publisher": [{schema + "name": [{"@value": "Aap noot mies"}]}]
    }

    m = walk_one({dcterms + "publisher": [{"@value": "Aap"}, {"@value": "noot"}]})
    assert m == {
        schema
        + "publisher": [
            {schema + "name": [{"@value": "Aap"}]},
            {schema + "name": [{"@value": "noot"}]},
        ]
    }

    m = walk_one(
        {
            dcterms
            + "publisher": [
                {"@value": "Aap"},
                {dcterms + "title": [{"@value": "noot"}]},
            ]
        }
    )
    assert m == {
        schema
        + "publisher": [
            {schema + "name": [{"@value": "Aap"}]},
            {schema + "name": [{"@value": "noot"}]},
        ]
    }

    m = walk_one(
        {
            dcterms
            + "publisher": [{schema + "about": [{"@value": "noot"}]}, {"@value": "Aap"}]
        }
    )
    assert m == {
        schema
        + "publisher": [
            {schema + "about": [{"@value": "noot"}]},
            {schema + "name": [{"@value": "Aap"}]},
        ]
    }


def test_foaf_empty_given_name():
    object = expand({"dcterms:creator": {"foaf:givenName": []}})


def test_foaf_no_family_name():
    object = expand({"dcterms:creator": {"foaf:givenName": ["Voornaam"]}})


def test_combine_properties():
    object = expand(
        {
            "dcterms:creator": {
                "foaf:givenName": ["Voornaam"],
                "foaf:familyName": "Achternaam",
            }
        }
    )
    result = walk_one(object[0])
    assert result == {
        "http://purl.org/dc/terms/creator": [
            {"http://schema.org/name": [{"@value": "Voornaam Achternaam"}]}
        ]
    }


def test_split_properties():
    result = walk_one(
        {dcterms + "creator": [{dcterms + "name": [{"@value": "Voornaam Achternaam"}]}]}
    )
    assert result == {
        dcterms
        + "creator": [
            {
                foaf + "givenName": [{"@value": "Voornaam"}],
                foaf + "familyName": [{"@value": "Achternaam"}],
            }
        ]
    }


#    class accu:
#        subject: dict = field(default_factory=dict)
#        index: dict = field(default_factory=dict)


def test_flatten_expanded_round_trip():
    """flatten -> expand introduces blank nodes
    we make an index of all nodes so we can detect and recur into them
    """
    doc = {f"{dcterms}creator": {f"{foaf}name": "Piet Pietersen"}}
    flt = jsonld.flatten(
        doc, {}
    )  # this does not work => {'@graph': {'@container': '@id'}})
    exp = jsonld.expand(doc, {})
    flt_exp = jsonld.expand(flt, {})
    # print(json.dumps(flt, indent=2))
    # print(json.dumps(exp, indent=2))
    # print(json.dumps(flt_exp, indent=2))
    assert node_index(flt) == {
        "_:b0": {"@id": "_:b0", "http://purl.org/dc/terms/creator": {"@id": "_:b1"}},
        "_:b1": {"@id": "_:b1", "http://xmlns.com/foaf/0.1/name": "Piet Pietersen"},
    }
    assert node_index(exp) == {}
    assert node_index(flt_exp) == {
        "_:b0": {"@id": "_:b0", "http://purl.org/dc/terms/creator": [{"@id": "_:b1"}]},
        "_:b1": {
            "@id": "_:b1",
            "http://xmlns.com/foaf/0.1/name": [{"@value": "Piet Pietersen"}],
        },
    }


def test_list2tuple_basics():
    assert list2tuple({}) == {}
    assert list2tuple({1: [1]}) == {1: (1,)}
    assert list2tuple({1: [{2: []}, {3: [2, 3]}]}) == {1: ({2: ()}, {3: (2, 3)})}
    assert list2tuple(
        {
            schema + "identifier": [{"@id": "urn:nbn:nl:hs:25-20.500.12470/10"}],
            schema + "dateModified": [{"@value": "2020-08-15T01:50:06.598316Z"}],
        }
    ) == {
        "http://schema.org/identifier": ({"@id": "urn:nbn:nl:hs:25-20.500.12470/10"},),
        "http://schema.org/dateModified": ({"@value": "2020-08-15T01:50:06.598316Z"},),
    }


def test_tuple2list_basics():
    d = {}
    d1 = tuple2list(d)
    assert d1 == {}
    assert id(d) != id(d1)

    d = {1: (1,), 3: ["iets"]}
    td = tuple2list(d)
    d[3].append("anders")
    assert td == {1: [1], 3: ["iets"]}
    assert tuple2list({1: (1,)}) == {1: [1]}
    assert tuple2list({1: ({2: ()}, {3: (2, 3)})}) == {1: [{2: []}, {3: [2, 3]}]}
    assert tuple2list(
        {
            schema + "identifier": ({"@id": "urn:nbn:nl:hs:25-20.500.12470/10"},),
            schema
            + "dateModified": (
                {
                    "@value": "2020-08-15T01:50:06.598316Z",
                    "@type": "dateString",
                    "@language": "nl",
                },
            ),
            schema + "object": ({"@type": (schema + "Thing",)},),
        }
    ) == {
        "http://schema.org/identifier": [{"@id": "urn:nbn:nl:hs:25-20.500.12470/10"}],
        "http://schema.org/dateModified": [
            {
                "@value": "2020-08-15T01:50:06.598316Z",
                "@type": "dateString",
                "@language": "nl",
            }
        ],
        "http://schema.org/object": [{"@type": ["http://schema.org/Thing"]}],
    }


def test_tuple2list_subclass():
    class D(dict):
        pass

    assert tuple2list(D(a=(D(b=()),))) == {"a": [{"b": []}]}


def test_map_predicate2_normalize():
    mp = map_predicate2("new_p")
    assert mp(
        {
            "a": ({"@value": "A"},),
        },
        "s",
        "p",
        [{"@value": "p"}],
    ) == {"a": ({"@value": "A"},), "new_p": ({"@value": "p"},)}
    mp = map_predicate2(
        "new_p", lambda os: tuple({"@value": "Changed:" + w["@value"]} for w in os)
    )
    assert mp(
        {
            "a": ({"@value": "A"},),
        },
        "s",
        "p",
        [{"@value": "p"}],
    ) == {"a": ({"@value": "A"},), "new_p": ({"@value": "Changed:p"},)}


def test_key_to_change_something():
    rules = {
        "__key__": lambda a, s, p, os: "start" if p.startswith("start") else p,
        "start": map_predicate2("A"),
        "other": map_predicate2("B"),
    }
    w = walk(rules)
    a = w(
        {
            "start.aap": [{"@value": "aap"}],
            "start.noot": [{"@value": "noot"}],
            "other": [{"@value": "mies"}],
        }
    )
    assert a == {
        "A": ({"@value": "aap"}, {"@value": "noot"}),
        "B": ({"@value": "mies"},),
    }
