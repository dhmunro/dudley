Filters
=======

Dudley supports two kinds of filters.  *Compression* filters convert an array
declared in the usual way into a (hopefully shorter) byte string::

    f8[1000, 100, 100] -> zfp  # compress 1000x100x100 array using zfp

what actually is written to the data stream is the result of compressing the
array using zfp.  The zfp filter uses a lossy compression scheme, so the
1000x100x100 array you read back will not be precisely the same as what you
wrote.  ZFP has many tuning options, but the default Dudley zfp filter
simplifies its various options to just a single optional parameter.  If you
want to pass a non-default parameter value to a filter, you write the filter
like a function call::

    f8[1000, 100, 100] -> zfp(1.e-6)  # compress with tolerance 1.e-6

Dudley implements four compression filters by default, but you can define and
register your own custom filters if you wish.  Unlike an unfiltered array, you
do not know in advance how many bytes of the stream will be occupied by the
compressed array, so using any filters at all restricts a Dudley layout to
a particualr individual byte stream.  The default filters are all
simplified versions of popular open source compressors::

    *zfp(level)* **[ZFP](https://zfp.io)** is a lossy compression library.
    The Dudley `level` parameter is the ZFP *tolerance*, which is the acceptable
    absolute error for the array values if `level>0`.  If `level<0`, then
    `-level` is the ZFP *precision*, which is roughly the number of bits of
    mantissa that will be preserved, a rough way to specify the acceptable
    relative error for array values.  Finally, `level=0` specifies the ZFP
    lossless compression option.  The default is `level=-15`, which produces
    a bit better than part per thousand relative accuracy.  Only works on
    arrays of numbers (best for floats) with up to four dimensions.
    *gzip(level)* **[zlib](https://zlib.net)** is a lossless compression library.
    The `level` parameter can be 0-9 or -1, with the same meanings as the gzip
    utility.  However, Dudley makes the default `level=9` on the assumption that
    you will usually want maximum compression.  The zlib compression is not
    really designed for binary data, but it can work well on integers and text.
    *jpeg(quality)* **[jpeg](https://jpeg.org)** is a lossy image
    compression format.  Accepts only `u1[NX, NY]` data (grayscale image),
    `u1[NX, NY, 3]` data (RGB image), or `u1[NX, NY, 4]` data (CMYK image).
    The `quality` is 0-95, with `quality=75` the default.
    *png(level)* **[png](https://libpng.org/pub/png)** is a lossless image
    compression format.  Accepts only `u?[NX, NY]` data (grayscale image),
    `u?[NX, NY, 3]` data (RGB image), where `u?` is either `u1` or `u2`.
    The `level` is 0-9, with `level=9` the default.

The second kind of filter, a *reference* filter, is completely different.
Instead of converting an array of declared type and shape to an unknown
number of bytes in the file like a compression filter, a *reference* filter
converts an array of unknown type and shape into a reference to that object
where each such reference has a known datatype (usually an integer).  This
reference is roughly equivalent to declaring a `void *` in C::

    datatype shape <- ref  # this array holds references to unknown objects

Now the objects which are referenced obviously must be declared *somewhere* in
the layout - otherwise there would be no way to read them back.  Therefore,
Dudley expects to find a sequence of special declarations of the form::

    = datatype shape filter address

These can appear anywhere a named dict item is expected, but these reference
declarations are kept outside of the dict-list container tree.  The `ref`
filter is responsible for associating these special declarations with the
item containing the `<- ref` marker.  HDF5 and PDB files each have their own
`ref` filter, but these are intended to be generated only by software
translators that produce Dudley layouts describing the HDF5 or PDB binary
files.

The HDF5 an PDB reference or pointer objects were primarily designed to support
a kind of "object store" feature that, at least at first glance, maps to the
way pointers are used in C/C++ data structures.  However, C/C++ pointers do
not map very well to scipy programs, since they objects they point to (at least
in scientific programs) are usually ndarrays, or to dict-like or list-like
objects containing them, which are first-class objects in scipy or Dudley.
