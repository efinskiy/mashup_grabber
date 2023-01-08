import random
import traceback
from typing import Union
import json
import eyed3
import requests
import os
from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings
import telebot

disable_warnings(InsecureRequestWarning)


class Mashup:
    def __init__(self, cookies: dict):
        self._cookies = cookies

    def create_headers(self, kind: int) -> dict:
        return {
            'DNT': '1',
            'Host': 'music.yandex.ru',
            'Referer': f'https://music.yandex.ru/users/finskiy.ru/playlists/{kind}',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
            'X-Current-UID': '727749803',
            'X-Requested-With': 'XMLHttpRequest',
            'X-Retpath-Y': r"https%3A%2F%2Fmusic.yandex.ru%2Fusers%2Ffinskiy.ru%2Fplaylists%2F"+str(kind),
            'X-Yandex-Music-Client': 'YandexMusicAPI',
            'sec-ch-ua': '"Not?A_Brand";v="8", "Chromium";v="108", "Google Chrome";v="108"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
        }

    def addAlbumCover(self, filePath: str, coverPath: str):
        audiofile = eyed3.load(filePath)
        albumcover = open(coverPath, 'rb')

        try:
            if audiofile.tag is None:
                audiofile.initTag()
        except Exception as e:
            print(f'{str(traceback.format_exc())}')
            return 0
        audiofile.tag.images.set(eyed3.id3.frames.ImageFrame.FRONT_COVER, albumcover.read(), 'image/jpeg')
        audiofile.tag.save()
        albumcover.close()

    def setTrackInfo(self, filePath: str):
        audiofile = eyed3.load(filePath)
        filename = os.path.basename(filePath).replace('.mp3', '').split('-')
        print(filename)
        if filename[1][0] == ' ':
            filename[1] = '' + filename[1][1:]

        audiofile.tag.artist = filename[0]
        audiofile.tag.title = filename[1]

        audiofile.tag.save()

    def ugcUpload(self,
                  bot: telebot.TeleBot, filename: str, kind: Union[str, int], lang: str = None,
                  overembed: bool = None, ncrnd: Union[int, float] = None, external_domain: str = None,
                  visibility: str = None
                  ) -> Union[str, bool]:

        if not lang:
            lang = 'ru'
        if not overembed:
            overembed = False
        if not ncrnd:
            ncrnd = random.random()
        if not external_domain:
            external_domain = 'music.yandex.ru'
        if not visibility:
            visibility = 'private'

        url = r'https://music.yandex.ru/handlers/ugc-upload.jsx'
        params = {'filename': filename, 'kind': kind, 'visibility': visibility,
                  'lang': lang, 'external-domain': external_domain, 'overembed': overembed, 'ncrnd': ncrnd}
        result = requests.get(url, params, cookies=self._cookies, headers=self.create_headers(kind))
        try:
            result = result.json()
        except requests.exceptions.JSONDecodeError as e:
            from bot import LOG_CHAT_ID
            if 'captcha' in result.text:
                bot.send_message(LOG_CHAT_ID,
                                 f'❌ Yandex запросил капчу',
                                 parse_mode='html')
            else:
                bot.send_message(LOG_CHAT_ID,
                                f'''❌ ugcUpload вернул некорректный *JSON*
                                `{str(result.content)}`
                                ''',
                                parse_mode='markdown')
            return False
        return result['post-target']

    def uploadTrack(self, file: bytes, post_target: str, cookies: dict, kind: int) -> bool:
        payload = {'file': file}
        result = requests.post(url=post_target, files=payload, cookies=cookies, timeout=360, verify=False,
                               headers=self.create_headers(kind)).json()

        if result['result'] == 'CREATED':
            return True
        else:
            return False


if __name__ == "__main__":
    print('Its a module, not for standalone run')