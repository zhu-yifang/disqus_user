import requests
import json
from bs4 import BeautifulSoup
import aiohttp
from aiohttp import ClientSession
from asyncio import Queue
import asyncio

movie_urls: Queue[str] = Queue()
series_tuples: Queue[tuple[str, int]] = Queue()


async def fetch_html(url: str, session: ClientSession, **kwargs) -> str:
    '''Fetches the html from a url and returns it as a string.
    '''
    print(f"Fetching {url}...")
    response = await session.get(url, **kwargs)
    response.raise_for_status()
    print(f"Got response {response.status} from {url}")
    html = await response.text()
    return html


async def get_shows_at(url: str, session: ClientSession, **kwargs):
    '''A producer. Get all the shows at the given url
    and add them to the movie_urls or the series_tuples queue.
    '''
    print(f"Getting shows at {url}...")
    html = await fetch_html(url, session, **kwargs)
    soup = BeautifulSoup(html, "html.parser")
    show_urls = soup.select('.item:not(.swiper-slide)')
    for show in show_urls:
        if show.select_one('.type').get_text() == 'Movie':
            await movie_urls.put(show.select_one('a')['href'])
        else:
            url = show.select_one('a')['href']
            seasons = int(show.select_one('.meta').text.split()[1])
            await series_tuples.put((url, seasons))


def create_tasks_for_shows(session: ClientSession, **kwargs):
    '''create tasks that will get all the movie and series urls
    '''
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


def get_iframe_url(url):
    response = requests.get("https://fmovies.media" + url)
    soup = BeautifulSoup(response.text, "html.parser")
    t_i = soup.select_one('#comment')['data-identifier']
    return f'https://disqus.com/embed/comments/?base=default&f=fmoviescomment&t_i={t_i}&t_u=https://fmovies.media/watch&s_o=default#version=7a4d09afbda9f3c44155fc8f6c0532e0'


def get_thread_id(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    return json.loads(soup.select_one(
        '#disqus-threadData').get_text())['response']['thread']['id']


def crawl_a_show(url):
    # get the url to the iframe
    url = get_iframe_url(url)
    # go to the iframe to get the thread number
    thread = get_thread_id(url)
    print(thread)
    # get the user links of the movie
    user_links = set()
    get_user_links(thread, user_links)
    # write the links to a csv file
    with open('user_links.csv', 'a') as f:
        for user_link in user_links:
            f.write(user_link + '\n')


# get the iframe of the comment areas
# movies
def crawl_movies():
    for movie_url in movie_urls:
        crawl_a_show(movie_url)


# series
def crawl_series():
    for series_url, seasons in series:
        for season in range(1, seasons + 1):
            crawl_a_show(series_url + f'/{season}-1')


async def main():
    # Solved the problem of aiohttp.client_exceptions.ClientConnectorCertificateError
    # by setting connector=aiohttp.TCPConnector(ssl=False)
    async with ClientSession(connector=aiohttp.TCPConnector(
            ssl=False)) as session:
        tasks = create_tasks_for_shows(session)
        await asyncio.gather(*tasks)

if __name__ == '__main__':
    # get the url of all the movies and series
    asyncio.run(main())