import os
import time
from dataclasses import dataclass

import requests

TIMEOUT = (10, 120)  # connect, read seconds


class PublishError(Exception):
    """retryable=False means retrying will not help (bad token, rejected video...)."""

    def __init__(self, message, retryable=True):
        super().__init__(message)
        self.retryable = retryable


@dataclass
class PublishResult:
    remote_id: str
    url: str = ""
    note: str = ""


def check(resp, what):
    if resp.status_code >= 400:
        retryable = resp.status_code >= 500 or resp.status_code == 429
        raise PublishError(f"{what}: HTTP {resp.status_code} {resp.text[:400]}", retryable=retryable)
    return resp


def file_size(path):
    return os.path.getsize(path)


def poll(fn, timeout=600, every=5):
    """Call fn() until it returns a truthy value or timeout (seconds)."""
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        out = fn()
        if out:
            return out
        time.sleep(every)
    raise PublishError("timed out waiting for the platform to finish processing", retryable=True)


session = requests.Session()
