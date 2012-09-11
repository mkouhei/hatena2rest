Hatena2reST is conversion tool from Hatena Diary to reST format.
================================================================

Hatena2reST is for conversion from Hatena Diary to Tinkerer. Tinkerer is blog system of reST format that is powered by Sphinx. Exported data of Hatena Diary are four kinds format. Those are XML, Movable Type format, CSV and PDF. This tools support XML only.


Requirement
-----------

* Python 2.x (>= 2.7)
* Sphinx (>= 1.1.0)
* `Tinkerer (>= 0.4 beta) <http://tinkerer.me/>`_


Setup
-----

Install Debian packages that Hatena2reST depends on
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Hatena2reST depends on Python2.7, Sphinx, Tinkerer. Install Sphinx is::

  $ sudo apt-get install python-sphinx

But Tinkerer are not yet official Debian packages, then download python-tinkerer from http://www.palmtb.net/deb/t/

Instal that choosing with one of three ways.

from source
"""""""""""
::

   $ git clone https://github.com/mkouhei/hatena2rest.git
   $ cd hatena2rest
   $ sudo python setup.py install

PyPI
""""
::

   $ pip install hatena2rest

Debian package
""""""""""""""

Not yet official package, then download python-hatena2rest-x.x_all.deb from http://www.palmtb.net/deb/ and install with dpkg command.::

  $ wget http://www.palmtb.net/deb/h/python-hatena2rest_x.x-x_all.deb
  $ sudo dpkg -i python-hatena2rest_x.x-x_all.deb


Usage
-----

#. Export Hatena Diary with XML format.
#. Execute htn2rst commandl. ::

   $ htn2rst your_hatena_id.xml

Retrieve your photo images when converting, execute htn2rst command with "-r/--retrieve" option. ::

   $ htn2rst -r your_hatena_id.xml

#. Change generated direcotry. ::

   $ cd ~/tmp/hatena2rest

#. Edit necessary setting items of tineker conf file. ::

   $ edit conf.py

#. Build from reST to HTML files with tinker command. ::

   $ tinker -b -q

