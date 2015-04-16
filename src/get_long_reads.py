#!/usr/bin/python

import argparse
import sys
import os
import re 
## =================================================================
## Find length of all sequences in a fasta file
## =================================================================
def get_long_reads(fastaFile,outFile=None,cutoff=1000):
    ''' Extract sequences longer than the specified cutoff from fastaFile
        Input:  fastaFile - file including all the sequences to investigate
                outFile - output file with long sequences
                cutoff - length cutoff
        Output: outFile
    '''
    if not os.path.exists(fastaFile):
        sys.stderr.write("fastaFile {} does not exist!\n".format(fastaFile))
        return -1
    if outFile is None:
        outFile = os.getcwd()  + '/long_sequences.fasta'
    outDir = os.path.dirname(os.path.abspath(outFile))
    if not os.path.exists(outDir):
        os.makedirs(outDir)
        
    fasta = open(fastaFile,'r') 
    myout = open(outFile,'w')
    seqLen = 0 # initialize to 0
    seq = ''
    seqID = ''
    seqNum = 0
    with open(fastaFile,'r') as fasta:
        for line in fasta:
            if line[0] == '>':
                if seqLen >= cutoff:
                    seqNum += 1
                    myout.write(">{}\n{}\n".format(seqID, seq))
                # reset sequence length, and sequence bases
                seqLen = 0
                seqID = line.strip()[1:]
                seq = ''
            else:
                seq += line.strip("\n")
                seqLen += len(line.strip('\n'))
    if seqLen >= cutoff:
        seqNum += 1
        myout.write("{}\n{}".format(seqID, seq))

    myout.close()
    sys.stdout.write("Total number of sequences longer than {} is {}\n".format(cutoff, seqNum))
                    
## =================================================================
## argument parser
## =================================================================
parser = argparse.ArgumentParser(description="Extract sequences longer than the specified cutoff from fastaFile",
                                 prog = 'get_long_reads', #program name
                                 prefix_chars='-', # prefix for options
                                 fromfile_prefix_chars='@', # if options are read from file, '@args.txt'
                                 conflict_handler='resolve', # for handling conflict options
                                 add_help=True, # include help in the options
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter # print default values for options in help message
                                 )

## input files and directories
parser.add_argument("-i","--in",help="input fasta file",dest='fastaFile',required=True)
parser.add_argument("-c","--cutoff",help="length cutoff",dest='cutoff',default=1000, type=int)

## output directory
parser.add_argument("-o","--out",help="output fasta file",dest='outFile',default=None)

## =================================================================
## main function
## =================================================================
def main(argv=None):
    if argv is None:
        args = parser.parse_args()

    get_long_reads(args.fastaFile, args.outFile, args.cutoff)
##==============================================================
## call from command line (instead of interactively)
##==============================================================

if __name__ == '__main__':
    sys.exit(main())
