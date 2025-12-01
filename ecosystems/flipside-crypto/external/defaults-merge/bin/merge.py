#!/usr/bin/env python3.9

"""Script to merge defaults into a source map in Terraform"""

from heapq import merge
from itertools import count
import os
import sys
import json
import logging
from base64 import b64encode
from datetime import datetime
from collections.abc import Mapping


defaults_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "defaults")
logger = logging.getLogger(__name__)


def get_logger(log_file):
    logger = logging.getLogger(__name__)
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    file_handler = logging.FileHandler(log_file, mode="w")
    logger.propagate = True
    logger.addHandler(file_handler)
    logger.setLevel(logging.DEBUG)
    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    logger.info(f"New run at {now}")
    return logger


def strtobool(val):
    val = val.lower()
    if val in ("y", "yes", "t", "true", "on", "1"):
        return True
    elif val in ("n", "no", "f", "false", "off", "0"):
        return False
    else:
        raise ValueError("invalid truth value %r" % (val,))


class DefaultsMerge:

    def __init__(
        self,
        log_file,
        source_map,
        defaults_file_path,
        defaults,
        base,
        overrides,
        allow_empty_values,
        allowlist_key,
        allowlist_value,
    ):
        self.logger = get_logger(log_file)

        self.allow_empty_values = strtobool(allow_empty_values)
        self.allowlist_key = allowlist_key
        self.allowlist_value = allowlist_value

        self.logger.info(
            f"Defaults File Path: {defaults_file_path}, Allow Empty Values: {self.allow_empty_values}, Allowlist Key: {self.allowlist_key}, Allowlist Value: {self.allowlist_value}"
        )

        self.base = json.loads(base)
        self.log_results(self.base, "Base")

        self.source_map = json.loads(source_map)
        self.log_results(self.source_map, "Source Map")

        self.defaults = self.load_defaults(
            defaults_file_path=defaults_file_path, defaults=json.loads(defaults)
        )
        self.log_results(self.defaults, "Defaults")

        self.overrides = json.loads(overrides)
        self.log_results(self.overrides, "Overrides")

    def merge(self):
        if not isinstance(self.source_map, Mapping):
            raise RuntimeError(f"Source isn't a map: '{self.source_map}'")

        self.logger.info(
            "Generating initial results by merging source map into defaults"
        )
        initial_results = self.join_merge(self.source_map, self.defaults)
        self.log_results(initial_results, "Initial results")

        self.logger.info("Generating base results by merging initial results into base")
        base_results = self.join_merge(self.base, initial_results)

        self.log_results(base_results, "Base results")

        self.logger.info("Generating results by overriding base results with overrides")
        results = self.join_merge(self.overrides, base_results)
        self.log_results(results, "Results")

        if not self.allowlist_key:
            self.logger.info("Filtering by key disabled, returning results")
            return results

        allowlist = results.get(self.allowlist_key)

        if not allowlist or len(allowlist) <= 0:
            self.logger.warning(
                f"Allowlist is set to: '{self.allowlist_key}' and allowlist: '{allowlist}' is empty, returning nothing"
            )
            return {}

        if not self.allowlist_value or self.allowlist_value not in allowlist:
            self.logger.warning(
                f"Allowlist '{allowlist}' returned for allowlist key: '{self.allowlist_key}' doesn't contain value: '{self.allowlist_value}', returning nothing"
            )
            return {}

        return results

    def log_results(self, results, label="Results"):
        self.logger.info(
            f"[JSON] {label}:\n{json.dumps(results, indent=4, sort_keys=True)}"
        )

    def load_defaults(self, defaults={}, defaults_file_path=""):
        self.log_results(defaults, "Defaults from map")

        if not os.path.exists(defaults_file_path):
            self.logger.info(
                f"No defaults file {defaults_file_path} exists, returning defaults from map"
            )
            return defaults

        self.logger.info(f"Loading additional defaults from file {defaults_file_path}")
        with open(defaults_file_path, "r") as defaults_file:
            defaults_from_file = json.load(defaults_file)
            self.log_results(defaults_from_file, "Defaults from file")

            defaults = self.join_merge(defaults, defaults_from_file)
            self.log_results(defaults, "Joined defaults")
            return defaults

    def join_merge(self, primary, secondary):
        self.logger.info(f"Join merge, Allow Empty Values: {self.allow_empty_values}")

        if primary == secondary:
            self.log_results(
                primary, "Primary and secondary are identical, returning primary"
            )
            return primary

        if isinstance(primary, Mapping):
            if not isinstance(secondary, Mapping):
                self.log_results(
                    secondary,
                    "Secondary is not a map while primary is, returning primary",
                )
                self.log_results(primary, "Primary")
                return primary

            merge_map = primary | secondary

            for k, v in secondary.items():
                if k in primary:
                    if isinstance(primary[k], list):
                        if len(primary[k]) > 0:
                            self.logger.info(
                                f"Primary map member '{k}' is a list {primary[k]},  using it as-is since it is not empty"
                            )
                            merge_map[k] = primary[k]
                        elif self.allow_empty_values:
                            self.logger.info(
                                f"Primary map member '{k}' is an empty list {primary[k]},  using it as-is since empty values are allowed"
                            )
                            merge_map[k] = primary[k]
                        else:
                            self.logger.info(
                                f"Primary map member '{k} is an empty list {primary[k]}, using secondary list {v}"
                            )
                            merge_map[k] = v
                    else:
                        self.logger.info(
                            f"Joining key {k}'s data for primary {primary[k]} and secondary {secondary[k]} of join merge"
                        )
                        merge_map[k] = self.join_merge(primary[k], secondary[k])

            self.log_results(merge_map, "Join merge results")
            return merge_map

        if isinstance(primary, list):
            if not isinstance(secondary, list):
                self.log_results(
                    secondary,
                    "Secondary is not a list while primary is, returning primary",
                )
                self.log_results(primary, "Primary")
                return primary

            for v in secondary:
                if v not in primary:
                    self.logger.info(
                        f"Value '{v}' from secondary not in primary, adding"
                    )
                    primary.append(v)

            self.log_results(primary, "Join merge results")
            return primary

        if primary or primary in [False, [], {}]:
            if not self.allow_empty_values and primary in [[], {}]:
                self.logger.info(
                    f"Primary '{primary}' is either '[]' or '{{}}' and empty values are not allowed, returning {secondary}"
                )
                return secondary

            self.log_results(
                primary,
                f"Primitive data type '{primary}' for primary is either true, false, or empty, but is "
                f"not null, returning it instead of performing join merge",
            )
            return primary

        self.log_results(
            secondary,
            "Primary is null, secondary is primitive data type, returning it instead of performing "
            "join merge",
        )
        return secondary

    @classmethod
    def from_stdin(cls):
        inp = json.load(sys.stdin)
        return cls(**inp)


def main():
    dm = DefaultsMerge.from_stdin()
    result = {
        "merged_map": b64encode(json.dumps(dm.merge()).encode("utf-8")).decode("utf-8")
    }

    sys.stdout.write(json.dumps(result))


if __name__ == "__main__":
    main()
