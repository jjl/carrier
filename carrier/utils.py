from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import platform
import re
import sys
import urlparse

from . import __version__


class NormalizingDict(dict):

    def pop(self, key, default=None):
        value = super(NormalizingDict, self).pop(key, default)
        if not value or value in ["UNKNOWN", "None"]:
            value = default
        return value


_PREDICATE = re.compile(r"(?i)^\s*(\w[\s\w-]*(?:\.\w*)*)(.*)")
_VERSIONS = re.compile(r"^\s*\((?P<versions>.*)\)\s*$|^\s*(?P<versions2>.*)\s*$")
_SPLIT_CMP = re.compile(r"^\s*(<=|>=|<|>|!=|==)\s*([^\s,]+)\s*$")


def _split_predicate(predicate):
    match = _SPLIT_CMP.match(predicate)
    if match is None:
        # probably no op, we'll use "=="
        comp, version = '==', predicate
    else:
        comp, version = match.groups()
    return comp, version  # NormalizedVersion(version)


class VersionPredicate(object):
    """Defines a predicate: ProjectName (>ver1,ver2, ..)"""

    _operators = {"<": lambda x, y: x < y,
                  ">": lambda x, y: x > y,
                  "<=": lambda x, y: str(x).startswith(str(y)) or x < y,
                  ">=": lambda x, y: str(x).startswith(str(y)) or x > y,
                  "==": lambda x, y: str(x).startswith(str(y)),
                  "!=": lambda x, y: not str(x).startswith(str(y)),
                  }

    def __init__(self, predicate):
        self._string = predicate
        predicate = predicate.strip()
        match = _PREDICATE.match(predicate)
        if match is None:
            raise ValueError('Bad predicate "%s"' % predicate)

        name, predicates = match.groups()
        self.name = name.strip()
        self.predicates = []
        if predicates is None:
            return

        predicates = _VERSIONS.match(predicates.strip())
        if predicates is None:
            return

        predicates = predicates.groupdict()
        if predicates['versions'] is not None:
            versions = predicates['versions']
        else:
            versions = predicates.get('versions2')

        if versions is not None:
            for version in versions.split(','):
                if version.strip() == '':
                    continue
                self.predicates.append(_split_predicate(version))

    def match(self, version):
        """Check if the provided version matches the predicates."""
        # if isinstance(version, basestring):
        #     version = NormalizedVersion(version)
        for operator, predicate in self.predicates:
            if not self._operators[operator](version, predicate):
                return False
        return True

    def __repr__(self):
        return self._string


def split_meta(meta):
    meta_split = meta.split(";", 1)

    vp = VersionPredicate(meta_split[0].strip())
    meta_env = meta_split[1].strip() if len(meta_split) == 2 else ""

    return {
        "name": vp.name,
        "version": ",".join(["".join(p) for p in [(op if op != "==" else "", v) for op, v in vp.predicates]]),
        "environment": meta_env,
    }


_url = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # ...or ipv4
        r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # ...or ipv6
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)


def clean_uri(url):
    parts = list(urlparse.urlsplit(url))

    if not parts[0]:
        # If no URL scheme given, assume http://
        parts[0] = "http"

    if not parts[1]:
        # Assume that if no domain is provided, that the path segment
        # contains the domain.
        parts[1] = parts[2]
        parts[2] = ""
        # Rebuild the url_fields list, since the domain segment may now
        # contain the path too.
        parts = list(urlparse.urlsplit(urlparse.urlunsplit(parts)))

    if not parts[2]:
        # the path portion may need to be added before query params
        parts[2] = "/"

    cleaned_url = urlparse.urlunsplit(parts)

    if not _url.search(cleaned_url):
        # Trivial Case Failed. Try for possible IDN domain
        if cleaned_url:
            scheme, netloc, path, query, fragment = urlparse.urlsplit(cleaned_url)

            try:
                netloc = netloc.encode("idna").decode("ascii")  # IDN -> ACE
            except UnicodeError:  # invalid domain part
                raise ValueError

            cleaned_url = urlparse.urlunsplit((scheme, netloc, path, query, fragment))

            if not _url.search(cleaned_url):
                raise ValueError
        else:
            raise ValueError

    return cleaned_url


def user_agent():
    _implementation = platform.python_implementation()

    if _implementation == "CPython":
        _implementation_version = platform.python_version()
    elif _implementation == "PyPy":
        _implementation_version = "%s.%s.%s" % (
                                                sys.pypy_version_info.major,
                                                sys.pypy_version_info.minor,
                                                sys.pypy_version_info.micro
                                            )
        if sys.pypy_version_info.releaselevel != "final":
            _implementation_version = "".join([_implementation_version, sys.pypy_version_info.releaselevel])
    elif _implementation == "Jython":
        _implementation_version = platform.python_version()  # Complete Guess
    elif _implementation == "IronPython":
        _implementation_version = platform.python_version()  # Complete Guess
    else:
        _implementation_version = "Unknown"

    return " ".join([
            "carrier/%s" % __version__,
            "%s/%s" % (_implementation, _implementation_version),
            "%s/%s" % (platform.system(), platform.release()),
        ])
