import struct
from pathlib import Path
from typing import Tuple
from urllib.parse import urljoin
from urllib.request import urlopen
from xml.etree import ElementTree as ET

from support import fixtures
fixtures.global_setup()

from unittest import TestCase

from resources.lib import proxy
from support.testutils import open_doc


setUp = fixtures.setup_local_tests()

MPD_NS = 'urn:mpeg:dash:schema:mpd:2011'
NAMESPACES = {'d': MPD_NS}
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / 'plugin.video.iplayerwww/resources/data'


def _boxes(data, start=0, end=None):
    end = len(data) if end is None else end
    while start < end:
        size = struct.unpack_from('>I', data, start)[0]
        box_type = data[start + 4:start + 8].decode('ascii')
        header_size = 8
        if size == 1:
            size = struct.unpack_from('>Q', data, start + 8)[0]
            header_size = 16
        elif size == 0:
            size = end - start
        if size < header_size or start + size > end:
            raise AssertionError(f'Invalid {box_type} box at offset {start}')
        yield box_type, start, start + header_size, start + size
        start += size


def _child_box(data, parent, box_type):
    for box in _boxes(data, parent[2], parent[3]):
        if box[0] == box_type:
            return box
    raise AssertionError(f'{box_type} box not found')


def _root_box(data, box_type):
    for box in _boxes(data):
        if box[0] == box_type:
            return box
    raise AssertionError(f'{box_type} box not found')


def _caption_template(manifest: bytes) -> Tuple[ET.Element, ET.Element, ET.Element]:
    root = ET.fromstring(manifest)
    for adaptation in root.findall('.//d:AdaptationSet', NAMESPACES):
        if adaptation.get('contentType') == 'text':
            representation = adaptation.find('d:Representation', NAMESPACES)
            if representation is None:
                raise AssertionError('Subtitle representation not found')
            template = representation.find('d:SegmentTemplate', NAMESPACES)
            if template is None:
                raise AssertionError('Subtitle segment template not found')
            return root, adaptation, template
    raise AssertionError('Subtitle adaptation set not found')


def _template_attribute(template, name):
    value = template.get(name)
    if value is None:
        raise AssertionError(f'SegmentTemplate attribute {name} not found')
    return value


def _base_url(root):
    base_url = root.find('d:BaseURL', NAMESPACES)
    if base_url is None or base_url.text is None:
        raise AssertionError('BaseURL not found')
    return base_url.text


class ManifestModification(TestCase):
    def test_fixed_duration_template_preserves_live_timing_and_resolves_urls(self):
        orig_mpd = open_doc('manifest/manifest_live_from_listing.mpd')().encode('utf-8')
        upstream_base = 'https://my.server.url/live'

        new_mpd = proxy.modify_manifest(orig_mpd, upstream_base, 18645)
        root, _, template = _caption_template(new_mpd)

        self.assertEqual(_template_attribute(template, 'timescale'), '48000')
        self.assertEqual(_template_attribute(template, 'duration'), '184320')
        self.assertEqual(_template_attribute(template, 'media'), 't=3840/s=caption1/b=64000/$Number$.m4s')
        self.assertEqual(_template_attribute(template, 'initialization'),
                         'http://127.0.0.1:18645/caption/segment.init')
        base_url = _base_url(root)
        self.assertEqual(base_url, 'https://my.server.url/live/')
        media_url = urljoin(base_url, _template_attribute(template, 'media').replace('$Number$', '9'))
        self.assertEqual(media_url,
                         'https://my.server.url/live/t=3840/s=caption1/b=64000/9.m4s')

    def test_timeline_and_attributes_are_inherited_from_all_levels(self):
        mpd = f'''<MPD xmlns="{MPD_NS}">
          <SegmentTemplate timescale="1000" startNumber="42" media="root/$Number$.m4s" />
          <Period>
            <SegmentTemplate presentationTimeOffset="500">
              <SegmentTimeline><S t="1000" d="4000" r="2" /></SegmentTimeline>
            </SegmentTemplate>
            <AdaptationSet contentType="video">
              <Representation id="video">
                <SegmentTemplate media="video/$Number$.m4s" initialization="video.init" />
              </Representation>
            </AdaptationSet>
          </Period>
        </MPD>'''.encode('utf-8')

        new_mpd = proxy.modify_manifest(mpd, 'https://cdn.example/live/', 18645)
        _, _, template = _caption_template(new_mpd)

        self.assertEqual(_template_attribute(template, 'timescale'), '1000')
        self.assertEqual(_template_attribute(template, 'startNumber'), '42')
        self.assertEqual(_template_attribute(template, 'presentationTimeOffset'), '500')
        timeline = template.find('d:SegmentTimeline', NAMESPACES)
        if timeline is None:
            self.fail('Inherited SegmentTimeline not found')
        segment = timeline.find('d:S', NAMESPACES)
        if segment is None:
            self.fail('SegmentTimeline entry not found')
        self.assertEqual(segment.attrib,
                         {'t': '1000', 'd': '4000', 'r': '2'})

    def test_existing_base_url_is_kept_upstream_and_media_uses_it(self):
        mpd = f'''<MPD xmlns="{MPD_NS}">
          <BaseURL>edge/</BaseURL>
          <Period>
            <AdaptationSet contentType="audio">
              <Representation id="audio">
                <SegmentTemplate timescale="1000" duration="4000" media="audio/$Number$.m4s" />
              </Representation>
            </AdaptationSet>
          </Period>
        </MPD>'''.encode('utf-8')

        new_mpd = proxy.modify_manifest(mpd, 'https://cdn.example/live/', 18645)
        root, _, template = _caption_template(new_mpd)

        base_url = _base_url(root)
        self.assertEqual(base_url, 'https://cdn.example/live/edge/')
        media_url = urljoin(base_url, _template_attribute(template, 'media').replace('$Number$', '17'))
        self.assertEqual(media_url,
                         'https://cdn.example/live/edge/t=3840/s=caption1/b=64000/17.m4s')
        self.assertNotIn('127.0.0.1', media_url)

    def test_no_scheduled_template_does_not_add_subtitle_adaptation(self):
        mpd = f'''<MPD xmlns="{MPD_NS}">
          <Period>
            <AdaptationSet contentType="audio">
              <Representation id="audio">
                <SegmentTemplate timescale="1000" media="audio/$Number$.m4s" />
              </Representation>
            </AdaptationSet>
          </Period>
        </MPD>'''.encode('utf-8')

        root = ET.fromstring(proxy.modify_manifest(mpd, 'https://cdn.example/live/', 18645))

        self.assertFalse(any(adaptation.get('contentType') == 'text'
                             for adaptation in root.findall('.//d:AdaptationSet', NAMESPACES)))

    def test_empty_timeline_overrides_inherited_duration(self):
        mpd = f'''<MPD xmlns="{MPD_NS}">
          <SegmentTemplate timescale="1000" duration="4000" />
          <Period>
            <SegmentTemplate><SegmentTimeline /></SegmentTemplate>
            <AdaptationSet contentType="audio">
              <Representation id="audio" />
            </AdaptationSet>
          </Period>
        </MPD>'''.encode('utf-8')

        root = ET.fromstring(proxy.modify_manifest(mpd, 'https://cdn.example/live/', 18645))

        self.assertFalse(any(adaptation.get('contentType') == 'text'
                             for adaptation in root.findall('.//d:AdaptationSet', NAMESPACES)))


