from support import fixtures
fixtures.global_setup()

import json
import sys
import re
import requests
from http import cookiejar
from datetime import datetime, timezone, timedelta

from unittest import TestCase
from resources.lib import ipwww_common
from resources.lib import ipwww_radio
from support.testutils import save_json, save_doc, doc_path, NotLoggedInCookieJar
from support.object_checks import is_not_empty, has_keys, expect_keys, is_iso_utc_time, is_url

setUpModule = fixtures.setup_web_test()


def scrape_sound_data(html):
    match = re.search(r'<script> window.__PRELOADED_STATE__ = (.*?);\s*</script>', html, re.DOTALL)
    if not match:
        return
    data = json.loads(match[1])
    return data


def check_page_has_json_data(testcase, url):
    resp = requests.get(url, headers=ipwww_common.headers, allow_redirects=False)
    html = resp.text
    # save_doc(html, 'sounds/html/bbc_radio_one.html')
    testcase.assertTrue(200, resp.status_code)
    testcase.assertTrue(resp.headers['content-type'].startswith('text/html'))
    match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)\s*</script>', html, re.DOTALL)
    data = None
    if match:
        data = json.loads(match[1])
        testcase.assertIsInstance(data, dict)
    return data


def check_synopses(testcase, synopses):
    """Check whether all keys are known and at least one of them as a non-empty value."""
    synopsis_types = ('short', 'medium', 'long')
    testcase.assertIsInstance(synopses, dict)
    for key in synopses.keys():
        # Just to flag if an unknown type comes up.
        testcase.assertTrue(key in synopsis_types)
    testcase.assertTrue(any(v for v in synopses.values()))


def check_titles(testcase, title_data):
    """Check whether all keys are present and at least one of them as a non-empty value."""
    testcase.assertIsInstance(title_data, dict)
    title_types = ('primary', 'secondary', 'tertiary')
    testcase.assertTrue(all(k in title_data.keys() for k in title_types))
    testcase.assertTrue(any(v for v in title_data.values()))


# def check_images(testcase, images):
#     """Check whether all keys are known and at least one of them as a non-empty value."""
#     testcase.assertIsInstance(images, dict)
#     image_types = ('primary', 'secondary', 'tertiary')
#     for key in  images.keys():
#         testcase.assertTrue(key in image_types)
#     testcase.assertTrue(any(v for v in images.values()))


class CheckAvailableStations(TestCase):
    def test_all_known_stations(self):
        """Check if all current radio stations are known by the addon, and if all known station are
        still present.
        """
        data  = check_page_has_json_data(self, 'https://www.bbc.co.uk/sounds/stations')
        national_stations = data['props']['pageProps']['dehydratedState']['queries'][0]['state']['data']['data'][0]
        self.assertEqual('national_and_regional_stations', national_stations['id'])
        station_list = national_stations['data']
        local_stations = data['props']['pageProps']['dehydratedState']['queries'][0]['state']['data']['data'][1]
        self.assertEqual('local_stations', local_stations['id'])
        station_list.extend(local_stations['data'])
        all_station_ids = set(station['id'] for station in station_list)
        known_station_ids = set(station[0] for station in ipwww_radio.channel_list)
        new_stations = []
        old_stations = []
        for station_id in all_station_ids:
            if station_id not in known_station_ids:

                new_stations.append(station_id)
        for station_id in known_station_ids:
            if station_id not in all_station_ids:
                old_stations.append(station_id)
        if new_stations:
            print(f"Found new radio stations: {', '.join(new_stations)}.")
        if old_stations:
            print(f"Radio station no longer available: {', '.join(old_stations)}")
        self.assertListEqual([], new_stations)
        self.assertListEqual([], old_stations)

    def create_channels_list(self, file=None):
        """Create a lists of channel_id, channel_name tuples, to be used as channel list in
        ipwww_radio and iptv settings.
        Run the test above first to check the integrity of the data returned by the BBC.

        :param file: A writable file-like object.
        """
        data = check_page_has_json_data(self, 'https://www.bbc.co.uk/sounds/stations')
        national_stations = data['props']['pageProps']['dehydratedState']['queries'][0]['state']['data']['data'][0]
        station_list = national_stations['data']
        local_stations = data['props']['pageProps']['dehydratedState']['queries'][0]['state']['data']['data'][1]
        station_list.extend(local_stations['data'])
        if file is None:
            file = sys.stdout
        file.write('channel_list = [\n')
        for station in station_list:
            file.write(f"    ('{station['id']}', '{station['network']['short_title']}'),\n")
        file.write(']\n\n\n')
        for station in station_list:
            station_name = station["network"]["short_title"].replace("&", "&amp;")
            file.write(f'{" "*44}<option label="{station_name}">{station["id"]}</option>\n')
        file.flush()


