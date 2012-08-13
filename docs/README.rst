htn2rest is tool of converting Hatena Diary to reST format.
===========================================================

Exporting data of Hatena Diary are 4 kinds format. Those are XML, Movable Type format, CSV, and PDF. This tools support XML or Movable Type format as input file.


Requirement
-----------

* Python 2.x (>= 2.7)
* `Pystache (>= 0.5.2) <https://github.com/defunkt/pystache>`_
* Sphinx (>= 1.1.0)
* `Tinkerer (>= 0.3 beta) <http://tinkerer.bitbucket.org/index.html>`_


Setup
-----

Install Debian packages that htn2rst depends on
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

htn2rst depends on Python2.7, Sphinx, Pystache, Tinkerer. Install Sphinx is::

  $ sudo apt-get install python-sphinx

But Pystache and Tinkerer are not yet official Debian packages, then download python-pystache and python-tinkerer from http://www.palmtb.net/deb/p/ and http://www.palmtb.net/deb/t/



Instal that choosing with one of three ways.

from source
"""""""""""
::

   $ git clone https://github.com/mkouhei/htn2rst.git
   $ cd htn2rst
   $ sudo python setup.py install

PyPI
""""
::

   $ pip install htn2rst

Debian package
""""""""""""""

Not yet official package, then download python-htn2rst-x.x_all.deb from http://www.palmtb.net/deb/ and install with dpkg command.::

  $ wget http://www.palmtb.net/deb/h/python-htn2rst_x.x-x_all.deb
  $ sudo dpkg -i python-htn2rst_x.x-x_all.deb


Usage
-----

1. Export Hatena Diary with Movable Type format.
2. Execute below procedure.::

   $ python mt2rest.py hatenaid.txt
   $ cd out
   $ tinker -s
   $ mv master.rst.tmp master.rst
   $ edit conf.py
   $ tinker -b -q

