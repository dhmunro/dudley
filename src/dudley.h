/* Dudley data description language C API */

#include <stdio.h>
#include <stddef.h>

/* Assume at least C99 compiler to get fixed integer sizes. */
#include <stdint.h>
#define d_u1_t uint8_t
#define d_i1_t int8_t
#define d_u2_t uint16_t
#define d_i2_t int16_t
#define d_u4_t uint32_t
#define d_i4_t int32_t
#define d_u8_t uint64_t
#define d_i8_t int64_t

typedef d_i8_t d_item_t;  /* d_item_t i; D_Item *item = layout->items[i] */

typedef struct D_Stream D_Stream;
typedef struct D_Item D_Item;
typedef struct D_Filter D_Filter;

/* Dudley primitive datatypes not supported in C89. */
#define d_f2_t d_u2_t
#define d_U2_t d_u2_t
#define d_U4_t d_u4_t
/* Dudley pre-defined primitive data type values, indeterminate byte order */
#define D_u1 -1
#define D_i1 -2
#define D_b1 -3
#define D_S1 -4
#define D_U1 -5
#define D_u2 -6
#define D_i2 -7
#define D_f2 -8
#define D_c4 -9
#define D_U2 -10
#define D_u4 -11
#define D_i4 -12
#define D_f4 -13
#define D_c8 -14
#define D_U4 -15
#define D_u8 -16
#define D_i8 -17
#define D_f8 -18
#define D_c16 -19
/* subtract D_le for explicitly little-endian, subtract D_be for big-endian */
#define D_le 15
#define D_be 30
/* The pseudo-primitive D_null is the Dudley datatype for {} */
#define D_null 0
/* Return value signalling error in many calls returning a d_item_t */
#define D_ERROR -63
/* Kinds of items (itype): */
#define D_DATA 1
#define D_DICT 2
#define D_LIST 3
#define D_TYPE 4
#define D_PARAM 5

/* A shape is a list of integers {ndims, dim1, dim2, ...}:
 * Non-negative values are dimension lengths declared as integer values.
 * Negative values correspond to parameter references:
 *   -(value>>6) = parameter item index, (value&0x3f)-32 = + or - suffix count
 *   This has the side effect of limiting the +- suffix count to 31.
 */
 #define D_P(pitem) ((-(d_i8_t)(pitem))<<6|32)
 #define D_PS(pitem, nsfx) (((-(d_i8_t)(pitem))<<6)|(32+(nsfx)))
 #define D_PX(dim) ((-((dim)>>6)))
 #define D_PSX(dim) (((dim)&0x3f)-32)

/* Convert address to align argument.  Note -1 is reserved for not present. */
#define D_ADDR(a) (-2 - (d_item_t)(a))

/* D_Item is base class for all five kinds of items. */
#define D_ITEM_BASE int itype;\
    d_item_t parent;\
    char *name

struct D_Item {
    D_ITEM_BASE;
};

