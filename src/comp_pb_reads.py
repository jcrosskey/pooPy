#!/usr/bin/python

import argparse
import sys
import os
import re 
## =================================================================
## Combine and compare different kinds of PacBio reads:
## 1. Filtered subreads (LCR)
## 2. CCS (circular consensus sequence)
## 3. RoI (Reads of insert)
## =================================================================
def comp_pb_reads(lcrFile, ccsFile, roiFile, outputFile):
    ''' Combine and compare different kinds of PacBio reads:

        1. Filtered subreads (LCR)
        2. CCS (circular consensus sequence)
        3. RoI (Reads of insert)
    '''
    if not os.path.exists(lcrFile):
        sys.stderr.write("lcrFile {} does not exist!\n".format(lcrFile))
        return -1
        
    if not os.path.exists(ccsFile):
        sys.stderr.write("ccsFile {} does not exist!\n".format(ccsFile))
        return -1
        
    if not os.path.exists(roiFile):
        sys.stderr.write("roiFile {} does not exist!\n".format(roiFile))
        return -1
        
    lcr_dict = dict()
    ccs_dict = dict()
    roi_dict = dict()

    with open(lcrFile,'r') as lcr:
        lcr.next()
        for line in lcr:
            seqID = line.strip().split('\t')[0]
            lcr_dict[seqID] = line.strip().split('\t')[1:]
    with open(ccsFile,'r') as ccs:
        for line in ccs:
            line = line.strip().split('\t')
            ccs_dict[line[0]] = line[1]
    with open(roiFile,'r') as roi:
        for line in roi:
            line = line.strip().split('\t')
            seqID = line[0][:line[0].rfind('/')]
            roi_dict[seqID] = line[1]

    myout = open(outputFile, 'w')
    myout.write("{}\t{}\t{}\t{}\t{}\t{}\n".format("ZMW_name","passes","min_len","max_len","ccs","roi"))
    for seqID in lcr_dict:
        myout.write("{}\t{}\t{}\t{}\t{}\t{}\n".format(seqID, lcr_dict[seqID][0], lcr_dict[seqID][1], lcr_dict[seqID][2], ccs_dict.get(seqID,0),roi_dict.get(seqID,0) ))
        
    myout.close()
## =================================================================
## argument parser
## =================================================================
parser = argparse.ArgumentParser(description="combine and compare different kinds of PacBio reads",
                                 prog = 'comp_pb_reads', #program name
                                 prefix_chars='-', # prefix for options
                                 fromfile_prefix_chars='@', # if options are read from file, '@args.txt'
                                 conflict_handler='resolve', # for handling conflict options
                                 add_help=True, # include help in the options
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter # print default values for options in help message
                                 )

## input files and directories
parser.add_argument("--lcr",help="input lcr file",dest='lcrFile',required=True)
parser.add_argument("--ccs",help="input ccs file",dest='ccsFile',required=True)
parser.add_argument("--roi",help="input roi file",dest='roiFile',required=True)

## output directory
parser.add_argument("-o","--out",help="output file",dest='outputFile',required=True)

## =================================================================
## main function
## =================================================================
def main(argv=None):
    
    if argv is None:
        args = parser.parse_args()

    comp_pb_reads(args.lcrFile, args.ccsFile, args.roiFile, args.outputFile)
##==============================================================
## call from command line (instead of interactively)
##==============================================================

if __name__ == '__main__':
    sys.exit(main())
