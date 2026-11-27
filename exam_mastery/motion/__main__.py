"""python -m exam_mastery.motion list | validate <scene> | export <scene> <out-dir> [--kind textbook|anki]"""
import argparse
import sys

from . import SceneError, available, export_keyframes, load


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m exam_mastery.motion", description="Mastery Motion scenes (offline)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    v = sub.add_parser("validate")
    v.add_argument("scene")
    e = sub.add_parser("export", help="write keyframes as standalone SVG")
    e.add_argument("scene")
    e.add_argument("out")
    e.add_argument("--kind", choices=("textbook", "anki"), default=None, help="only the scene's keyframes of this kind")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "list":
            print("\n".join(available()))
        elif a.cmd == "validate":
            print(f"{a.scene}: {len(load(a.scene)['steps'])} steps valid")
        else:
            for path in export_keyframes(load(a.scene), a.out, a.kind):
                print(path)
    except SceneError as exc:
        print(exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
