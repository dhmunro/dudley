"""Read HDF5 metadata (pure python, without h5py)

This will likely never be able to interpret everything in an arbitrary
HDF5 file, but it can handle many common cases and relatively simple
files, which is to say files with relatively simple structures.  It
gets progressively more likely to break as the number of objects in a
file increases, and as the HDF version increases.

Even the lowest level HDF5 API hides the address of the data on disk.
For uncompressed data, at least, it may be convenient to be able to
locate data in an HDF5 file without recourse to the very large and
tricky HDF5 library.

The hdf5meta API is very simple::

    f = HDF5(filename)
    var = f["varname"]  # get a variable from root group
    atype, size, shape, addr = var()  # call variable to get basic information
    # atype is numpy dtype name - "<f8", ">i4", etc. - for primitive
    #   types, a dict {name: (atype, size, shape, offset), ...} for compounds
    # atype of None means compressed or external or unknown data
    # size is number of bytes in one instances of atype, not whole var
    names = list(f)  # names of variables and subgroups in root group
    grp = f["grpname"]  # get a subgroup from root group
    # grp[varname], list(grp), len(grp) work as for f
    # grp() returns atype of dict (the dict class, not {}),
    #   size of len(grp), and None for shape and addr
    items = grp.items()  # or f.items() like dict items method
    data = grp.data()  # or f.data() like items, but only non-subgroups
    grps = grp.groups()  # or f.groups() like items, but only subgroups
"""

from struct import unpack
import re
import weakref
from functools import reduce

_heap_name = re.compile(rb"[^\x00]+")
_c_string = re.compile(rb"[^\x00]*")


