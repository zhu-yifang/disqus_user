import requests
import json
from bs4 import BeautifulSoup
import aiohttp
from aiohttp import ClientSession
from asyncio import Queue
import asyncio

shows: Queue[str] = Queue()
iframe_urls: Queue[str] = Queue()
thread_ids: Queue[str] = Queue()


async def fetch_html(url: str, session: ClientSession, **kwargs) -> str:
    '''Fetches the html from a url and returns it as a string.
    '''
    print(f"Fetching {url}...")
    response = await session.get(url, **kwargs)
    retry_count = 0
    while response.status != 200:
        if retry_count > 3:
            return
        print(f"Got response {response.status} from {url}, retrying...")
        response = await session.get(url, **kwargs)
        retry_count += 1
    print(f"Got response {response.status} from {url}")
    html = await response.text()
    return html


async def get_shows_at(url: str, session: ClientSession, **kwargs):
    '''A producer. Get all the shows at the given url
    and add them to the show_urls queue.
    '''
    print(f"Getting shows at {url}...")
    html = await fetch_html(url, session, **kwargs)
    soup = BeautifulSoup(html, "html.parser")
    show_urls = soup.select('.item:not(.swiper-slide)')
    for show in show_urls:
        # if the show is a movie, add it to the queue
        if show.select_one('.type').get_text() == 'Movie':
            await shows.put(show.select_one('a')['href'])
        else:
            # if the show is a series, add all the seasons to the queue
            url = show.select_one('a')['href']
            seasons = int(show.select_one('.meta').text.split()[1])
            for season in range(1, seasons + 1):
                await shows.put(f'{url}/{season}-1')


def create_tasks_for_shows(session: ClientSession, **kwargs):
    '''create tasks that will get all the movie and series urls
    '''
    print("Creating tasks to get shows...")
    movie_tasks = [
        asyncio.create_task(
            get_shows_at(f'https://fmovies.media/movies?page={page}', session))
        for page in range(1, 1049)
    ]
    series_task = [
        asyncio.create_task(
            get_shows_at(f'https://fmovies.media/tv-series?page={page}',
                         session, **kwargs)) for page in range(1, 287)
    ]
    return movie_tasks + series_task


async def get_iframe_url(session: ClientSession, **kwargs):
    '''When there is a show url in the queue, get the url and
    add the iframe url to another queue.
    '''
    while True:
        url = await shows.get()
        print(f"Getting iframe url of {url}...")
        # fetch the html of the show
        html = await fetch_html(f"https://fmovies.media{url}", session,
                                **kwargs)
        soup = BeautifulSoup(html, "html.parser")
        # get the iframe url
        t_i = soup.select_one('#comment')['data-identifier']
        assert t_i is not None
        iframe_urls.put(
            f'https://disqus.com/embed/comments/?base=default&f=fmoviescomment&t_i={t_i}&t_u=https://fmovies.media/watch&s_o=default#version=7a4d09afbda9f3c44155fc8f6c0532e0'
        )
        shows.task_done()


async def get_thread_id(session: ClientSession, **kwargs):
    '''When there is an iframe url in the queue, get the url and
    add the thread id to another queue.
    '''
    while True:
        url = await iframe_urls.get()
        print(f"Getting thread id of {url}...")
        # fetch the html of the iframe
        html = await fetch_html(url, session, **kwargs)
        soup = BeautifulSoup(html, "html.parser")
        # get the thread id
        thread_id = json.loads(
            soup.select_one(
                '#disqus-threadData').get_text())['response']['thread']['id']
        assert thread_id is not None
        thread_ids.put(thread_id)
        iframe_urls.task_done()


# get 50 comments from a thread
def get_comments(thread, page_num=1):
    cookies = {
        'zeta-ssp-user-id': 'ua-1b7691a4-7f48-335f-b09c-605ff6f6af61',
        'disqus_unique': '8b1tt0010qek5o',
        'G_ENABLED_IDPS': 'google',
        '__jid': '8b5jsg61k1rbbk',
    }

    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive',
        # 'Cookie': 'zeta-ssp-user-id=ua-1b7691a4-7f48-335f-b09c-605ff6f6af61; disqus_unique=8b1tt0010qek5o; G_ENABLED_IDPS=google; __jid=8b5jsg61k1rbbk',
        'Referer':
        'https://disqus.com/embed/comments/?base=default&f=fmoviescomment&t_i=64881&t_u=https%3A%2F%2Ffmovies.media%2Fwatch%2Fvqro2&t_d=FMovies%20%7C%20Watch%20Luther%3A%20The%20Fallen%20Sun%20(2023)%20Online%20Free%20on%20fmovies.media&t_t=FMovies%20%7C%20Watch%20Luther%3A%20The%20Fallen%20Sun%20(2023)%20Online%20Free%20on%20fmovies.media&s_o=default',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent':
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
        'sec-ch-ua':
        '"Chromium";v="110", "Not A(Brand";v="24", "Google Chrome";v="110"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
    }

    params = {
        'limit':
        '50',
        'thread':
        f'{thread}',
        'forum':
        'fmoviescomment',
        'order':
        'popular',
        'cursor':
        f'{page_num}:0:0',
        'api_key':
        'E8Uh5l5fHZ6gD8U3KycjAIAk46f68Zw7C6eW8WSjZvCLXebZ7p0r1yrYDrLilk2F',
    }

    response = json.loads(
        requests.get('https://disqus.com/api/3.0/threads/listPostsThreaded',
                     params=params,
                     cookies=cookies,
                     headers=headers).text)
    return response


# add the public links to the set
def add_public_links(response, res):
    for post in response['response']:
        if post['author']['name'] == 'Guest':
            continue
        elif post['author']['isPrivate']:
            continue
        else:
            res.add(post['author']['profileUrl'])


# get all public user links of a thread
def get_user_links(thread, res):
    response = get_comments(thread)
    add_public_links(response, res)
    # if there is only one page
    if response['cursor']['total'] == 1:
        return
    else:
        page_nums = response['cursor']['total']
        for i in range(2, page_nums + 1):
            response = get_comments(thread, i)
            add_public_links(response, res)


async def main():
    # Solved the problem of aiohttp.client_exceptions.ClientConnectorCertificateError
    # by setting connector=aiohttp.TCPConnector(ssl=False)
    async with ClientSession(connector=aiohttp.TCPConnector(
            ssl=False)) as session:
        show_url_getters = create_tasks_for_shows(session)
        [asyncio.create_task(get_iframe_url(session)) for _ in range(5000)]
        [asyncio.create_task(get_thread_id(session)) for _ in range(5000)]
        await asyncio.gather(*show_url_getters)


if __name__ == '__main__':
    # get the url of all the movies and series
    asyncio.run(main())
