#!/usr/bin/env python

"""Script to merge context objects in Terraform"""

import os
import sys
import json
import logging
from datetime import datetime
from base64 import b64encode
from collections.abc import Mapping
from copy import copy


logger = logging.getLogger(__name__)


def log_results(results, label="Results"):
    logger.info(f"[JSON] {label}:\n{json.dumps(results, indent=4, sort_keys=True)}")


def strtobool(val):
    val = val.lower()
    if val in ("y", "yes", "t", "true", "on", "1"):
        return True
    elif val in ("n", "no", "f", "false", "off", "0"):
        return False
    else:
        raise ValueError("invalid truth value %r" % (val,))


def list_merge(primary, secondary):
    logger.info(f"List merge of primary '{primary}' and secondary '{secondary}'")
    try:
        return list(set(primary + secondary))
    except TypeError as exc:
        logger.warning(f"Could not simply join lists {primary} and {secondary}: {exc}")

        for item in secondary:
            if item not in primary:
                primary.append(item)

        return primary


def nullify_enumerables(obj, label):
    if isinstance(obj, Mapping) or isinstance(obj, list):
        log_results(obj, f"Rejecting enumerable object '{label}")
        return None

    return obj


def join_merge(primary, secondary, reject_enumerables):
    if primary == secondary:
        log_results(primary, "Primary and secondary are identical, returning primary")
        return primary

    if reject_enumerables:
        primary = nullify_enumerables(primary, "primary")
        secondary = nullify_enumerables(secondary, "secondary")

    if isinstance(primary, Mapping):
        if not isinstance(secondary, Mapping):
            log_results(
                secondary, "Secondary is not a map while primary is, returning primary"
            )
            log_results(primary, "Primary")
            return primary

        merge_map = primary | secondary

        for k, v in secondary.items():
            if k in primary:
                if isinstance(primary[k], list):
                    logger.info(
                        f"Primary map member '{k}' is a list {primary[k]}, getting the union of it and list {secondary[k]}"
                    )
                    merge_map[k] = list_merge(primary[k], secondary[k])
                else:
                    logger.info(
                        f"Joining key {k}'s data for primary {primary[k]} and secondary {secondary[k]} of join merge"
                    )
                    merge_map[k] = join_merge(
                        primary[k], secondary[k], reject_enumerables
                    )

        log_results(merge_map, "Join merge results")
        return merge_map

    if isinstance(primary, list):
        if not isinstance(secondary, list):
            log_results(
                secondary, "Secondary is not a list while primary is, returning primary"
            )
            log_results(primary, "Primary")
            return primary

        for v in secondary:
            if v not in primary:
                logger.info(f"Value '{v}' from secondary not in primary, adding")
                primary.append(v)

        log_results(primary, "Join merge results")
        return primary

    try:
        if primary or primary in [False, [], {}] or strtobool(primary) == False:
            log_results(
                primary,
                f"Primitive data type '{primary}' for primary is either true, false, or empty, but is "
                f"not null, returning it instead of performing join merge",
            )
            return primary

    except ValueError:
        log_results(
            primary,
            f"Primary could not be processed, returning secondary: '{secondary}'",
        )
        return secondary

    log_results(
        secondary,
        "Primary is null, secondary is primitive data type, returning it instead of performing "
        "join merge",
    )
    return secondary


def main():
    inp = json.load(sys.stdin)

    log_file = inp["log_file"]
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    file_handler = logging.FileHandler(log_file, mode="w")
    logger.addHandler(file_handler)
    logger.setLevel(logging.DEBUG)
    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    logger.info(f"New merge at {now}")
    log_results(inp, "Inputs")

    source_maps = json.loads(inp["source_maps"])
    reject_enumerables = strtobool(inp["reject_enumerables"])
    reject_empty = strtobool(inp["reject_empty"])
    log_results(source_maps, "Source Maps")

    merged_maps = {}

    for source_map in source_maps:
        base_merged_maps = join_merge(merged_maps, source_map, reject_enumerables)

    log_results(base_merged_maps, "Merged Maps")

    if reject_empty:
        merged_maps = {k: v for k, v in base_merged_maps.items() if v is not None}
        log_results(merged_maps, "Rejected empty values from the merge")
    else:
        merged_maps = base_merged_maps

    result = {
        "merged_maps": b64encode(json.dumps(merged_maps).encode("utf-8")).decode(
            "utf-8"
        )
    }

    sys.stdout.write(json.dumps(result))


if __name__ == "__main__":
    main()
