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
            self.ref_dict[self.ref] = int(record_fields[6])
        self.rstart = int(record_fields[7])
        self.rend = int(record_fields[8])
        self.rstrand = record_fields[9] # tstrand
        self.nummatch = int(record_fields[11])
        self.nummismatch = int(record_fields[12])
        self.numins = int(record_fields[13])
        self.numdel = int(record_fields[14])
    def __lt__(self, r_m5):
        return self.qstart < r_m5.qstart
    def __eq__(self, r_m5):
        return (self.qstart == r_m5.qstart) and (self.mapLen == r_m5.mapLen)
    def __str__(self):
        s = "{} mapped to {} on {} strand with mapped segment length {}\n".format(self.qname, self.ref, self.rstrand, self.mapLen)
        s += "{} {} | {} {} | {} | {} \n".format(self.qstart, self.qend, self.rstart, self.rend, self.qlen, self.ref_dict[self.ref])
        return s
    def contains(self, r_m5):
        return (self.rstart < r_m5.rstart and self.rend > r_m5.rend)
    def end_connected(self, m5):
        """ check and see if two mappings are separated because of circularity of the genome """
        if self.ref != m5.ref: # not mapped to the same references
            return False
        elif self.rstart < 15 and (self.ref_dict[self.ref] - m5.rend) < 15:
            return True
        else:
            return False


class ReadMap:
    """ Class to store all the mappings of a contig/read to the reference genome """
    def __init__(self, m5=None):
        if m5 is None:
            self.name = ""
            self.records = []
            self.maxMapLen = 0
            self.length = 0
        else:
            self.name = m5.qname
            self.length = m5.qlen
            self.records=[m5]
            self.maxMapLen = m5.mapLen
    def add_m5(self,m5):
        if m5.qname != self.name:
            sys.stderr.write("Cannot add this record to the current read, they don't have the same name!\n")
        else:
            self.records.append(m5)
            if m5.mapLen > self.maxMapLen:
                self.maxMapLen = m5.mapLen
    def sort(self, key="start"):
        if key == "start":
            self.records.sort()
        else:
            self.records = sorted(self.records, key=lambda record:record.mapLen)
    # remove mappings included in a longer mapping
    def simplify(self):
        self.records.sort()
        i = 0
        while i < len(self.records):
            r_i = self.records[i]
            j = i + 1
            while j < len(self.records):
                r_j = self.records[j]
                if not r_i < r_j:
                    break
                elif r_i.contains(r_j):
                    del self.records[j]
                    j -= 1
    # number of mappings for this read
    def tot_maps(self):
        return len(self.records)
    def tot_mapLen(self):
        return sum(j.mapLen for j in self.records)
    def map_type(self):
        if self.tot_mapLen() > self.length * 0.95:
            if self.tot_maps() == 1: 
                return "NoError"
            elif self.tot_maps() > 2:
                return "Chimeric"
            elif self.records[0].end_connected(self.records[1]):
                return "Fake"
            else:
                return "Chimeric"
        else:
            return "partial"
    def __str__(self):
        return "".join(r.__str__() for r in self.records)


def m5_stat(m5_fin, minSeg, out):
    m5_fin.readline()
    read = ReadMap()
    for line in m5_fin:
        m5 = BlasrM5(line)
        if m5.qname != read.name:
            if read.name != "" and read.length >= minSeg:
                out.write("{}\t{}\t{}\n".format(read.name, read.map_type(), read.length))
                #out.write(read.__str__())
            read = ReadMap(m5)
        else:
            read.add_m5(m5)
    if read.name != "" and read.length >= minSeg:
        out.write("{}\t{}\t{}\n".format(read.name, read.map_type(), read.length))
        #out.write(read.__str__())



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