class ReadInit(TestCase):
    def test_caption_init_matches_bbc_fragment_track(self):
        init_data = proxy.read_caption_init()
        fragment_data = (DATA_DIR / 'iplayer-captions.m4s').read_bytes()

        self.assertEqual([box[0] for box in _boxes(init_data)], ['ftyp', 'moov'])
        moov = _root_box(init_data, 'moov')
        trak = _child_box(init_data, moov, 'trak')
        tkhd = _child_box(init_data, trak, 'tkhd')
        mdia = _child_box(init_data, trak, 'mdia')
        mdhd = _child_box(init_data, mdia, 'mdhd')
        minf = _child_box(init_data, mdia, 'minf')
        stbl = _child_box(init_data, minf, 'stbl')
        stsd = _child_box(init_data, stbl, 'stsd')

        track_id_offset = tkhd[2] + (20 if init_data[tkhd[2]] == 1 else 12)
        track_id = struct.unpack_from('>I', init_data, track_id_offset)[0]
        timescale_offset = mdhd[2] + (20 if init_data[mdhd[2]] == 1 else 12)
        timescale = struct.unpack_from('>I', init_data, timescale_offset)[0]
        entries = list(_boxes(init_data, stsd[2] + 8, stsd[3]))
        self.assertEqual([entry[0] for entry in entries], ['stpp'])
        self.assertIn(b'application/ttml+xml', init_data)
        self.assertIn(b'codecs=im1t', init_data)

        moof = _root_box(fragment_data, 'moof')
        traf = _child_box(fragment_data, moof, 'traf')
        tfhd = _child_box(fragment_data, traf, 'tfhd')
        fragment_track_id = struct.unpack_from('>I', fragment_data, tfhd[2] + 4)[0]
        self.assertEqual(track_id, fragment_track_id)
        self.assertEqual(track_id, 1)
        self.assertEqual(timescale, 1000)

    def test_init_is_served_over_the_local_http_endpoint(self):
        server = proxy.ProxyServer(('127.0.0.1', 0), proxy.ProxyRequestHandler, '')
        server.start_server()
        try:
            with urlopen(f'http://127.0.0.1:{server.server_port}/caption/segment.init',
                         timeout=3) as response:
                data = response.read()
                self.assertEqual(response.status, 200)
                self.assertEqual(response.headers.get_content_type(), 'video/mp4')
                self.assertEqual(int(response.headers['Content-Length']), len(data))
            self.assertEqual(data, proxy.read_caption_init())
        finally:
            server.stop_server(timeout=3)
            server.server_close()
