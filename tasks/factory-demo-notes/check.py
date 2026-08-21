#!/usr/bin/env python3
"""Evaluate the notes task using only the Python standard library."""

import json
import pathlib
import sys
import traceback


ROOT = pathlib.Path(__file__).resolve().parent


def load_notes(target):
    source_path = target / "notes.py"
    source = source_path.read_text(encoding="utf-8")
    namespace = {"__file__": str(source_path), "__name__": "candidate_notes"}
    exec(compile(source, str(source_path), "exec"), namespace)
    return namespace["Notes"]


def passes(test):
    try:
        test()
    except Exception:
        return False
    return True


def require(condition, message="check failed"):
    if not condition:
        raise AssertionError(message)


def requirement_checks(Notes):
    def r1():
        notes = Notes()
        first = notes.add("One", tags=("x",))
        second = notes.add("Two")
        result = notes.search()
        require([item["id"] for item in result] == [first, second])
        require(notes.search(query="", tags=None) == result)

    def r2():
        notes = Notes()
        title_hit = notes.add("Straße map", "elsewhere")
        body_hit = notes.add("Other", "Look in the HAYSTACK")
        notes.add("Miss", "nothing useful")
        require([note["id"] for note in notes.search("STRASSE")] == [title_hit])
        require([note["id"] for note in notes.search("haystack")] == [body_hit])
        require(len(notes.search("")) == 3)

    def r3():
        notes = Notes()
        both = notes.add("Both", tags=(" Work ", "Urgent"))
        work = notes.add("Work", tags=("work",))
        notes.add("Home", tags=("home",))
        require([note["id"] for note in notes.search(tags=(" WORK ",))] == [both, work])
        require([note["id"] for note in notes.search(tags=("work", "URGENT"))] == [both])
        require(len(notes.search(tags=[])) == 3)
        require(len(notes.search(tags=None)) == 3)

    def r4():
        notes = Notes()
        first = notes.add("One", tags=("tag",))
        second = notes.add("Two")
        result = notes.search()
        require([note["id"] for note in result] == sorted((first, second)))
        result[0]["title"] = "changed"
        result[0]["tags"].append("changed")
        require(notes.get(first)["title"] == "One")
        require(notes.get(first)["tags"] == ["tag"])

    def r5():
        notes = Notes()
        notes.add("One")
        output = notes.export_json()
        require(isinstance(output, str))
        document = json.loads(output)
        require(set(document) == {"schema_version", "notes"})
        require(document["schema_version"] == 1)
        require(isinstance(document["notes"], list))

    def r6():
        notes = Notes()
        first = notes.add("One", "Body", ("z", "a"))
        second = notes.add("Two", tags=("m",))
        exported = json.loads(notes.export_json())["notes"]
        require([note["id"] for note in exported] == [first, second])
        require(all(set(note) == {"id", "title", "body", "tags"} for note in exported))
        require(exported[0] == {"id": first, "title": "One", "body": "Body", "tags": ["a", "z"]})

    def r7():
        notes = Notes()
        notes.add("One", "Body", ("z", "a"))
        expected = json.dumps(
            {
                "schema_version": 1,
                "notes": [
                    {"id": 1, "title": "One", "body": "Body", "tags": ["a", "z"]}
                ],
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        first = notes.export_json()
        second = notes.export_json()
        require(first == second)
        require(first.rstrip("\n") == expected)

    def r8():
        notes = Notes()
        notes.add("Café ☕", "naïve")
        output = notes.export_json()
        require("Café ☕" in output and "naïve" in output)
        require("\\u00e9" not in output.lower())
        require(output.endswith("\n"))
        require("\n" not in output[:-1])

    tests = (r1, r2, r3, r4, r5, r6, r7, r8)
    return {f"R{index}": passes(test) for index, test in enumerate(tests, 1)}


def regression_checks(Notes):
    def g1():
        notes = Notes()
        require(notes.add("First") == 1)
        require(notes.add("Second", "body", ("x",)) == 2)
        require(notes.get(2) == {"id": 2, "title": "Second", "body": "body", "tags": ["x"]})
        try:
            notes.get(99)
        except KeyError as error:
            require(error.args == (99,))
        else:
            raise AssertionError("missing note did not raise KeyError")

    def g2():
        notes = Notes()
        notes.add("First", tags=("x",))
        notes.add("Second")
        result = notes.all()
        require([note["title"] for note in result] == ["First", "Second"])
        result[0]["tags"].append("changed")
        result[1]["title"] = "changed"
        require(notes.all()[0]["tags"] == ["x"])
        require(notes.all()[1]["title"] == "Second")

    def g3():
        notes = Notes()
        for bad_title in ("", "   ", None):
            try:
                notes.add(bad_title)
            except ValueError:
                pass
            else:
                raise AssertionError("invalid title accepted")
        try:
            notes.add("Title", body=object())
        except TypeError:
            pass
        else:
            raise AssertionError("invalid body accepted")
        try:
            notes.add("Title", tags=("ok", 3))
        except TypeError:
            pass
        else:
            raise AssertionError("invalid tag accepted")

    return {"G1": passes(g1), "G2": passes(g2), "G3": passes(g3)}


def main():
    target = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "public"
    if not target.is_absolute():
        target = pathlib.Path.cwd() / target

    try:
        Notes = load_notes(target)
        requirements = requirement_checks(Notes)
        regressions = regression_checks(Notes)
    except Exception:
        traceback.print_exc(file=sys.stderr)
        requirements = {f"R{index}": False for index in range(1, 9)}
        regressions = {"G1": False, "G2": False, "G3": False}

    resolved = all(requirements.values()) and all(regressions.values())
    result = {
        "requirements": requirements,
        "regressions": regressions,
        "resolved": resolved,
    }
    print(json.dumps(result, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
