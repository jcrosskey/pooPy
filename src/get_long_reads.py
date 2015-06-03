#!/usr/bin/python

import argparse
import sys
import os
import re 
## =================================================================
## Function: getRead
## =================================================================
def getReadFromFasta(fin):
    output = ""
    for line in fin:
        if line.strip("\n").strip() != "":
            if line[0] != ">":
                output += line
            else:
                if output != "":
                    yield output
                output = line
    yield output

def getReadFromFastq(fin):
    output = ""
    count = 0
    for line in fin:
        if count != 4:
            output += line
            count = count + 1
        else:
            yield output
            output = line
            count = 1
    yield output

## =================================================================
## Find length of all sequences in a fasta file
## =================================================================
def get_long_reads(inputFile,outFile=None,cutoff=1000):
    ''' Extract sequences longer than the specified cutoff from inputFile
        Input:  inputFile - file including all the sequences to investigate
                outFile - output file with long sequences
                cutoff - length cutoff
        Output: outFile
    '''
    fileExt = inputFile.split(".")[-1] # file type, fasta or fastq, autodetect
    if fileExt in ["fa", "Fa", "fasta", "Fasta"]:  # either fa or fq
        fileType = "fasta" 
    elif fileExt in ["fq", "Fq", "fastq", "Fastq"]:  # either fa or fq
        fileType = "fastq" 
    else:
        sys.stderr.write("File type is not correct...\n") 

    if not os.path.exists(inputFile):
        sys.stderr.write("input File {} does not exist!\n".format(inputFile))
        return -1
    if outFile is None:
        outFile = os.getcwd()  + '/long_sequences.fasta'
    outDir = os.path.dirname(os.path.abspath(outFile))
    if not os.path.exists(outDir):
        os.makedirs(outDir)
        
    fout = open(outFile, 'w')
    readCount = 0
    with open(inputFile,'r') as fin:
        if fileType == "fastq":
            for readLines in getReadFromFastq(fin):
                seq_len = len(readLines.split("\n"[1]))
                if seq_len >= cutoff:
                    fout.write(readLines)
                    readCount += 1
        elif fileType == "fasta":
            for readLines in getReadFromFasta(fin):
                seq_len = sum(map(len, readLines.split("\n")[1:]))
                if seq_len >= cutoff:
                    fout.write(readLines)
                    readCount += 1
    fout.close()
    sys.stderr.write("Total number of sequences longer than {} is {}\n".format(cutoff, readCount))
                    
## =================================================================
## argument parser
## =================================================================
parser = argparse.ArgumentParser(description="Extract sequences longer than the specified cutoff from sequence File",
                                 prog = 'get_long_reads', #program name
                                 prefix_chars='-', # prefix for options
                                 fromfile_prefix_chars='@', # if options are read from file, '@args.txt'
                                 conflict_handler='resolve', # for handling conflict options
                                 add_help=True, # include help in the options
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter # print default values for options in help message
                                 )

## input files and directories
parser.add_argument("-i","--in",help="input file",dest='inputFile',required=True)
parser.add_argument("-c","--cutoff",help="length cutoff",dest='cutoff',default=1000, type=int)

## output directory
parser.add_argument("-o","--out",help="output file",dest='outFile',default=None)

## =================================================================
## main function
## =================================================================
def main(argv=None):
    if argv is None:
        args = parser.parse_args()

    get_long_reads(args.inputFile, args.outFile, args.cutoff)
##==============================================================
## call from command line (instead of interactively)
##==============================================================

if __name__ == '__main__':
    sys.exit(main())