class HDF5(object):
    def __init__(self, filename, noexpand=False):
        self.hdf5 = None
        signature = b"\x89HDF\r\n\x1a\n"
        f = open(filename, "rb")
        size = f.seek(0, 2)
        addr = 0
        while addr + 8 < size:
            f.seek(addr)
            if f.read(8) == signature:
                break
            addr = 2*addr if addr else 512
        else:
            f.close()
            raise ValueError("HDF5 superblock missing in {}".format(filename))
        base0 = addr  # signature address is 1st guess at base address
        addr += 8
        # HDF5 metadata fields are stored in little-endian byte order.
        vers, offsz, lensz, _ = unpack("<4B", f.read(4))
        addr += 4
        kleaf, kint, kintis = 4, 16, 32  # default values???
        if vers < 2:
            # free space, root group versions unused (only one value)
            # shared header version must be 0
            _, offsz, lensz, _, kleaf, kint = unpack("<4B2H", f.read(8))
            addr += 12  # skip 4 byte file consistency flags
            f.seek(addr)
            if vers:
                kintis, = unpack("<H", f.read(4))
                addr += 4
        offch = {4: "i", 8: "q"}[offsz]
        lench = {4: "i", 8: "q"}[lensz]
        base, superx, eof, root = unpack("<4"+offch, f.read(4*offsz))
        # superx = -1 if no superblock extension
        addr += 4*offsz
        if vers < 2:
            # do not care about driver info
            superx = -1  # free space address, always undefined
            f.seek(addr + offsz)  # skip root group link name offset
            root, = unpack("<"+offch, f.read(offsz))
        self.f = f
        self.base0 = base0
        self.base, self.eof = base, eof
        self.offsz, self.offch = offsz, offch
        self.lensz, self.lench = lensz, lench
        sharetab = shareind = None
        if superx > 0:  # version 2+ superblock extension object header
            for mtype, mflags, morder, msg, addr in self.oheader(superx):
                if mtype == 19:
                    _, kintis, kint, kleaf = unpack("<BHHH", msg)
                elif mtype == 15:
                    _, sharetab, shareind = unpack("<B"+offch+"B", msg)
                # ignore driver info
        self.kleaf, self.kint, self.kintis = kleaf, kint, kintis
        self.sharetab, self.shareind = sharetab, shareind
        self.root = HDF5Group(self, self.oheader(root))
        if not noexpand:
            self.root.expand()

    def __getitem__(self, key):
        return self.root.symtab[key]

    def __iter__(self):
        return iter(self.root.symtab)

    def __call__(self):
        return dict, None, None

    def __len__(self):
        return len(self.root)

    def items(self):
        return self.root.items()

    def data(self):
        return self.root.data()

    def groups(self):
        return self.root.groups()

    def btree1(self, addr, haddr=None, ndim=None):  # v1 B-tree
        base = self.base
        f = self.f
        offsz, offch = self.offsz, self.offch

        # Here, we do not care about the btree structure - we simply
        # want to generate the sequence of all leaves in the tree.
        # Since all nodes at one level of the tree are linked to their
        # siblings at the same level, all we need to do is to first
        # descend to level zero, preferably the leftmost leaf at
        # level zero, then follow the right sibling links to all
        # other level zero nodes.
        def read_node_header(addr):
            addr += base
            f.seek(addr)
            if f.read(4) != b"TREE":
                raise IOError("missing TREE - v1 B-tree")
            offch, offsz = self.offch, self.offsz
            return unpack("<BBH2"+offch, f.read(4+2*offsz))

        # First descend to leftmost node of level zero of btree.
        keysize = kfmt = None
        while True:  # Descend to level zero
            ntype, level, nent, left, right = read_node_header(addr)
            if not keysize:
                if left != -1:
                    raise IOError("v1 B-tree top level node has sibling")
                if not ntype:
                    # HDF5 format document III.A.1 (Version 1 B-trees) claims
                    # that group node keys are lensz, but offsets into local
                    # heap, whereas III.C (Symbol Table Entry) has link name
                    # offset of length offsz, which seems more correct.
                    # So assume keys in ntype=0 table are offsz, not lensz.
                    keysize = offsz
                elif ndim is not None:
                    keysize = 8 * (ndim + 2)
                    kfmt = "<2I{}q".format(ndim+1)
                else:
                    raise IOError("chunked data B-tree needs dimensionality")
            if level == 0:
                break
            # Otherwise move to child 0 (leftmost)
            f.seek(addr + 8 + 2*offsz + keysize)
            addr, = unpack("<"+offch, f.read(offsz))
        # Collect addresses of all level zero children.
        entrysz = keysize + offsz
        fmt = "<" + offch
        keys = [] if ntype else None
        leaves = []
        while True:
            addr += 8 + 2*offsz
            while nent > 0:
                if not ntype:  # group node
                    f.seek(addr + keysize)
                else:  # chunked storage mode
                    # key is (chunk size, filter mask, off0, ..., offN)
                    # discard trailing 0 at end of each key
                    keys.append(unpack(kfmt, f.read(keysize))[:-1])
                leaves.append(unpack(fmt, f.read(offsz))[0])
                addr += entrysz
                nent -= 1
            if right == -1:
                break
            addr = right
            ntype, level, nent, left, right = read_node_header(addr)
        if ntype:
            keys.append(unpack(kfmt, f.read(keysize))[:-1])  # key[N]

        # All leaf nodes collected in leaves, plus keys for ntype=1.
        if ntype:
            # For chunked data B-trees, just return chunk addresses and
            # keys from level zero.
            return leaves, keys

        # Group node leaves are symbol table entries.
        # Go ahead and collect the symbol table entries as a dict of
        # object header addresses.  Names themselves are in local heap.
        symtab = {}
        heap = self.local_heap(haddr + base)  # offset -> name map
        entrysz = 2*offsz + 24
        for addr in leaves:
            addr += base
            f.seek(addr)
            if f.read(4) != b"SNOD":
                raise IOError("missing SNOD - symbol table node")
            _, _, nent = unpack("<2BH", f.read(4))
            addr += 8
            while nent > 0:
                f.seek(addr)
                off, obj = unpack("<2"+offch, f.read(2*offsz))
                addr += 2*offsz + 24  # skip cache and scratch pad
                symtab[heap[off].decode("cp1252")] = obj
                nent -= 1
        return symtab

    def local_heap(self, addr):
        f = self.f
        addr += self.base
        f.seek(addr)
        if f.read(4) != b"HEAP":
            raise IOError("missing HEEP - local heap")
        addr += 8  # skip version, always 0
        f.seek(addr)
        lench, lensz, offch, offsz = (
            self.lench, self.lensz, self.offch, self.offsz)
        size, free, addr = unpack("<2"+lench+offch, f.read(2*lensz + offsz))
        f.seek(addr + self.base)
        heap = f.read(size)  # no use for offset to head of free list
        return {m.start(): m.group() for m in _heap_name.finditer(heap)}

    def btree2(self, addr, haddr=None, maxindex=None, otree=None):
        # v2 B-tree with fractal heap, possibly tracked and indexed
        f, base = self.f, self.base
        if addr < 0:
            return None
        f.seek(addr + base)
        if f.read(4) != b"BTHD":
            raise IOError("missing BTHD - v2 B-tree header")
        offsz, offch = self.offsz, self.offch
        lensz, lench = self.lensz, self.lench
        fmt = "<BBIHHBB"+offch+"H"+lench
        (version, btype, nodesz, recsz, depth, split, merge, root, nroot,
         nrecs) = unpack(fmt, f.read(14+offsz+lensz))
        max_nrec = (nodesz - 10) // recsz  # max records in leaf
        max_nrec_sz = self.min_nbytes(max_nrec)
        cum_max_nrec = max_nrec
        cum_max_nrec_sz = [0]*(depth + 1)
        for d in range(1, depth+1):
            entry_size = offsz + max_nrec_sz + cum_max_nrec_sz[d-1]
            max_nrec = (nodesz - 10 - entry_size) / (recsz + entry_size)
            cum_max_nrec *= max_nrec + 1
            cum_max_nrec_sz[d] = self.min_nbytes(cum_max_nrec)
        # Now build list of all leaf nodes.
        if root != -1:
            leaves = self.btree2child(root, nroot, nrecs, recsz, depth,
                                      max_nrec_sz, cum_max_nrec_sz, nodesz)
        else:
            leaves = []
        if btype == 5:  # group name B-tree
            if otree is not None and otree != -1:
                otree = self.btree2(otree)
            else:
                otree = None
            heap = self.fractal_heap(haddr, True)
            # heap item ends with:
            #   01, 00, namelen[1], name[namelen], hdroff[offsz]
            # --> each heap item is a link message, mtype == 6
            # Apparently, v2 B-tree type=5 puts items in order of name hash
            # recsz=11 is vers_type[1], heapoff[4], objlen[2]
            btree = {}
            for leaf in leaves:
                # nmhash = unpack("<I", leaf[:4])[0]
                sz = recsz - 4  # == 7 always?
                heapid = unpack("<q", leaf[4:] + b"\x00"*(8-sz))[0]
                order = otree[heapid & 0xffffffffffffff] if otree else None
                idtype = (heapid >> 4) & 0x3
                if idtype != 0:
                    raise IOError("tiny or huge object in B-tree")
                # Assume associated fractal heap always has
                # blkoffsz = 4 (maxheapsz = 32)
                # maximum managed object size that fits in 2 bytes
                hoff = (heapid >> 8) & 0xffffffff
                hlen = (heapid >> 40) & 0xffff
                msg = heap[hoff:hoff+hlen]  # mtype=6 obj header message
                ltype, name, addr, _ = decode_link_msg(msg)
                btree[name] = addr if order is None else (addr, order)
            if otree:
                btree = list(btree.items())
                btree.sort(lambda x: x[1][1])
                btree = dict([(x[0], x[1][0]) for x in btree])
            return btree
        elif btype == 6:  # creation order B-tree (otree)
            table = {}
            for i, leaf in enumerate(leaves):
                order = unpack("<q", leaf[:8])[0]
                sz = recsz - 8
                heapid = unpack("<q", leaf[8:] + b"\x00"*(8-sz))[0]
                table[heapid & 0xffffffffffffff] = unpack("<q", leaf[:8])
                table[heapid] = order
        elif btype == 7:  # shared object header messages
            pass
        return leaves

    @staticmethod
    def min_nbytes(x):
        if x < 0x100:
            return 1
        elif x < 0x10000:
            return 2
        elif x < 0x1000000:
            return 3
        elif x < 0x100000000:
            return 4
        elif x < 0x10000000000:
            return 5
        elif x < 0x1000000000000:
            return 6
        elif x < 0x100000000000000:
            return 7
        else:
            return 8

    def btree2child(self, addr, nrec, ntot, recsz, depth,
                    max_nrec_sz, cum_max_nrec_sz, nodesz):
        f, base = self.f, self.base
        addr += base
        f.seek(addr)
        signature = f.read(4)
        is_leaf = signature == b"BTLF"
        if not is_leaf and signature != b"BTIN":
            raise IOError("missing BTIN or BTLF - v2 B-tree node")
        version, btype = unpack("BB", f.read(2))
        addr += 6
        # Read nrec records owned by this node (leaf or internal)
        if nrec*recsz > nodesz:
            raise IOError("v2 B-tree sanity check failed")
        recs = [f.read(recsz) for i in range(nrec)]
        addr += nrec * recsz
        if is_leaf:
            return recs
        offsz, offch = self.offsz, self.offch
        ntsz = cum_max_nrec_sz[depth - 1]
        leaves = []
        get_child = self.btree2child
        for i in range(nrec+1):
            add = unpack("<"+offch, f.read(offsz))[0]
            nr = unpack("<q", f.read(max_nrec_sz) + b"\x00"*(8-max_nrec_sz))[0]
            addr += offsz + max_nrec_sz
            if ntsz:
                nt = unpack("<q", f.read(ntsz) + b"\x00"*(8-ntsz))[0]
                addr += ntsz
            else:
                nt = nr
            leaves.extend(get_child(add, nr, nt, recsz, depth-1,
                                    max_nrec_sz, cum_max_nrec_sz, nodesz))
            f.seek(addr)
            # presumably nrec records interleaved with nrec+1 children
            if i < nrec:
                leaves.append(recs[i])
        return leaves

    def fractal_heap(self, addr, check5=False):
        f, base = self.f, self.base
        addr += base
        f.seek(addr)
        if f.read(4) != b"FRHP":
            raise IOError("missing FRHP - fractal heap")
        lench, lensz, offch, offsz = (
            self.lench, self.lensz, self.offch, self.offsz)
        fmt = ("<BHHBI" + lench + offch + lench + offch + "8" + lench + "H" +
               "2" + lench + "HH" + offch + "H")
        n = 18 + 12*lensz + 3*offsz
        (_, idlen, filtlen, flags, maxsz,
         hugeid, hugetree, free, manager, mansz, allocsz, directit,
         nman, hugesz, nhuge, tinysz, ntiny, width, startsz, directmx,
         maxheapsz, nrows0, root, nrows1) = unpack(fmt, f.read(n))
        has_cksum = (flags & 2) != 0
        # off_size = self.min_nbytes(maxsz)
        # len_size = off_size if maxsz<directmx else self.min_nbytes(directmx)
        blkoffsz = (maxheapsz + 7) // 8
        max_dblock_rows = 2
        rat = directmx // startsz
        while rat > 1:
            max_dblock_rows += 1
            rat >>= 1
        log2start = 0
        rat = startsz * width
        while rat > 1:
            log2start += 1
            rat >>= 1
        if check5 and blkoffsz != 4:
            raise IOError("fractal heap for v2 B-tree has wrong offset size")
        if filtlen:
            # filtsz, filtmsk = unpack("<"+lench+"I", f.read(lensz+4))
            # filtinfo = f.read(filtlen)
            raise IOError("compressed fractal heap")
        #   512   512   512   512  --> startsz = 512, directmx = 65536
        #   512   512   512   512
        #  1024  1024  1024  1024
        #  ,,,
        # 32768 32768 32768 32768
        # 65536 65536 65536 65536   --> hence 9 rows max indirect block
        #   01 00 04 var0 0xc3 --> OHDR for var0 <checked>
        #   ^ at offset 21 = 0x15 from FHDB at 0x0eca2a,
        #      mtype == 6 link message length is 15 (1+1+1+4+8)
        #   which is indeed the first FHDB in the root FHIB
        if not nrows1:  # root is direct block
            f.seek(root + base)
            heap = f.read(startsz)
            if heap[:4] != b"FHDB":
                raise IOError("missing FHDB - fractal heap root block")
        else:  # root is indirect block
            ibheadsz = 5 + offsz + blkoffsz
            chksz = 4 if has_cksum else 0

            def get_fhib(self, addr, nrows):
                if nrows <= max_dblock_rows:
                    k = nrows * width
                    n = 0
                else:
                    k = max_dblock_rows * width
                    n = (nrows - max_dblock_rows) * width
                f.seek(root + base)
                iblock = f.read(ibheadsz + (k + n)*offsz + chksz)
                if iblock[:4] != b"FHIB":
                    raise IOError("missing FHIB - fractal heap root block")
                heap = b""
                bsz = nextsz = startsz
                fmt = "<" + offch
                i, j = ibheadsz, ibheadsz + offsz
                for row in range(max_dblock_rows):
                    if row >= nrows:
                        return heap  # no indirect blocks
                    for col in range(width):
                        addr = unpack(fmt, iblock[i:j])[0]
                        i, j = j, j + offsz
                        if addr == -1:
                            continue
                        f.seek(addr + base)
                        heap += f.read(bsz)
                    bsz, nextsz = nextsz, 2*nextsz
                mrows = max_dblock_rows + 1  # next generation iblock
                for row in range(max_dblock_rows, nrows):
                    for col in range(width):
                        addr = unpack(fmt, iblock[i:j])[0]
                        i, j = j, j + offsz
                        if addr == -1:
                            break
                        heap += get_fhib(self, addr, mrows)
                    else:
                        mrows += 1
                        continue
                    break
                return heap

            heap = get_fhib(self, root, nrows1)
        return heap

    def oheader(self, addr):
        addr += self.base
        f = self.f
        f.seek(addr)
        signature = f.read(4)
        addr += 4
        ver2 = signature == b"OHDR"
        contfmt = "<" + self.offch + self.lench
        msgs = []
        if ver2:
            _, flags = unpack("bb", f.read(2))
            addr += 2
            if flags & 32:
                addr += 16  # skip four timestamps
                f.seek(addr)
            if flags & 16:
                ncompact, ndense = unpack("<HH", f.read(4))
                addr += 4
            tracked = flags & 4
            # indexed = flags & 8
            flags &= 3
            n = [1, 2, 4, 8][flags]
            maxaddr, = unpack("<"+["B", "H", "i", "q"][flags], f.read(n))
            addr += n
            maxaddr += addr
            ntrack = 6 if tracked else 4
            while addr:
                addr1 = len1 = None
                maxaddr -= ntrack
                while addr < maxaddr:
                    mtype, msize, mflags = unpack("<BHB", f.read(4))
                    morder, = unpack("<H", f.read(2)) if tracked else (-1,)
                    addr += ntrack
                    # Note: msize is *not* padded
                    msg = f.read(msize) if msize else b""
                    if mtype == 16:
                        addr1, len1 = unpack(contfmt, msg)
                    else:
                        msgs.append((mtype, mflags, morder, msg, addr))
                    addr += msize
                    # ignore checksum at maxaddr+ntrack
                addr = addr1
                if len1 is not None:
                    addr += self.base
                    maxaddr = addr + len1
                    f.seek(addr)
                    signature = f.read(4)
                    addr += 4
                    if signature != b"OCHK":
                        break
        else:
            nmsgs, = unpack("<H", signature[2:])
            addr += 4  # skip object reference count
            f.seek(addr)
            # HDF5 format document IV.A.1 (Data Object Header Prefix)
            # shows object header size as 4-bytes, but
            # guess it is actually lensz bytes.  (Consistent with length
            # field in continuation messages.)
            lensz = self.lensz
            maxaddr = addr + unpack("<"+self.lench, f.read(lensz))[0]
            addr += lensz
            addr1 = len1 = None
            while nmsgs > 0:
                if addr > maxaddr:
                    if addr1 is None:
                        break
                    addr = addr1 + self.base
                    maxaddr = addr + len1
                    addr1 = len1 = None
                    f.seek(addr)
                mtype, msize, mflags = unpack("<HHB", f.read(8)[:5])
                addr += 8
                # Note: msize is padded to multiple of 8 bytes
                msg = f.read(msize) if msize else b""
                nmsgs -= 1
                if mtype == 16:  # header continuation message
                    addr1, len1 = unpack(contfmt, msg)
                    continue
                if mflags & 2:
                    msg = self.handle_shared(mtype, msg)
                msgs.append((mtype, mflags, -1, msg, addr))
                addr += msize
        # Note mflags & 2 means shared - msg points to actual mtype data.
        return msgs

    def handle_shared(self, mtype, msg):
        vers, stype = unpack("BB", msg[:2])
        addr = -1
        heapid = None
        if vers < 3:
            offsz, offch = self.offsz, self.offch
            i = 2 if vers > 1 else 8
            addr = unpack("<"+offch, msg[i:i+offsz])
        elif vers == 2:
            if stype == 2:
                offsz, offch = self.offsz, self.offch
                addr = unpack("<"+offch, msg[2:2+offsz])
            elif stype == 1:
                heapid = unpack("<q", msg[2:10])
                if not self.sharetab:
                    heapid = None  # ignore error
            else:
                # unclear why this message is here
                return msg
        if addr != -1:
            f = self.f
            addr0 = f.tell()
            for m in self.oheader(addr):
                if m[0] == mtype and not m[1] & 2:
                    msg = m[3]
                    break
            f.seek(addr0)
        if heapid is not None:
            pass  # dont understand this yet
        return msg

    def sort(self):
        return self.root.sort()