#ifdef __cplusplus
extern "C" {
#endif

/* Create and destroy a D_Stream. */

/* In general, a D_Stream has two parts: the binary file (or stream in general)
 * given by its FILE*, and its layout, which is the Dudley description of the
 * contents of its binary stream.  The Dudley layout (which is UTF-8 text) may
 * be appended to the end of the binary file to make a standalone binary file,
 * or it may be shared among multiple binary files or streams.
 * If you are opening a standalone file, or when opeing the first of several
 * files which are both standalone and share a common layout, use
 *    stream = d_stream(binaryfile, 0);
 * After the first file of a multi-file collection is opened, open subsequent
 * files with d_stream passing the first stream as the common layout:
 *    stream2 = d_stream(binaryfile2, stream);
 * Without an explict layout argument, Dudley must parse the text of the
 * (appended) layout; when you pass an explict layout argument, Dudley skips
 * parsing the layout or reading anything from the file, reducing its cost to
 * nearly zero.
 *
 * Dudley uses ftell to determine the position of the binaryfile pointer
 * passed to d_stream, and uses this as an offset for all addresses in the
 * file.  This allows Dudley layouts to describe embedded binary files, or for
 * multiple instances of a Dudley layout to be concatenated.
 *
 * The d_layout function takes a UTF-8 text file and parses it as a Dudley
 * layout, returning a D_Stream which has no associated binary file:
 *    layout = d_layout(textfile);
 * You may also pass a null pointer to open an empty layout, then declare items
 * in that layout to build up a layout in memory:
 *    layout = d_layout(0);
 * You can pass this in-memory layout to d_stream to open finary files with
 * this shared layout.
 *
 * Note that if the textfile is writable, you may declare new items in the
 * layout, just as for d_layout(0).
 *
 * The d_detach function returns the in-memory layout associated with the
 * stream, allowing you to keep it even after the d_close(stream), or to
 * use it as the layout for additional streams.
 *
 * The d_attach function allows you to associate a dudfile text stream with
 * the stream.  The current layout, if any, will be written to this FILE*,
 * as will any subsequent additions to the layout when the stream is flushed.
 * If the stream was by d_stream(binaryfile, 0), then this layout will also
 * be appended to the binaryfile when it is flushed, so that there will be
 * both a free-standing dudfile, and a copy of it appended to binaryfile.
 * This prevents the layout of at least the beginning of binaryfile from
 * being lost if the writing process is interrupted after additional data has
 * clobbered the layout but before the extended layout has been appended.
 *
 * The d_flush function makes both the binaryfile and any separate attached
 * ddudfile current, including appending a copy of the layout to the (current)
 * end of binaryfile, if it was opened with layout=0.
 *
 * The d_close function does a d_flush, then closes the binaryfile FILE*.
 */
extern D_Stream *d_stream(FILE *binaryfile, D_Stream *layout);
extern D_Stream *d_layout(FILE *dudfile);
extern D_Stream *d_detach(D_Stream *stream);
extern int d_attach(D_Stream *stream, FILE *dudfile);
extern int d_flush(D_Stream *stream);
extern int d_close(D_Stream *stream);

/* Query an existing item in a D_Stream. */
extern d_item_t dq_parent(D_Stream *stream, d_item_t item);  /* -1 if none */
extern const char *dq_name(D_Stream *stream, d_item_t item);  /* 0 if none */
/* If the current container is a dict or type, elements can also be accessed
 * by name using dq_item.  No matter what the current container, the
 * current meaning of a named type or parameter may be retrieved using
 * dq_type or dq_param.
 */
extern d_item_t dq_item(D_Stream *stream, const char *name);
extern d_item_t dq_type(D_Stream *stream, const char *name);
extern d_item_t dq_param(D_Stream *stream, const char *name);

/* Navigate and iterate over containers. */
extern d_item_t d_go_to(D_Stream *stream, d_item_t item);
extern d_item_t d_go_up(D_Stream *stream, d_item_t item);  /* closes types */
/* Iterate over elements of current container (dict, list, or type), in item
* declaration order for dict and type containers.
 */
extern d_item_t d_element(D_Stream *stream, d_item_t index);
extern d_i8_t d_count(D_Stream *stream, d_item_t item);  /* 0<=index<count */

/* Query data array or variable parameter, returning number of items -
 * shape in dq_data0 is as declared, including parameter references, while
 * xshape in dq_data is shape with parameters expanded.
 * On input, shape[0] or xshape[0] should be set to minus length of array.
 * If actual number of dimensions is larger, leading dimesnions will be
 * filled in, but shape[0] or xshape[0] will be negative of actual number
 * of dimensions.
 */
extern d_i8_t dq_data0(D_Stream *stream, d_item_t item, d_item_t *datatype,
                       d_i8_t **shape, d_item_t *align, D_Filter **filter);
extern d_i8_t dq_data(D_Stream *stream, d_item_t item,
                      d_item_t *datatype, d_i8_t **xshape);

/* Declare new items in a D_Stream.
 * Use name=0 if current container is list, or for anonymous items if current
 * container is dict or type.  For d_dict or d_list, name may refer to an
 * existing dict or list in order to make it the current container - in effect
 * reopening it.  (To reopen an existing dict or list whose parent is a list,
 * use d_element, then d_go_to; dq_item followed by d_go_to is equivalent to
 * d_dict or d_list if the container already exists.)
 */
extern d_item_t d_dict(D_Stream *stream, const char *name);
extern d_item_t d_list(D_Stream *stream, const char *name);
extern d_item_t d_type(D_Stream *stream, const char *name);
extern d_item_t d_data(D_Stream *stream, const char *name, d_item_t datatype,
                       d_i8_t *shape, d_item_t align, D_Filter *filter);
/* For d_param, use datatype=0 for fixed parameter and align for its value. */
extern d_item_t d_param(D_Stream *stream, const char *name,
                        d_item_t datatype, d_i8_t align);
/* Declare new list data item to have same type and shape as a previous one. */
extern d_item_t d_like(D_Stream *stream, d_item_t item, d_item_t align);

/* Read or write data.
 * Note that xshape must be expanded shape or 0 - no parameter references.
 *
 * On either read or write, any items which are declared to be in non-native
 * byte order in the Dudley layout are byte swapped before writing or after
 * reading.
 *
 * If stream is an in-memory stream, these fail; but you can use d_associate
 * to associate a memory buffer with such a stream.  If you have done that,
 * you may pass buf=0 to any of these read or write functions.  If every item
 * in a container has an associated memory buffer, you can call d_read or
 * d_write with the container item and Dudley will read or write everything
 * in the container.  To de-associate an item, call d_associate with buf=0.
 *
 * Note that supplying an xshape will implicitly set the current value of
 * any variable parameters in the stream if they have not been set, or
 * signal an error if the xshape does not agree with previously set parameter
 * values.
 * 
 * The d_get_params and d_set_params functions allow you to get or set all
 * of the dynamic parameter values at once.  If a dynamic parameter value has
 * not been set, then its value will be -2.  (Note that parameter value -1 has
 * a different meaning.)  The return value is the actual nummber of parameters,
 * while the count argument is the number of values in values.
 */
extern int d_read(D_Stream *stream, d_item_t item, void *buf, d_i8_t *xshape);
extern int d_write(D_Stream *stream, d_item_t item, void *buf, d_i8_t *xshape);
extern int d_pread(D_Stream *stream, d_item_t item, d_i8_t *leading,
                   d_i8_t min, d_i8_t max, void *buf, d_i8_t *xshape);
extern int d_pwrite(D_Stream *stream, d_item_t item, d_i8_t *leading,
                    d_i8_t min, d_i8_t max, void *buf, d_i8_t *xshape);
extern int d_associate(D_Stream *stream, d_item_t item,
                       void *buf, d_i8_t *xshape);
extern int d_get_params(D_Stream *stream, int count, d_i8_t *values);
extern int d_set_params(D_Stream *stream, int count, d_i8_t *values);

/* Get size of memory buffer to hold item, 0 if undefined parameters. */
extern size_t d_sizeof(D_Stream *stream, d_item_t item);

/* Load shape into buffer, returning input buffer address.
 *   shape = {ndims, dim1, dim2, ...}
 * Use D_P and D_PS macros for parameterized dimensions (fixed or dynamic).
 */
extern d_i8_t *d_shape(d_i8_t *buf, int ndims, ...);

/* Filter arguments are passed as double values; filter callback function must
 * convert to integer values as required.
 */
extern D_Filter *d_filter(const char *name, int nargs, ...);

#ifdef __cplusplus
}
#endif
