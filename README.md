# Detecting American regions using migration data and community detection in graphs

What is the Midwest? Where is the South? Where's the gateway to the West? How do we define the regions of the United States? Plenty of folks have answered this question, and many have taken a quantitative approach. Take a look:

### Earth features
* [Let’s settle it: This is what makes up the Midwest](https://www.twincities.com/2016/01/29/this-is-whats-in-the-midwest-2/)
* [Coldest Day of the Year](https://www.ncdc.noaa.gov/sites/default/files/Contiguous-US-Climatological-Coldest-Day-of-the-Year-Map.jpg)
* [How presidential elections are impacted by a 100-million-year-old coastline](http://www.deepseanews.com/2012/06/how-presidential-elections-are-impacted-by-a-100-million-year-old-coastline/)

### Economic and cultural features
* [The Nine Nations of North America](https://en.wikipedia.org/wiki/The_Nine_Nations_of_North_America)
* [The Sweet Tea Line](https://bigthink.com/strange-maps/317-tea-as-a-northsouth-litmus-test)
* [Soda vs. Pop with Twitter](http://blog.echen.me/2012/07/06/soda-vs-pop-with-twitter/)
* [Finding the True Border Between Yankee and Red Sox Nation Using Facebook Data](https://harvardsportsanalysis.wordpress.com/2012/08/17/finding-the-true-border-between-yankee-and-red-sox-nation-using-facebook-data/)
* [Urban dialect areas](https://www.ling.upenn.edu/phono_atlas/NationalMap/NatMap1.html)
* [Votes and Vowels: A Changing Accent Shows How Language Parallels Politics](http://blogs.discovermagazine.com/crux/2012/03/28/votes-and-vowels-a-changing-accent-shows-how-language-parallels-politics/)
* [Which of the 11 American nations do you live in?](https://www.washingtonpost.com/blogs/govbeat/wp/2013/11/08/which-of-the-11-american-nations-do-you-live-in/)
* [Speaking American: How Y’all, Youse , and You Guys Talk: A Visual Guide](https://hmhbooks.com/shop/books/Speaking-American/9780544703391) via the wonderful [dialect quiz on the New York Times](https://www.nytimes.com/interactive/2014/upshot/dialect-quiz-map.html)
* [Modular networks of word correlations on Twitter](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3492865/figure/f2/)

### Social interactions
* [The Connected States of America](http://senseable.mit.edu/csa/)
* [How to split up the US](https://petewarden.com/2010/02/06/how-to-split-up-the-us/)

### Aggregations and crowdsourcing
* [The Midwest](http://www.radicalcartography.net/index.html?midwest)
* [Go Ahead, Try Drawing an Outline of the Midwest on a Map](https://www.citylab.com/design/2013/07/go-ahead-try-drawing-outline-midwest-map/6208/)
* [Which States Are in the Midwest?](https://fivethirtyeight.com/features/what-states-are-in-the-midwest/)
* [More Data Analysts Went Looking For the South And Midwest, And Here’s What They Found](https://fivethirtyeight.com/features/more-data-analysts-went-looking-for-the-south-and-midwest-and-heres-what-they-found/)

And of course, Wikipedia's [List of regions of the United States](https://en.wikipedia.org/wiki/List_of_regions_of_the_United_States) and [Regions of the United States category](https://en.wikipedia.org/wiki/Category:Regions_of_the_United_States).

## My approach
1. Migration data
2. Graph data structures
3. Graph community detection methods
4. Probablistic method that gives us "fuzzy" community detection
5. Regions are defined by a county of interest. That is, for any given County C, what proportion of the time does any other County X fall into the same detected community?
