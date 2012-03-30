mt2rest.py
==========

Convert Hatna Diary (Movable Type format) to Tinkerer (reST).

Requirement
-----------

* python 2.x (>= 2.7)

* pystache   (>= 0.4.1)
  https://github.com/defunkt/pystache

* Sphinx     (>= 1.1.0)
  http://sphinx.pocoo.org/

* Tinkerer   (>= 0.3 beta)
  http://tinkerer.bitbucket.org/index.html

Usage
-----

1. Cloning this program from Github.
2. Setup system requirement.
3. Export Hatena Diary with Movable Type format.
4. Execute below procedure.

``` shell
$ python mt2rest.py hatenaid.txt
$ cd out
$ tinker -s
$ mv master.rst.tmp master.rst
$ edit conf.py
$ tinker -b -q
```

ToDo
----

This has some unsupported issues.

* ol tag
* nested list (ul, ol)
* parsing escaped character
* There are continuos curly brackets ( "{{" and "}}") in MT format file, fails executing.
* blog parts (script, div, style tags)
* setup script

