#!/bin/bash

echo "getSamFromBam bamFile bigFasta pacbioName"
bamFile=$1 # bam file name
pFasta=$2
pName=$3 # pacbio read name
pfilename=${pName//\//__}

echo first generate fasta file
python ../src/get_contig.py -i $pFasta -n $pName -l 1 > ${pfilename}.fasta

echo second generate bam file
samtools view -o ${pfilename}.bam -b $bamFile $pName
samtools index ${pfilename}.bam
