.. Dudley documentation master file, created by
   sphinx-quickstart on Sat Aug 23 09:42:09 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

:hide-toc:

Dudley Data Description Language
================================

A Dudley description of a binary file is called a **layout**.  A layout is a
text file which may either be separate from the binary file(s) it describes or
be appended to the end of the binary data to make a single self-describing
binary file (like an HDF5 file).

Features:
---------

* **Simple data model**

  * based on numpy `ndarray` and python `dict` and `list`
  * multi-dimensional array data in containers
  * dict-like containers map names to arrays or containers
  * list-like containers hold sequence of anonymous arrays or containers
  * array data type may be numeric, string, unicode, or compounds

* **Human readable**

  * layout with documentation comments serves as quick-reference guide
    for binary file contents
  * simplifies collaborations involving exchange of binary data

* **Single layout can describe multiple binary files or streams**

  * array dimensions can be parameters stored in the binary file
  * enables catalog files describing large collections of files sharing
    one layout (or a few layouts)

* **Lightweight** (compared to HDF5)

  * Python and C language implementations

.. toctree::
   :maxdepth: 2
   :hidden:

   overview
   syntax
   comments
   filters
   grammar
   signatures
   python
   
