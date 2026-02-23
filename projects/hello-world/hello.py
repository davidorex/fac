"""
hello-world factory artifact: minimal CLI greeting script.

Prints a greeting with the current local date/time.
No third-party dependencies; uses argparse and datetime from stdlib.
"""

import argparse
from datetime import datetime


def main():
    parser = argparse.ArgumentParser(description="Factory hello-world greeter")
    parser.add_argument("--name", type=str, default=None, help="A name to include in the greeting")
    args = parser.parse_args()

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if args.name is not None and args.name == "":
        parser.error("--name value must be a non-empty string")

    if args.name:
        message = f"Hello, {args.name}, from the factory! {timestamp}"
    else:
        message = f"Hello from the factory! {timestamp}"

    print(message)


if __name__ == "__main__":
    main()
