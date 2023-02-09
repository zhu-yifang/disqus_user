from playwright.sync_api import sync_playwright


# input: a page object and a show's url
# return: a set of user links
def crawl_a_movie(page, movie_url) -> set:
    page.goto(movie_url)
    # wait for the iframe to load
    comment = page.wait_for_selector('iframe[src^="https://disqus.com/embed"]',
                                     state='attached')
    disqus_url = comment.get_attribute('src')
    page.goto(disqus_url)
    page.wait_for_load_state('networkidle')

    while True:
        try:
            page.click(".load-more-refresh", timeout=1000)
        # if TimeoutError, break
        except:
            break
    # get all the user_links
    usernames_elements = page.query_selector_all('a[data-action="profile"]')
    user_links = set()
    for element in usernames_elements:
        user_links.add(element.get_attribute('href'))
    return user_links


def crawl_series(page, series_url):
    # crawl a series
    user_links = set()
    page.goto(series_url + "/1-1")
    # get the number of seasons by get the last element in the list
    season_num = page.locator("input[name='season']").locator(
        "nth=-1").get_attribute("value")
    # crawl each season
    for i in range(1, int(season_num) + 1):
        # crawl a season like a movie
        season_url = series_url + "/" + str(i) + "-1"
        user_links = user_links.union(crawl_a_movie(page, season_url))
    return user_links


def get_all_shows(page, home_url):
    page.goto(home_url)
    titles_elements = page.query_selector_all('.title')
    shows_urls = set()
    for element in titles_elements:
        shows_urls.add(element.get_attribute('href'))
    return shows_urls


with sync_playwright() as p:
    # launch browser and pretend to be a normal user
    browser = p.firefox.launch(headless=False)
    context = browser.new_context(
        user_agent=
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36'
    )
    page = context.new_page()

    user_links = set()
    # get all the shows
    site_url = "https://www.fmovies.media"
    home_url = site_url + "/home"
    shows_urls = get_all_shows(page, home_url)
    for show_url in shows_urls:
        # if it's a movie
        if "movie" in show_url:
            user_links = crawl_a_movie(page, site_url + show_url)
        # if it's a series
        else:
            user_links = crawl_series(page, site_url + show_url)
    print(user_links)
    browser.close()
