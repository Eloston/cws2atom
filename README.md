cws2atom
========

A script to retrieve Chrome Webstore reviews and support feedback and output them as an [Atom feed](https://en.wikipedia.org/wiki/Atom_(standard)) to standard output

It will grab reviews and support feedback in all languages, including replies.

Requirements
------------

* Python (tested on version 3.5)
* [pyatom](https://github.com/rpcope1/pyatom)

Usage
-----

```
python3 cws2atom.py EXTENSION_ID [NUM_RESULTS]
```
where:
* EXTENSION_ID is the extension's ID on the Chrome Webstore, e.g. `efdhoaajjjgckpbkoglidkeendpkolai`
* NUM_RESULTS is an optional parameter specifying the number of reviews to download and the number of support posts to download. Reviews and support posts are ordered in descending order of time, so only the beginning NUM_RESULTS are selected. The default is 100, which seems to be the maximum that the Chrome Webstore will take.

The Atom feed will be written to standard output.

It may be more helpful to use this in conjunction with a RSS reader such as [Liferea](https://lzone.de/liferea/), which can be configured to invoke cws2atom.

Contributing
------------

Please leave issues, suggestions, and questions in the Issue Tracker. Pull requests are welcome.

License
-------

Public domain