class TestLive(TestCase):
    def test_bbc_one_web_page_not_signed_in(self):
        """When not logged in the radio one webpage returns without redirects
        and contains a valid JWT token

        """
        resp = requests.get('https://www.bbc.co.uk/sounds/play/live:bbc_radio_one', allow_redirects=False)
        self.assertEqual(200, resp.status_code)
        data  = scrape_sound_data(resp.text)
        # save_json(data, 'json/sounds-live_radio1.json')
        # save_doc(resp.text, 'html/sounds-live_radio1.html')
        self.assertFalse(data['userSettings']['isSignedIn'])
        self.assertTrue(is_not_empty(data['smp']['liveStreamJwt'], str))

    def test_bbc_one_web_page_authenticated(self):
        resp = requests.get('https://www.bbc.co.uk/sounds/play/live:bbc_radio_one',
                            headers=ipwww_common.headers,
                            cookies=ipwww_common.cookie_jar,
                            allow_redirects=True)
        self.assertEqual(200, resp.status_code)
        data  = scrape_sound_data(resp.text)
        # save_json(data, 'json/sounds-live_radio1_authenticated.json')
        # save_doc(resp.text, 'html/sounds-live_radio1_authenticated.html')
        self.assertTrue(data['userSettings']['isSignedIn'])
        self.assertTrue(is_not_empty(data['smp']['liveStreamJwt'], str))

    def test_media_selector_live_not_authenticated(self):
        """Request media selector with no authentication and no JWT."""
        resp = requests.get('https://open.live.bbc.co.uk/mediaselector/6/select/version/2.0/mediaset/pc/vpid/bbc_radio_one/format/json/jsfunc/JS_callbacks0')
        self.assertEqual(200, resp.status_code)
        content = resp.text
        self.assertFalse(content.startswith('/**/ JS_callbacks0({"media":'))
        self.assertFalse('bitrate' in content)
        self.assertTrue('result":"selectionunavailable' in content)

    def _get_radio_one_data(self, authenticated=True):
        # Get data from the radio one website
        if authenticated:
            cookies = ipwww_common.cookie_jar
        else:
            cookies = NotLoggedInCookieJar()
        resp = requests.get('https://www.bbc.co.uk/sounds/play/live:bbc_radio_one',
                            headers=ipwww_common.headers,
                            cookies=cookies)
        data = scrape_sound_data(resp.text)
        if authenticated:
            self.assertTrue(data['userSettings']['isSignedIn'])
        else:
            self.assertFalse(data['userSettings']['isSignedIn'])
        return data

    def test_media_selector_live_authenticated(self):
        data = self._get_radio_one_data()
        # Request media selector with JWT from data
        resp = requests.get('https://open.live.bbc.co.uk/mediaselector/6/select/version/2.0/mediaset/pc/vpid/bbc_radio_one/format/json/jsfunc/JS_callbacks0',
                            headers=ipwww_common.headers,
                            cookies=ipwww_common.cookie_jar,
                            params={'jwt_auth': data['smp']['liveStreamJwt']})
        self.assertEqual(200, resp.status_code)
        content = resp.text
        self.assertTrue(content.startswith('/**/ JS_callbacks0({"media":'))
        self.assertTrue('bitrate' in content)
        self.assertFalse('result":"selectionunavailable' in content)

    def test_media_selector_live_authenticated_without_jwt(self):
        """Check if passing JWT token in the querystring is required if we do a
        request with all authentication cookies.

        """
        # Assert we are signed in
        self._get_radio_one_data()

        # Request media selector WITH all auth cookies, but WITHOUT JWT.
        resp = requests.get('https://open.live.bbc.co.uk/mediaselector/6/select/version/2.0/mediaset/pc/vpid/bbc_radio_one/format/json/jsfunc/JS_callbacks0',
                            cookies=ipwww_common.cookie_jar)
        self.assertEqual(200, resp.status_code)
        content = resp.text
        self.assertFalse(content.startswith('/**/ JS_callbacks0({"media":'))
        self.assertFalse('bitrate' in content)
        self.assertTrue('result":"selectionunavailable' in content)

    def test_media_selector_live_not_authenticated_with_jwt(self):
        """Check if passing auth cookies is required when JWT token is present in the querystring.

        """
        data = self._get_radio_one_data(authenticated=False)

        # Request media selector WITHOUT auth cookies, but WITH JWT.
        resp = requests.get('https://open.live.bbc.co.uk/mediaselector/6/select/version/2.0/mediaset/pc/vpid/bbc_radio_one/format/json/jsfunc/JS_callbacks0',
                            params={'jwt_auth': data['smp']['liveStreamJwt']})
        self.assertEqual(200, resp.status_code)
        content = resp.text
        self.assertTrue(content.startswith('/**/ JS_callbacks0({"media":'))
        self.assertTrue('bitrate' in content)
        self.assertFalse('result":"selectionunavailable' in content)


