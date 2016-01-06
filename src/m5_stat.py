#!/usr/bin/env python

# -*- coding: utf-8 -*-
"""
m5_stat

Created on Tue May 26 14:23:09 EDT 2015

@author: JJ Crosskey
"""
import sys
import argparse

## =================================================================
## argument parser
## =================================================================
parser = argparse.ArgumentParser(description="parse .m5 file and get alignment summary statistics",
                                 prog = 'm5_stat', #program name
                                 prefix_chars='-', # prefix for options
                                 fromfile_prefix_chars='@', # if options are read from file, '@args.txt'
                                 conflict_handler='resolve', # for handling conflict options
                                 add_help=True, # include help in the options
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter # print default values for options in help message
                                 )

## input files and directories
parser.add_argument("-i","--in",help="input .m5 file (generated by BLASR)",dest='m5File', default=sys.stdin, type=argparse.FileType('r'))

## options
parser.add_argument("-m", "--minSeg", help="minimum length of the mapped query segment", dest="minSeg", default=1000, type=int)
#parser.add_argument("-p", "--minPercent", help="percent of mapped length below which read is considered chimeric", dest="minPercent", default=0.95, type=float)

## output directory
parser.add_argument("-o","--out",help="output file",dest='output', default=sys.stdout, type=argparse.FileType('w'))
#parser.add_argument("-mo","--mapout",help="mapped length output file",dest='mapout', required=True, type=argparse.FileType('w'))

## =================================================================
## parsing function
## =================================================================
class BlasrM5:
    """Class for Blasr's .m5 result, including mapping record"""
    ref_dict = dict()
    def __init__(self, m5_string):
        record_fields = m5_string.strip().split()
        self.qname = record_fields[0]
        self.qlen = int(record_fields[1])
        self.qstart = int(record_fields[2])
        self.qend = int(record_fields[3])
        self.mapLen = self.qend - self.qstart
        self.qstrand = record_fields[4]
        self.ref = record_fields[5]
        # ref_name: ref_length
        if self.ref not in self.ref_dict:
            self.ref_dict[self.ref] = [0] * int(record_fields[6])
        self.rstart = int(record_fields[7])
        self.rend = int(record_fields[8])
        for i in xrange(self.rstart, self.rend):
            self.ref_dict[self.ref][i] = 1
        self.rstrand = record_fields[9] # tstrand
        self.nummatch = int(record_fields[11])
        self.nummismatch = int(record_fields[12])
        self.numins = int(record_fields[13])
        self.numdel = int(record_fields[14])
        self.indel = self.numins + self.numdel
    # sort the mappings (interal) by their starting coordinates
    # for later intersection and union
    def __lt__(self, r_m5):
        if self.qstart == r_m5.qstart:
            return self.mapLen < r_m5.mapLen
        else:
            return self.qstart < r_m5.qstart
    def __eq__(self, r_m5):
        return (self.qstart == r_m5.qstart) and (self.mapLen == r_m5.mapLen)
    def __str__(self):
        s = "{} mapped to {} on {} strand with mapped segment length {}\n".format(self.qname, self.ref, self.rstrand, self.mapLen)
        s += "{} {} | {} {} | {} | {} \n".format(self.qstart, self.qend, self.rstart, self.rend, self.qlen, len(self.ref_dict[self.ref]))
        return s
    def end_connected(self, m5):
        """ check and see if two mappings are separated because of circularity of the genome """
        if self.ref != m5.ref: # not mapped to the same references
            return False
        elif self.rstart < 15 and (len(self.ref_dict[self.ref]) - m5.rend) < 15:
            return True
        else:
            return False


class interval:
    """class for a closed interval, for intersection, union operations, etc (to be added) """
    def __init__(self, start, end):
        assert start < end
        self.start = start
        self.end = end
    def __str__(self):
        s = "[{}, {}]".format(self.start, self.end)
        return s
    def __lt__(self, r):
        return self.start < r.start
    def __len__(self):
        return self.end - self.start
    def contains(self, right):
        return (self.start <= right.start and self.end >= right.end)
    def intersect(self, r):
        if self < r:
            if self.end < r.start:
                return None
            else:
                return interval(r.start, min(r.end, self.end))
        else:
            if r.end < self.start:
                return None
            else:
                return interval(self.start, min(self.end, r.end))
    def union(self,r):
        if self < r:
            if self.end < r.start:
                return [self, r]
            else:
                return [interval(self.start, max(r.end, self.end))]
        else:
            if r.end < self.start:
                return [r, self]
            else:
                return [interval(r.start, max(r.end, self.end))]


