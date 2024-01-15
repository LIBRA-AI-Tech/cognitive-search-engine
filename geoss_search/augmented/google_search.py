import aiohttp
import asyncio
from bs4 import BeautifulSoup

class GoogleSearch():

    def __init__(self, timeout: int = 3) -> None:
        self._url = "https://www.google.com/search"
        self._headers = {
            'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36'
        }
        self._timeout = timeout

    async def parse_google_html(self, html: str):
        if html is None:
            return None
        try:
            soup = BeautifulSoup(html, 'lxml')
        except Exception as e:
            print(str(e))
        results = []
        css_mappings = {
            'title': '.DKV0Md',
            'link': '.yuRUbf a',
            'description': '#rso .VwiC3b',
        }
        for result in soup.select('.tF2Cxc'):
            result = {key: result.select_one(css) for key, css in css_mappings.items()}
            for key in result:
                if result[key] is None:
                    return
                if key == 'link':
                    result[key] = result[key].get('href')
                else:
                    result[key] = result[key].text
            results.append(result)
        return results

    async def search(self, text: str):
        params = dict(q=text, start=0)
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(self._url, headers=self._headers, params=params, timeout=self._timeout) as resp:
                    if resp.status == 200:
                        html = await resp.text()
                        results = await self.parse_google_html(html)
                        return results
                    else:
                        return None
            except asyncio.TimeoutError:
                return None
