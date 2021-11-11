# coding: utf-8
from __future__ import unicode_literals

import base64

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    try_get
)


class DVTVIE(InfoExtractor):
    IE_NAME = 'dvtv'
    IE_DESC = 'dvtv.cz videos'
    _VALID_URL = r'https?://(?:www\.)?dvtv\.cz/video/[^/?#&]+'

    _TESTS = [{
        'url': 'https://www.dvtv.cz/video/obtezujici-pravidla-mi-jsou-volna-flakanec-byl-zasah-vyssi-moci-rika-poslanec-volny',
        'info_dict': {
            'id': '512689404',
            'ext': 'mp4',
            'title': 'md5:dce68a81e71b456014b8e071434613de',
            'description': 'md5:fa4f59a1043d760f846925d8a51b14b2'
        },
        'params': {
            'skip_download': True
        }
    }, {
        'url': 'https://www.dvtv.cz/video/nejhorsi-cisla-od-jara-je-cas-kvuli-covidu-znovu-zavrit-skoly-sledujte-dvtv',
        'info_dict': {
            'id': '644491806',
            'ext': 'mp4',
            'title': 'md5:123fbc7338f6edd72b063bacf857a753',
            'description': 'md5:f0ca8949e3d4f148324238dcf6fa32c8'
        },
        'params': {
            'skip_download': True
        }
    }]

    def _real_extract(self, url):
        webpage = self._download_webpage(url, None)

        video_id = self._parse_json(base64.b64decode(self._html_search_regex(r'data-video-options=([\'"])(?P<config>[^\'"]+)\1', webpage, 'video_config', group='config')).decode('ascii'), None).get('vimeoId')
        if video_id is None:
            raise ExtractorError('Failed extracting video id')

        iframe = self._download_json(f'https://vimeo.com/api/oembed.json?url=https://vimeo.com/{video_id}', video_id, headers={'Referer': 'https://www.dvtv.cz'}, note='Downloading iframe').get('html')
        if iframe is None:
            raise ExtractorError('Failed getting iframe')

        player_data = self._download_webpage(self._html_search_regex(r'<iframe src\s*=\s*([\'"])(?P<url>[^\'"]+)\1', iframe, 'player_data', group='url'), video_id, headers={'Referer': 'https://www.dvtv.cz'}, note='Downloading player data')
        player_config = self._parse_json(self._html_search_regex(r'config\s*=\s*(?P<json>{[^;]+});', player_data, 'player_config', group='json'), video_id)

        formats = []
        subs = []
        dash_info = try_get(player_config, lambda x: x['request']['files']['dash'], dict)
        if dash_info is not None:
            formats += self._extract_mpd_formats(
                try_get(dash_info, lambda x: x['cdns'][x['default_cdn']]['url'], str).replace('master.json', 'master.mpd'),
                video_id, mpd_id='dash', fatal=False)
        hls_info = try_get(player_config, lambda x: x['request']['files']['hls'], dict)
        if hls_info is not None:
            formats_m3u8, subs = self._extract_m3u8_formats_and_subtitles(
                try_get(hls_info, lambda x: x['cdns'][x['default_cdn']]['url'], str),
                video_id, m3u8_id='hls', fatal=False)
            formats += formats_m3u8
        audio_url = self._html_search_regex(r'<source\s+src\s*=\s*([\'"])(?P<url>.+)\1', webpage, 'audio_url', group='url', fatal=False)
        if audio_url is not None:
            formats += [{'url': f'https://www.dvtv.cz{audio_url}', 'vcodec': 'none'}]
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': self._html_search_meta(
                ['title', 'og:title', 'twitter:title'],
                webpage, 'title', default=None),
            'description': self._html_search_meta(
                ['og:description', 'twitter:description'],
                webpage, 'description', default=None),
            'thumbnail': self._html_search_meta(
                ['og:image', 'twitter:image'],
                webpage, 'image', default=None),
            'formats': formats,
            'subtitles': subs
        }
