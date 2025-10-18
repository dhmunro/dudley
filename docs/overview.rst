Overview
========

Dudley is a data description language - a human-readable way to describe
how data is encoded in a byte stream.  A Dudley description, or *layout*,
specifies the contents of a binary data file, with roughly the same scope and
use cases as `HDF5 <https://www.hdfgroup.org/solutions/hdf5/>`__ and similar
self-describing binary file formats.  However, a single Dudley layout may also
describe many different files or byte streams, so it can also be used like
the `XDR <https://www.rfc-editor.org/rfc/rfc4506>`__ standard to exchange
multiple similar data sets among programs built around a common layout.  Like
HDF5 (but not XDR), Dudley is specialized for describing scientific data.

Specifically, Dudley is modeled after numpy, where n-dimensional arrays are
first class objects, which are grouped using python's dict and/or list
containers.  Thus, a Dudley layout organizes data in exactly the same way as
`JASON <https://json.org>`__, except that the elements in the container tree
are binary numpy ndarrays instead of textual numbers or strings.

But one of Dudley's most important features has no numpy equivalent: symbolic
names for dimension lengths.  Very often a collection of data arrays share
common dimension lengths, so this feature can show important relationships
among the various arrays in a data set.  The
`netCDF <https://www.unidata.ucar.edu/software/netcdf>`__ format also has this
feature, but unlike netCDF, Dudley allows the dimension lengths to be stored
in the stream as parameter values.  This extension permits a single Dudley
layout to describe a large number of files or stream instances - potentially
every restart dump file for even aphysics simulation code, 

Since physics simulations often require only a few dozen parameters to fix
the dimensions of every array, a separate catalog file can store copies of all
parameters for the very large numbers of individual data files which may be
associated with large parallel simulations.  Dudley has only very low level
support for this use case, but by using Dudley for the individual files in
such collections, you are in a strong position to design efficient ways to
access arbitrary data anywhere in the collection.

A final remark is that by commenting a Dudley layout, you can document all the
variables stored in the file in the same place you describe the layout of
the file or data stream.  Thus, a layout can serve as a quick reference guide
to the variables describing the state of a simulation or the results of an
experiment or observation.
