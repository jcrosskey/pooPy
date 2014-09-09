#!/usr/bin/python

import argparse
import sys
import os
import re 
## =================================================================
## Find length of all sequences in a fasta file
## =================================================================
def count_bps(fastaFile,countFile,trim_string=None):
    ''' Find length of all sequences in a fasta file

        Input:  fastaFile - file that includes filtered subreads
        Output: countFile - file that contains the number of bases in each sequence
    '''
    if not os.path.exists(fastaFile):
        sys.stderr.write("fastaFile {} does not exist!\n".format(fastaFile))
        return -1
        
    fasta = open(fastaFile,'r') 
    mycount = open(countFile,'w')
    seqID = ''
    seqLen = 0
    with open(fastaFile,'r') as fasta:
        for line in fasta:
            if line[0] == '>':
                if seqLen != 0:
                    mycount.write("{}\t{}\n".format(seqID, seqLen))
                    seqLen = 0
                seqID = line.strip()[1:]
                if trim_string is not None:
                    seqID = seqID.split(trim_string)[0]
            else:
                seqLen += len(line.strip('\n'))
    # write the length of the last sequence
    mycount.write("{}\t{}".format(seqID, seqLen))
    mycount.close()
                    
## =================================================================
## argument parser
## =================================================================
parser = argparse.ArgumentParser(description="count number of bps for each sequence in fasta file",
                                 prog = 'count_bps', #program name
                                 prefix_chars='-', # prefix for options
                                 fromfile_prefix_chars='@', # if options are read from file, '@args.txt'
                                 conflict_handler='resolve', # for handling conflict options
                                 add_help=True, # include help in the options
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter # print default values for options in help message
                                 )

## input files and directories
parser.add_argument("-i","--in",help="input fasta file",dest='fastaFile',required=True)
parser.add_argument("-t","--trim",help="string/character where the read name is trimmed",dest='trim_string',default=None)

## output directory
parser.add_argument("-o","--out",help="output directory",dest='countFile',required=True)

## =================================================================
## main function
## =================================================================
def main(argv=None):
    if argv is None:
        args = parser.parse_args()

    count_bps(args.fastaFile, args.countFile, args.trim_string)
##==============================================================
## call from command line (instead of interactively)
##==============================================================

if __name__ == '__main__':
    sys.exit(main())
