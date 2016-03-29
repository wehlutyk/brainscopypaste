# Brains Copy Paste [![Build Status](https://travis-ci.org/wehlutyk/brainscopypaste.svg?branch=master)](https://travis-ci.org/wehlutyk/brainscopypaste)

Analyzing mutation in quotes when they propagate through the blog- and news-spaces. This should tell us stuff on how the brain copy-pastes and alters quotes when doing so.

This software was developed for a research paper based on the [MemeTracker](http://memetracker.org/) quotes database [to be pusblished]. It is released under the GNU/GPLv3 licence.

[The documentation](https://brainscopypaste.readthedocs.org/en/latest/) explains all about how to setup and use the software.


## Notes

For pipeline graph:
- [Graffiti](https://github.com/SegFaultAX/graffiti)
- [PyLeaf](http://www.francesconapolitano.it/leaf/lgl.html)
- [Ruffus](https://github.com/bunbun/ruffus)

Timings:
- brainscoppypaste load memetracker
  - parsing; 0:12:24
  - saving; ~0:15:00?
  - checking: 8:45:33
- brainscoppypaste filter memetracker
  - parsing: 3:37:41
  - saving; ~0:15:00?
- brainscoppypaste mine memetracker
  - parsing: 2:16:13