class HDF5Object(object):
    def __init__(self, parent):
        self.parent = weakref.ref(parent)  # None for root group
        self.hdf5 = parent.hdf5
        self.noise = []  # unnecessary header messages
        self.filters = None
        self.is_group = False

    def __call__(self):
        return None, None, None, None

    def key(self):
        return 2**62 + 1

    def header_msg(self, mtype, mflags, morder, msg, addr):
        if mtype == 17:  # v1 group
            obj = HDF5Group(self)
            obj.header_msg(mtype, mflags, morder, msg, addr)
        elif mtype in (2, 6, 10):  # v2 group
            obj = HDF5Group(self)
            obj.header_msg(mtype, mflags, morder, msg, addr)
        elif mtype in (1, 3, 8, 7):  # data
            obj = HDF5Data(self)
            obj.header_msg(mtype, mflags, morder, msg, addr)
        else:
            if mtype == 11:  # filter pipline
                self.filters = mtype, mflags, morder, msg, addr
            else:
                self.noise.append((mtype, mflags, morder, msg, addr))
            obj = self
        return obj


class HDF5Group(object):
    def __init__(self, generic, msgs=None):
        self.is_root = is_root = msgs is not None
        self._symtab = self.v2 = self.compact = None
        if not is_root:
            self.parent = generic.parent
            self.hdf5 = generic.hdf5
            self.noise = generic.noise
            self.filters = generic.filters
        else:
            self.parent = lambda *args: self  # emulate weakref
            self.hdf5 = weakref.ref(generic)
            self.noise = []
            self.filters = None
            for args in msgs:
                self.header_msg(*args)
        self.is_group = True
        self._sorted = None

    def __call__(self):
        return dict, len(self), None, None

    @property
    def symtab(self):
        _symtab = self._symtab
        if _symtab is None:
            hdf5 = self.hdf5()
            # The btree adds nothing at all logically - it's entire
            # purpose is to keep the symtab entries sorted alphabetically.
            # All of the information is actually in the associated heap.
            if self.compact is not None:
                btree = self.compact
            elif self.v2:
                btree = hdf5.btree2(self.baddr, self.haddr,
                                    self.maxindex, self.otree)
            else:
                btree = hdf5.btree1(self.baddr, self.haddr)
            for name, obj in btree.items():
                msgs = hdf5.oheader(obj)
                obj = HDF5Object(self)
                for args in msgs:
                    obj = obj.header_msg(*args)
                btree[name] = obj
            self._symtab = _symtab = btree
        return _symtab

    def expand(self):
        symtab = self.symtab
        for item in symtab.values():
            if item.is_group:
                item.expand()

    def __len__(self):
        return len(self.symtab)

    def __getitem__(self, key):
        return self.symtab[key]

    def __iter__(self):
        return iter(self.symtab)

    def items(self):
        return self.symtab.items()

    def data(self, good=False):
        for name, var in self.symtab.items():
            if var.is_group:
                continue
            if good and var()[0] is None:
                continue
            yield name, var

    def groups(self):
        for name, var in self.symtab.items():
            if var.is_group:
                yield name, var

    def key(self):
        _sorted = self.sort()
        return 2**62 + 2 if not _sorted else self[_sorted[0]].key()

    def sort(self):
        # Data items first
        #   Good data first, sorted by address (min address for chunked)
        #   Bad data next, alphabetically
        # Subgroups next, by minimum address or alphabetically if none
        # This recurses to all subgroups.
        _sorted = self._sorted
        if _sorted is None:
            dkeys = []
            for name, d in self.data():
                dkeys.append((d.key(), name))
            dkeys.sort()
            gkeys = []
            for name, g in self.groups():
                gkeys.append((g.key(), name))
            _sorted = [d[1] for d in dkeys + gkeys]
        return _sorted

    def header_msg(self, mtype, mflags, morder, msg, addr):
        # Need an mtype=17 symbol table message for a v1 btree.
        # Need mtype=10 group info message and mtype=2 link info message
        #   for a v2 btree.
        if mtype == 17:
            if self.v2 is not None:
                raise IOError("Group cannot be both v1 and v2")
            self.v2 = False
            hdf5 = self.hdf5()
            offsz, offch = hdf5.offsz, hdf5.offch
            self.baddr, self.haddr = unpack("<2"+offch, msg[:2*offsz])
        elif mtype == 2:
            if not self.v2 and self.v2 is not None:
                raise IOError("Group cannot be both v2 and v1")
            self.v2 = True
            _, flags = unpack("2B", msg[:2])
            msg = msg[2:]
            tracked = flags & 1
            indexed = flags & 2
            if tracked:
                self.maxindex, = unpack("<q", msg[:8])
                msg = msg[8:]
            else:
                self.maxindex = None
            hdf5 = self.hdf5()
            offsz, offch = hdf5.offsz, hdf5.offch
            self.haddr, self.baddr = unpack("<2"+offch, msg[:2*offsz])
            if indexed:
                self.otree, = unpack("<"+offch, msg[2*offsz:3*offsz])
            else:
                self.otree = None
        elif mtype == 6:
            if not self.v2 and self.v2 is not None:
                raise IOError("Group cannot be both v2 and v1 (6)")
            self.v2 = True
            ltype, name, value, order = decode_link_msg(msg)
            if ltype == 0:
                compact = self.compact
                if compact is None:
                    compact = self.compact = {}
                compact[name] = value  # object header
        elif mtype == 10:
            if not self.v2 and self.v2 is not None:
                raise IOError("Group cannot be both v2 and v1 (10)")
            self.v2 = True
            self.noise.append((mtype, mflags, morder, msg, addr))
        else:
            if mtype == 11:  # filter pipline
                self.filters = mtype, mflags, morder, msg, addr
            else:
                self.noise.append((mtype, mflags, morder, msg, addr))
        return self


