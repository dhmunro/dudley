# Dudley Data Description Language

Dudley is a binary data description language, that is, a tool for describing
how data is encoded in a stream of bytes.

Dudley is a simplified alternative to
[HDF5](https://www.hdfgroup.org/solutions/hdf5/) and similar
self-describing binary file formats.  However, a single Dudley layout may also
describe many different files or byte streams, so it can be used to describe
whole collections of files, as often produced by parallel simulations.

See the documentation at https://dhmunro.github.io/dudley.

Dudley features:

* Simple data model
  - based on numpy ndarray and python dict and list
  - multi-dimensional array data in containers
  - dict-like containers map names to arrays or containers
  - list-like containers hold sequence of anonymous arrays or containers
  - array data type may be numeric, string, unicode, or compounds
* Human readable
  - layout with documentation comments serves as quick-reference guide for
    binary file contents
  - simplifies collaborations involving exchange of binary data
* Single layout can describe multiple binary files or streams
  - array dimensions can be parameters stored in the binary file
  - enables catalog files describing large collections of files sharing
    one layout (or a few layouts)
* Lightweight (compared to HDF5)
  - Python and C language implementations
