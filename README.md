1. Get the url of all the movies and series
   1. fetch HTML. Problem: sometimes it give Error 504
   2. parse HTML, if movie: get url; elif series: get url and seasons
   This step should return a list of url / (url, seasons)
2. Get the iframe url for all given urls
   1. input: show urls
   2. output: iframe urls
3. Input: iframe urls
   Output: thread ids
4. Input: thread ids
   Output: user links
5. Write to file