def decode_link_msg(msg):
    _, flags = unpack("2B", msg[:2])
    msg = msg[2:]
    ltype = 0  # default is hard link
    order = None
    charset = "cp1252"
    if flags & 0x8:
        ltype = unpack("B", msg[:1])
        msg = msg[1:]
    if flags & 0x4:
        order = unpack("q", msg[:8])
        msg = msg[8:]
    if flags * 0x10:
        if unpack("B", msg[:1]):
            charset = "utf-8"
        msg = msg[1:]
    flags &= 3
    lensz = [1, 2, 4, 8][flags]
    namelen, = unpack(["B", "<H", "<I", "<q"][flags], msg[:lensz])
    msg = msg[lensz:]
    name = msg[:namelen].decode(charset)
    msg = msg[namelen:]
    value = None
    if ltype == 0:
        offsz = len(msg[:8])
        value = unpack("<q", msg + b"\x00"*(8-offsz))[0]
    else:
        length = unpack("<H", msg[:2])
        msg = msg[2:]
        if ltype == 1:
            value = msg[:length].decode(charset)
        else:
            value = (length, charset, msg)
    return ltype, name, value, order


class HDF5Data(object):
    def __init__(self, generic):
        self.parent = generic.parent
        self.hdf5 = generic.hdf5
        self.noise = generic.noise
        self.filters = generic.filters
        self.atype = self.itemsize = self.shape = self.addr = None
        self.maxdims = self.url = self.keys = self.chunk = None
        # Note: If maxdims disagrees with shape for non-unlimited
        #   dimensions, data may actually be stored with strides
        #   corresponding to maxdims, not shape?
        self.enumeration = None
        # filters is not None means data is compressed
        # maxdims item of -1 indicates an unlimited dimension
        # chunk and keys is not None indicates chunked storage
        #   chunk is shape of each chunk, keys is tuple of nd-offsets
        #   addr is tuple of chunk addresses
        # url is not None indicates external storage
        self.is_group = False

    def __call__(self):
        if self.filters or self.url:
            return None, self.shape, self.addr
        return self.atype, self.itemsize, self.shape, self.addr

    def key(self):
        addr = self.addr
        if addr is None or addr == -1 or self.filters or self.url:
            return 2**62
        if isinstance(addr, tuple):
            addr = min(addr)  # addr is tuple for chunked data
        return addr

    def szch(self, mask):
        hdf5 = self.hdf5()
        offs = (hdf5.offsz, hdf5.offch) if (mask & 1) else ()
        if mask & 2:
            offs += hdf5.lensz, hdf5.lench
        return offs

    def header_msg(self, mtype, mflags, morder, msg, addr):
        if mtype == 1:  # dataspace - that is, shape
            version, ndims, flags, stype = unpack("4B", msg[:4])
            if version == 1:
                msg = msg[8:]
            else:
                msg = msg[4:]
            if version == 2 and stype == 2:
                self.shape = (0)
            elif ndims:
                lensz, lench = self.szch(2)
                shape = unpack("<{}".format(ndims)+lench, msg[:ndims*lensz])
                msg = msg[ndims*lensz:]
                if flags & 1:
                    self.maxdims = unpack("<{}".format(ndims)+lench,
                                          msg[:ndims*lensz])
                    msg = msg[ndims*lensz:]
                # description of permutation sounds like shape and maxdims
                # always in canonical C-like order, so ignore flags&2 here
            else:
                shape = ()
            if self.shape:  # already got datatype message for array class
                self.shape += shape
            else:
                self.shape = shape
        elif mtype == 3:  # datatype
            atype, itemsize, msg = self.get_type(msg, True)
            # In version 1, msg is always multiple of 8 bytes.
            # In OHDR versions, msg is not padded, and so should
            # always be empty here.
            if len(msg) > 7:
                print("WARNING - type 3 message too long", len(msg))
            if isinstance(atype, tuple):
                if self.shape:  # already got dataspace message
                    self.shape = atype[1] + self.shape
                else:
                    self.shape = atype[1]
                atype = atype[0]
            self.atype, self.itemsize = atype, itemsize
        elif mtype == 8:  # data layout
            hdf5 = self.hdf5()
            base = hdf5.base
            version, = unpack("B", msg[:1])
            if version < 3:
                ndims, cls = unpack("BB", msg[1:3])
                msg = msg[8:]
                if ndims and cls == 2:  # chunked
                    ndims -= 1
                offsz, offch = self.szch(1)
                if cls:  # contiguous or chunked
                    addr = unpack("<"+offch, msg[:offsz])[0] + base
                msg = msg[offsz:]
                if ndims:
                    shape = unpack("<{}I".format(ndims), msg[:ndims*4])
                    msg = msg[ndims*4:]
                else:
                    shape = ()
                if not cls:  # compact
                    # value = msg[4:]  # skip data size in bytes
                    addr += 12 + 4*ndims
                elif cls > 1:  # chunked
                    self.chunk = shape
                    if addr != -1:
                        addrs, keys = hdf5.btree1(addr + base, ndim=ndims)
                        addr = tuple(a+base for a in addrs)
                        self.keys = keys
                    else:
                        self.keys = ()
            else:
                cls, = unpack("B", msg[1:2])
                msg = msg[2:]
                if not cls:  # compact
                    # value = msg[4:]
                    addr += 4  # skip data size in bytes
                elif cls == 1:  # contiguous
                    offsz, offch = self.szch(1)
                    addr = unpack("<"+offch, msg[:offsz])[0] + base
                elif version < 4:  # version 3 chunked
                    ndims = unpack("B", msg[:1])[0]
                    offsz, offch = self.szch(1)
                    addr = unpack("<"+offch, msg[1:1+offsz])[0] + base
                    msg = msg[1+offsz:]
                    if addr != -1:
                        addrs, keys = hdf5.btree1(addr + base, ndim=ndims)
                        addr = tuple(a+base for a in addrs)
                        self.keys = keys
                    else:
                        self.keys = ()
                    if ndims:
                        shape = unpack("<{}I".format(ndims), msg[:ndims*4])
                        msg = msg[ndims*4:]
                    else:
                        shape = ()
                    self.chunk = shape
                elif cls == 2:  # version 4 chunked
                    pass
                else:  # version 4 cls==3, ignore virtual storage
                    addr = -1
                    self.url = True
            self.addr = addr
        elif mtype == 7:  # external data
            self.url = True  # ignore URLs for now, but mark as external
        else:
            if mtype == 11:  # filter pipline
                self.filters = mtype, mflags, morder, msg, addr
            else:
                self.noise.append((mtype, mflags, morder, msg, addr))
        return self

    def get_type(self, msg, toplevel=False):
        bits, size = unpack("<2I", msg[:8])
        msg = msg[8:]
        version = (bits >> 4) & 0xf
        cls = bits & 0xf
        bits = (bits >> 8) & 0xffffff
        if cls == 0:  # fixed-point
            atype = ">" if (bits & 1) else "<"
            atype += "i" if (bits & 8) else "u"
            atype += "{}".format(size)
            off, prec = unpack("<HH", msg[:4])
            msg = msg[4:]
        elif cls == 1:  # floating-point
            atype = ">f" if (bits & 1) else "<f"
            atype += "{}".format(size)
            if bits & 64:
                atype = "vax-" + atype
            # sgna = (bits >> 8) & 0xf
            # off, prec, expa, expz, mana, manz, bias = unpack("<HH4BI",
            #                                                  msg[:12])
            msg = msg[12:]
        elif cls == 2:  # time
            atype = ">u" if (bits & 1) else "<u"
            atype += "{}".format(size)
            prec, = unpack("<H", msg[:2])
            msg = msg[2:]
        elif cls == 3:  # string
            atype = "U1" if (bits & 16) else "S1"
        elif cls == 4:  # bit field
            atype = ">u" if (bits & 1) else "<u"
            atype += "{}".format(size)
            off, prec = unpack("<HH", msg[:4])
            msg = msg[4:]
        elif cls == 5:  # opaque
            sz = bits & 0xff  # error if not multiple of 8...
            m = _c_string.match(msg)
            atype = m.group() + "-o{}".format(size)
            msg = msg[((sz+7)//8)*8:]  # ...but be safe
        elif cls == 6:  # compound
            atype = {}
            if version < 3:
                offsz = offch = None
            elif size < 0x100:
                offsz, offch = 1, "B"
            elif size < 0x10000:
                offsz, offch = 2, "H"
            elif size < 0x1000000:
                offsz, offch = 3, "I"  # special treatment
            else:
                offsz, offch = 4, "I"
            nmemb = bits & 0xffff
            while nmemb > 0:
                nmemb -= 1
                m = _c_string.match(msg)
                name = m.group()
                if version < 3:
                    sz = ((m.end()+8) // 8) * 8  # length of name in bytes
                    msg = msg[sz:]
                    off, = unpack("<I", msg[:4])
                    msg = msg[4:]
                else:
                    msg = msg[m.end()+1:]
                    n = offsz if offsz != 3 else 4
                    off, = unpack("<"+offch, msg[:n])
                    msg = msg[offsz:]
                    if offsz == 3:
                        off &= 0xffffff
                if version == 1:
                    ndims, = unpack("B", msg[:1])
                    msg = msg[12:]  # skip dim permutation and reserved bytes
                    shape = unpack("<{}I".format(ndims), msg[:ndims*4])
                    msg = msg[ndims*4:]
                else:
                    shape = ()  # uses Array for shape
                typ, sz, msg = self.get_type(msg)
                if isinstance(typ, tuple):
                    # member has Array type (class 10), combine shapes
                    typ, shape = typ[0], shape + typ[1]
                atype[name] = typ, sz, shape, off
        elif cls == 7:  # reference
            atype = "refreg" if (bits & 1) else "refobj"
        elif cls == 8:  # enumerated
            atype, sz, msg = self.get_type(msg)  # assert sz == size ??
            nmemb = bits & 0xffffff
            enumeration = {}
            names = []
            while nmemb > 0:
                nmemb -= 1
                m = _c_string.match(msg)
                name = m.group()
                if version < 3:
                    sz = ((m.end()+8) // 8) * 8  # length of name in bytes
                    msg = msg[sz:]
                else:
                    msg = msg[m.end()+1:]
                names.append(name)
            for name in names:
                enumeration[name] = msg[:sz]
                msg = msg[sz:]
            if toplevel:
                self.enumeration = enumeration
        elif cls == 9:  # variable-length
            string = bits & 1
            # padding = (bits & 0x300) >> 8
            atype = "varlen-"
            typ, sz, msg = self.get_type(msg)
            if string:
                atype += "U1" if (bits & 0x10000) else "S1"
            elif isinstance(type, str):
                atype += typ
        elif cls == 10:  # array
            ndims, = unpack("B", msg[:1])
            if version < 3:
                msg = msg[4:]  # skip dim permutation and reserved bytes
            else:
                msg = msg[1:]
            if ndims:
                shape = unpack("<{}I".format(ndims), msg[:ndims*4])
                if version < 3:
                    msg = msg[ndims*8:]
                else:
                    msg = msg[ndims*4:]
            else:
                shape = ()
            typ, sz, msg = self.get_type(msg)
            if isinstance(typ, tuple):
                typ, shape = typ[0], shape + typ[1]
            atype = typ, shape
            # need to correct size to reflect base type, not whole array
            if shape and size:
                size /= reduce((lambda x, y: x * y), shape)
        return atype, size, msg


# Message types:
#   mflags & 2: shared message (mtype is type of shared message?)
# 0 NIL
# 1 dataspace (shape)
# 2 link info
# 3 datatype
# 4 old fill value
# 5 fill value
# 6 link
# 7 external data files
# 8 data layout (contiguous, chunked, compact, virtual)
# 9 bogus
# 10 group info (related to link info message)
# 11 filter pipeline
# 12 attribute
# 13 comment
# 14 old mod time
# 15 shared message table (only in superblock extension)
# 16 object header continuation
# 17 symbol table (old style groups with v1 B-tree, local heap)
# 18 mod time
# 19 B-tree K-values (only in superblock extension)
# 20 driver info
# 21 attribute info
# 22 object reference count
