#!/usr/bin/env python3
import sys

from bridge.direct_send import SUCCESS_RESULTS, payload_from_argv, send_to_openclaw


def main() -> int:
    text, files = payload_from_argv(sys.argv)
    if not text:
        print("EMPTY")
        return 1
    result = send_to_openclaw(text, files)
    print(result)
    return 0 if result in SUCCESS_RESULTS else 1


if __name__ == "__main__":
    raise SystemExit(main())
