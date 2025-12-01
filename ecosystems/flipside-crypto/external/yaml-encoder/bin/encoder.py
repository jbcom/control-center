#!/usr/bin/env python3.9

import sys
import json
import yaml
from base64 import b64encode


def main():
    inp = json.load(sys.stdin)
    data = json.loads(inp["data"])

    result = {"yaml": b64encode(yaml.dump(data).encode("utf-8")).decode("utf-8")}

    sys.stdout.write(json.dumps(result))


if __name__ == "__main__":
    main()
