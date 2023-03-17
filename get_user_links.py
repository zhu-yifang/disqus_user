import requests
import json

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
    'limit': '50',
    'thread': '9592924335',
    'forum': 'fmoviescomment',
    'order': 'popular',
    'cursor': '',
    'api_key':
    'E8Uh5l5fHZ6gD8U3KycjAIAk46f68Zw7C6eW8WSjZvCLXebZ7p0r1yrYDrLilk2F',
}

response = requests.get('https://disqus.com/api/3.0/threads/listPostsThreaded',
                        params=params,
                        cookies=cookies,
                        headers=headers)

pretty_json = json.dumps(response.json(), indent=4)

print(pretty_json)