class ReadMap:
    """ Class to store all the non-repetitive mappings of a contig/read to the reference genome """
    # constructor of the ReadMap.
    # If an m5 record is given, save it as the its first mapping
    # otherwise start a contig mapping with empty record
    def __init__(self, m5=None):
        if m5 is None:
            self.name = ""
            self.records = []
            self.length = 0
        else:
            self.name = m5.qname
            self.length = m5.qlen
            self.records=[m5]
        self.is_sorted = False
    # Add another mapping record to the class
    def add_m5(self,m5):
        if m5.qname != self.name:
            sys.stderr.write("Cannot add this record to the current read, they don't have the same name!\n")
        else:
            self.records.append(m5)
    # sort the mappings
    def sort(self):
        self.records.sort()
    # remove mappings included in a longer mapping
    def simplify(self):
        self.sort()
        record_indices = [0]
        i = 1
        r = interval(self.records[0].qstart, self.records[0].qend)
        union_intervals = [r] # union of the mapped intervals
        tot_maps = 1
        tot_mapLen = 0
        max_mapLen = len(r)
        while i < len(self.records):
            r_i = interval(self.records[i].qstart, self.records[i].qend)
            r_previous = union_intervals[-1]
            if len(r_i) > max_mapLen:
                max_mapLen = len(r_i)
            if r_i.contains(r_previous):
                union_intervals[-1] = r_i
                record_indices[-1] = i
            elif r_previous.contains(r_i):
                union_intervals[-1] = r_previous
            else:
                union_intervals = union_intervals[:-1] + r_previous.union(r_i)
                tot_maps += 1
                record_indices.append(i)
            i += 1
        self.max_mapLen = max_mapLen
        self.intervals = union_intervals
        self.tot_maps = tot_maps
        self.tot_mapLen = sum(len(x) for x in union_intervals)
        self.records = [self.records[i] for i in record_indices]
        self.is_sorted = True
        self.refs = list(set([x.ref for x in self.records]))

    def map_type(self):
        if not self.is_sorted:
            self.simplify()
        if self.max_mapLen > self.length * 0.95:
            return "NoError"
        elif self.tot_mapLen > self.length * 0.95:
            if self.tot_maps == 1: 
                return "NoError"
            elif self.tot_maps > 2:
                return "Chimeric"
            elif self.records[0].end_connected(self.records[1]):
                return "Fake"
            else:
                return "Chimeric"
        else:
            return "partial"
    def __str__(self):
        return "".join(r.__str__() for r in self.intervals)


def m5_stat(m5_fin, minSeg, out):
    m5_fin.readline()
    read = ReadMap()
    mismatch = 0
    indel = 0
    max_mapLen = 0
    tot_mapLen = 0
    for line in m5_fin:
        m5 = BlasrM5(line)
        if m5.qname != read.name:
            if read.name != "" and read.length >= minSeg:
                out.write("{}\t{}\t{}\t{}\t{}\t{}\t({})\t".format(read.name, read.map_type(), read.length, read.tot_mapLen,\
                        read.tot_maps, len(read.refs), ",".join(read.refs)))
                out.write(read.__str__())
                out.write("\n")
                if read.max_mapLen > max_mapLen:
                    max_mapLen = read.max_mapLen
                mismatch += sum(x.nummismatch for x in read.records)
                indel += sum(x.indel for x in read.records)
                tot_mapLen += read.tot_mapLen
            read = ReadMap(m5)
        else:
            read.add_m5(m5)
    if read.name != "" and read.length >= minSeg:
        out.write("{}\t{}\t{}\t{}\t{}\t{}\t({})\t".format(read.name, read.map_type(), read.length, read.tot_mapLen,\
                read.tot_maps, len(read.refs), ",".join(read.refs)))
        out.write(read.__str__())
        out.write("\n")
        if read.max_mapLen > max_mapLen:
            max_mapLen = read.max_mapLen
        mismatch += sum(x.nummismatch for x in read.records)
        indel += sum(x.indel for x in read.records)
        tot_mapLen += read.tot_mapLen
    covered_bps = sum([sum(m5.ref_dict[r]) for r in m5.ref_dict])
    sys.stdout.write("Largest alignment: {}\n".format(max_mapLen))
    sys.stdout.write("Total mismatches: {}\n".format(mismatch))
    sys.stdout.write("Total indels: {}\n".format(indel))
    sys.stdout.write("Total mapped length: {}\n".format(tot_mapLen))
    sys.stdout.write("Total covered bases: {}\n".format(covered_bps))



## =================================================================
## main function
## =================================================================
def main(argv=None):
    
    if argv is None:
        args = parser.parse_args()
    m5_stat(args.m5File, args.minSeg, args.output)

##==============================================================
## call from command line (instead of interactively)
##==============================================================

if __name__ == '__main__':
    sys.exit(main())
