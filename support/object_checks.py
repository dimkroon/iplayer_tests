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


def is_li_compatible_dict(testcase: unittest.TestCase, dict_obj: dict):
    """Check if `dict_obj` is a dict that can be passed to codequick's Listitem.from_dict()

    """
    testcase.assertIsInstance(dict_obj, dict)
    has_keys(dict_obj, 'label', 'params')
    for item_key, item_value in dict_obj.items():
        testcase.assertTrue(item_key in ('label', 'art', 'info', 'params'))
        if item_key == 'label':
            testcase.assertIsInstance(dict_obj['label'], str)
            testcase.assertTrue(dict_obj['label'])
            continue

        testcase.assertIsInstance(item_value, dict)
        # all sub items must be strings or integers.
        # Is not a requirement for Listitem, but I like to keep it that way.
        for item_val in item_value.values():
            testcase.assertIsInstance(item_val, (str, int, type(None)))

        if item_key == 'art':
            for art_type, art_link in item_value.items():
                testcase.assertTrue(art_type in ('thumb', 'fanart', 'poster'),
                                    'Unexpected artType: {}'.format(art_type))
                testcase.assertTrue(not art_link or is_url(art_link))
        elif item_key == 'params':
            for param, param_val in item_value.items():
                if param == 'url' and param_val:
                    testcase.assertTrue(is_url(param_val))
    return True


def is_not_empty(item, type):
    if not isinstance(item, type):
        return False
    if type in (int, float, bool):
        return True
    else:
        return bool(item)
