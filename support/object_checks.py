# ----------------------------------------------------------------------------------------------------------------------
#  Copyright (c) 2022-2023 Dimitri Kroon.
#  This file is part of plugin.video.viwx.
#  SPDX-License-Identifier: GPL-2.0-or-later
#  See LICENSE.txt
# ----------------------------------------------------------------------------------------------------------------------

from __future__ import annotations
import time
import unittest



def has_keys(dict_obj, *keys, obj_name='dictionary'):
    """Checks if all keys are present in the dictionary"""
    keys_set = set(keys)
    present_keys = set(dict_obj.keys()).intersection(keys_set)
    if present_keys != keys_set:
        absent = keys_set.difference(present_keys)
        raise AssertionError("Key{} {} {} not present in '{}'".format(
            's' if len(absent) > 1 else '',
            absent,
            'is' if len(absent) == 1 else 'are',
            obj_name)
        )


def misses_keys(dict_obj: dict, *keys: str, obj_name: str = 'dictionary') -> bool:
    """Checks if all keys are NOT present in the dictionary

    :param dict_obj: The dictionary to check
    :param obj_name: Optional name of the object, only used to add a meaningful message to an AssertionError
    :raises AssertionError:

    """
    keys_set = set(keys)
    present_keys = set(dict_obj.keys()).intersection(keys_set)
    if present_keys:
        raise AssertionError("Key{} {} {} unexpectedly present in '{}'".format(
            's' if len(present_keys) > 1 else '',
            present_keys,
            'is' if len(present_keys) == 1 else 'are',
            obj_name)
        )
    return True


def expect_keys(dict_obj: dict, *keys: str, obj_name: str ='dictionary'):
    """Print a warning if a key is not present, but do not fail a test.
    """
    try:
        has_keys(dict_obj, *keys, obj_name=obj_name)
    except AssertionError as err:
        print('Expected', err)


def expect_misses_keys(dict_obj, *keys, obj_name='dictionary'):
    """Print a warning if a key is unexpectedly present, but do not fail a test.
    """
    try:
        return misses_keys(dict_obj, *keys, obj_name=obj_name)
    except AssertionError as err:
        print(err)
        return False


def is_url(url: str, ext: str| list | tuple | None = None) -> bool:
    """Short and simple check if the string `url` is indeed a URL.
    This is in no way intended to completely validate the URL - it is just to check
    that the string is not just a path without protocol specification, or just some
    other string that is not a URL at all.

    :param url: str: String to check.
    :param ext: Optional file extension(s) (including preceding dot) of the document requested in the URL.

    """
    if not isinstance(url, str):
        return False
    result = url.startswith('https://')
    result = result and url.find('//', 7) == -1
    if ext is not None:
        if isinstance(ext, (tuple, list)):
            result = result and any(url.endswith(extension) or extension + '?' in url for extension in ext)
        else:
            result = result and (url.endswith(ext) or ext + '?' in url)
    return result


def is_iso_utc_time(time_str):
    """check if the time string is in a format like yyyy-mm-ddThh:mm:ssZ which is
    often used by itv's web services.
    Accept times with or without milliseconds
    """
    try:
        if '.' in time_str:
            time.strptime(time_str, '%Y-%m-%dT%H:%M:%S.%fZ')
        else:
            time.strptime(time_str, '%Y-%m-%dT%H:%M:%SZ')
        return True
    except ValueError:
        return False


def iso_duration_2_seconds(iso_str: str) -> int | None:
    """Convert an ISO 8601 duration string into seconds.

    Simple parser to match durations found in films and tv episodes.
    Handles only hours, minutes and seconds.

    """
    try:
        if len(iso_str) > 3:
            import re
            match = re.match(r'^PT(?:([\d.]+)H)?(?:([\d.]+)M)?(?:([\d.]+)S)?$', iso_str)
            if match:
                hours, minutes, seconds = match.groups(default=0)
                return int(float(hours) * 3600 + float(minutes) * 60 + float(seconds))
    except (ValueError, AttributeError, TypeError):
        pass
    return None


def is_li_compatible_dict(testcase: unittest.TestCase, dict_obj: dict):
    """Check if object can be passed as keyword arguments to AddMenuEntry()

    """
    all_args = {'name': str,
                'url': str,
                'mode': int,
                'iconimage': str,
                'description': str,
                'subtitles_url': str,
                'aired': (str, type(None)),
                'resolution': (str, type(None)),
                'resume_time': str,
                'total_time': str}

    mandatory_args = ('name', 'mode')

    for key, value in dict_obj.items():
        testcase.assertTrue(key in all_args.keys())
        testcase.assertIsInstance(value, all_args[key])
    for arg_name in mandatory_args:
        testcase.assertTrue(is_not_empty(dict_obj[arg_name], all_args[arg_name]))
    return True


def is_not_empty(item, type):
    if not isinstance(item, type):
        return False
    if type in (int, float, bool):
        return True
    else:
        return bool(item)
