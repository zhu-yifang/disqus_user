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
    count = 0
    while True:
        print(count)
        if count > 300:
            break
        try:
            page.click(".load-more-refresh", timeout=3000)
            count += 1
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
        if element.get_attribute('href'):
            shows_urls.add(element.get_attribute('href'))
    return shows_urls


def is_private(page, user_url):
    page.goto(user_url)
    if page.query_selector("p.text-gray.text-medium"):
        return True
    else:
        return False


def remove_private(page, user_links):
    new_set = set()
    for user_link in user_links:
        if not is_private(page, user_link):
            new_set.add(user_link)
    return new_set


def write_to_csv(user_links):
    with open('user_links.csv', 'a', newline='') as f:
        # append all the user_links to the csv file in a new line
        for user_link in user_links:
            f.write(user_link + "\n")


def run():
    with sync_playwright() as p:
        # launch browser and pretend to be a normal user
        browser = p.firefox.launch(headless=False)
        context = browser.new_context(
            user_agent=
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36'
        )
        page = context.new_page()
        
        # test with a series
        user_links = crawl_series(page, "https://fmovies.media/series/the-last-of-us-x1qo8")


        # get all the shows
        site_url = "https://www.fmovies.media"
        home_url = site_url + "/home"
        shows_urls = get_all_shows(page, home_url)
        for show_url in shows_urls:
            # if it's a movie
            if "series" in show_url:
                user_links = crawl_series(page, site_url + show_url)
                # remove private users
                user_links = remove_private(page, user_links)
                print(user_links)
                # write to csv
                write_to_csv(user_links)
            # if it's a series
            else:
                user_links = crawl_a_movie(page, site_url + show_url)
                # remove private users
                user_links = remove_private(page, user_links)
                print(user_links)
                # write to csv
                write_to_csv(user_links)

        browser.close()


if __name__ == '__main__':
    run()