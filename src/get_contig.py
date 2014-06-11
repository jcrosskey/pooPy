#!/usr/bin/python

import argparse
import sys
import os
import re 
## =================================================================
## Given a fasta file, find the sequence for the specific region of 
## a sequence with given ID. 
## Return -1 if the sequence does not exist or its sequence does not
## include the specified region.
## =================================================================
def get_contig(fastaFile, seqID, start, end):
    ''' Given a fasta file, find the sequence for the specific region of 
        a sequence with given ID. 
        Return -1 if the sequence does not exist or its sequence does not
        include the specified region.
        
        Input:  fastaFile - file that includes all the sequences
                seqID - ID of the sequence of interest
                start - 1-based starting position
                end - 1-based ending position
        Output: sequence string if found, -1 if not found
    '''
    if not os.path.exists(fastaFile):
        sys.stderr.write("fastaFile {} does not exist!\n".format(fastaFile))
        return -1
    if end != -1 and start > end:
        sys.stderr.write("Please check input for starting and ending positiosn.\n")
        return -1
        
    seq = ""
    fasta = open(fastaFile,'r') 
    line = fasta.readline()
    sys.stdout.write('>{}\n'.format(seqID))
    while line != "":
        if line[0] == '>':
            thisID = line.strip().split()[0][1:] # sequence ID until the first space
            if thisID == seqID:
                nextline = fasta.readline().strip("\n")
                while nextline!='' and nextline[0] != '>' and (len(seq)<=end or end==-1):
                    seq += nextline
                    nextline = fasta.readline().strip("\n")
                if end == -1 or (start <= end and end <= len(seq)):
                    sys.stdout.write('{}\n'.format(seq[(start - 1):end]))
                else:
                    sys.stderr.write("end position passed end of the sequence!\n")
                    sys.stdout.write('{}\n'.format(seq[(start - 1):-1]))
                    return -1
        line = fasta.readline()
    if seq == "":
        sys.stderr.write("sequence {} was not found in file {}!\n".format(seqID, fastaFile))
        return -1
                    
## =================================================================
## argument parser
## =================================================================
parser = argparse.ArgumentParser(description="fetch sequence from fasta file given an ID and the starting, ending positions",
                                 prog = 'get_contig', #program name
                                 prefix_chars='-', # prefix for options
                                 fromfile_prefix_chars='@', # if options are read from file, '@args.txt'
                                 conflict_handler='resolve', # for handling conflict options
                                 add_help=True, # include help in the options
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter # print default values for options in help message
                                 )

## input files and directories
parser.add_argument("-i","--in",help="input fasta file",dest='fastaFile',required=True)
parser.add_argument("-n","--name",help="ID of the sequence to find",dest='seqID',required=True)
parser.add_argument("-s","--start",help="1-based starting position of the sequence",dest='start',default=1, type=int)
parser.add_argument("-e","--end",help="1-based ending position of the sequence",dest='end',default=-1, type=int)

## output directory
#parser.add_argument("-o","--out",help="output directory",dest='outputDir',required=True)

## =================================================================
## main function
## =================================================================
def main(argv=None):
    
    if argv is None:
        args = parser.parse_args()

    get_contig(args.fastaFile,args.seqID,args.start,args.end)

##==============================================================
## call from command line (instead of interactively)
##==============================================================

if __name__ == '__main__':
    sys.exit(main())