class RadioSchedules(TestCase):
    def check_schedule_data(self, schedule_item):
        has_keys(schedule_item,
                 'type',
                 'id',
                 'start',
                 'end',
                 'duration',
                 'titles',
                 'synopses',
                 'image_url',
                 'playable_item')
        expect_keys(schedule_item,
                    'urn', 'service_id', 'network')
        self.assertEqual('broadcast_summary', schedule_item['type'])
        self.assertTrue(is_not_empty(schedule_item['id'], str))
        self.assertTrue(is_iso_utc_time(schedule_item['start']))
        self.assertTrue(is_iso_utc_time(schedule_item['end']))
        self.assertTrue(is_not_empty(schedule_item['duration'], int))
        check_titles(self, schedule_item['titles'])
        check_synopses(self, schedule_item['synopses'])
        self.assertTrue(is_url(schedule_item['image_url'], 'jpg'))
        if schedule_item['playable_item'] is not None:
            playable = schedule_item['playable_item']
            self.assertTrue(is_not_empty(playable, dict))
            self.assertTrue(is_not_empty(playable['urn'], str))   # urn is like "urn:bbc:radio:episode:m00262rg"
            self.assertEqual(5, len(playable['urn'].split(':')))
            self.assertNotEqual(playable['id'], playable['urn'].split(':')[-1])  # The item's ID is different to the ID in the urn

    def test_schedules_html(self):
        data = check_page_has_json_data(self, 'https://www.bbc.co.uk/sounds/schedules/bbc_radio_one')
        # Check the revision id needed in urls to request json schedules.
        self.assertTrue(is_not_empty(data['buildId'], str))
        programmes_list = data['props']['pageProps']['dehydratedState']['queries'][1]['state']['data']['data'][0]['data']
        for progr in programmes_list:
            self.check_schedule_data(progr)

    def test_schedules_json(self):
        """Data returned by specific json requests is the same is _next data embedded in the html page."""
        url = 'https://www.bbc.co.uk/sounds/_next/data/76968d6/schedules/bbc_radio_one.json?scheduleIds=bbc_radio_one&scheduleIds=bbc_radio_two'
        resp = requests.get(url, allow_redirects=False)
        self.assertEqual(200, resp.status_code)
        data = resp.json()
        programmes_list = data['pageProps']['dehydratedState']['queries'][1]['state']['data']['data'][0]['data']
        for progr in programmes_list:
            self.check_schedule_data(progr)

    def test_schedules_query_string_effect(self):
        """The querystring does not seem to have any effect."""
        yesterday = (datetime.now(timezone.utc)-timedelta(days=1)).strftime('%Y-%m-%d')
        url1 = f'https://www.bbc.co.uk/sounds/_next/data/76968d6/schedules/bbc_radio_two/{yesterday}.json?scheduleIds=bbc_radio_two&scheduleIds={yesterday}'
        url2 = f'https://www.bbc.co.uk/sounds/_next/data/76968d6/schedules/bbc_radio_two/{yesterday}.json'
        resp1 = requests.get(url1, allow_redirects=False)
        self.assertEqual(200, resp1.status_code)
        # save_doc(resp1.text, 'sounds/json/schedule_w_qs.json')
        data1 = resp1.json()
        resp2 = requests.get(url2, allow_redirects=False)
        self.assertEqual(200, resp2.status_code)
        data2 = resp2.json()
        # Apart from some timestamps both dicts are equal
        del data1['pageProps']['dehydratedState']['queries'][0]['state']['dataUpdatedAt']
        del data1['pageProps']['dehydratedState']['queries'][1]['state']['dataUpdatedAt']
        del data1['pageProps']['serverTimeIso']
        del data2['pageProps']['dehydratedState']['queries'][0]['state']['dataUpdatedAt']
        del data2['pageProps']['dehydratedState']['queries'][1]['state']['dataUpdatedAt']
        del data2['pageProps']['serverTimeIso']
        self.assertEqual(json.dumps(data1), json.dumps(data2))

    def test_schedules_with_query_string_only(self):
        """Test if generic url with station and date defined in the querystring returns data.

        """
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime('%Y-%m-%d')
        url = f'https://www.bbc.co.uk/sounds/_next/data/76968d6/schedules.json?scheduleIds=bbc_radio_two&scheduleIds={yesterday}'
        resp = requests.get(url, allow_redirects=False)
        self.assertEqual(404, resp.status_code)

    def test_schedules_station_in_path_date_in_qs(self):
        """Define station in url and date in querystring.

        This return the schedule of today, instead of yesterday, i.e. querystring data is ignored.
        """
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        url = f'https://www.bbc.co.uk/sounds/_next/data/76968d6/schedules/bbc_radio_two.json?scheduleIds=bbc_radio_two&scheduleIds={yesterday.strftime("%Y-%m-%d")}'
        resp = requests.get(url, allow_redirects=False)
        self.assertEqual(200, resp.status_code)
        data = resp.json()
        programmes_list = data['pageProps']['dehydratedState']['queries'][1]['state']['data']['data'][0]['data']
        for progr in programmes_list:
            # Strip the 'Z' which fromisoformat cannot handle from the time string and convert to UTC.
            end_date = datetime.fromisoformat(progr['end'][:-1]).replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
            self.assertGreater(end_date, yesterday)

    def test_schedules_per_day(self):
        """Test schedules for each day from a week ago to a next week."""
        for i in range(-7, 8):
            day = (datetime.now(timezone.utc) + timedelta(days=i)).strftime('%Y-%m-%d')
            url = f'https://www.bbc.co.uk/sounds/_next/data/76968d6/schedules/bbc_radio_two/{day}.json?'
            resp = requests.get(url, allow_redirects=False)
            self.assertEqual(200, resp.status_code)
            data = resp.json()
            programmes_list = data['pageProps']['dehydratedState']['queries'][1]['state']['data']['data'][0]['data']
            for progr in programmes_list:
                self.check_schedule_data(progr)


class TestListening(TestCase):
    def test_old_listening_list_page_logged_in(self):
        resp = requests.get(url="http://www.bbc.co.uk/radio/favourites",
                            headers=ipwww_common.headers,
                            cookies=ipwww_common.cookie_jar,
                            allow_redirects=False)
        self.assertTrue(resp.is_permanent_redirect)
        self.assertEqual('https://www.bbc.co.uk/radio/favourites', resp.headers['location'])
        resp = requests.get(url="https://www.bbc.co.uk/radio/favourites",
                            headers=ipwww_common.headers,
                            cookies=ipwww_common.cookie_jar,
                            allow_redirects=False)
        self.assertTrue(resp.is_permanent_redirect)
        self.assertEqual('https://www.bbc.co.uk/sounds/favourites', resp.headers['location'])

    def test_get_listening_list_page_logged_in(self):
        resp = requests.get(url="https://www.bbc.co.uk/sounds/favourites",
                            headers=ipwww_common.headers,
                            cookies=ipwww_common.cookie_jar,
                            allow_redirects=False)
        self.assertEqual(404, resp.status_code)

    def test_get_following_page_logged_in(self):
        """currently not used in the add-on"""
        resp = requests.get(url="https://www.bbc.co.uk/radio/favourites/programmes",
                            headers=ipwww_common.headers,
                            cookies=ipwww_common.cookie_jar,
                            allow_redirects=False)
        self.assertEqual(404, resp.status_code)


class TestBookmarks(TestCase):
    def test_get_bookmarks_signed_in(self):
        resp = requests.get('https://www.bbc.co.uk/sounds/my/bookmarks', cookies=ipwww_common.cookie_jar, allow_redirects=False)
        self.assertEqual(200, resp.status_code)
        # save_doc(resp.text, 'html/sounds-bookmarks.html')
        data = scrape_sound_data(resp.text)
        pass


class TestCategories(TestCase):
    def test_categories_data(self):
        resp = requests.get('https://www.bbc.co.uk/sounds/categories', allow_redirects=False)
        self.assertFalse(resp.is_redirect)
        self.assertTrue(resp.headers['content-type'].startswith('text/html'))
        # save_doc(resp.text, 'html/radio-categories.html')
        data = scrape_sound_data(resp.text)
        pass
