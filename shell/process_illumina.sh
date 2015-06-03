#!/bin/bash

# pipeline used to process Illumina reads #
# Usage: process_illumina.sh *.fastq #
echo 'Usage: process_illumina.sh *.fastq'

in_reads=$1 # input file as interleaved paired end reads in fastq format
work_dir=`pwd`
prefix=`basename $1`
prefix=${prefix%%\.*}
mkdir $prefix
cd $prefix
#==================================
# trimming
#==================================
cat > trim.sh <<TrimmingScriptWriting
#!/bin/bash

#PBS -N trim_${prefix}
#PBS -q medium
#PBS -l nodes=1:ppn=1
#PBS -l walltime=24:00:00
#PBS -d ${work_dir}/${prefix}
#PBS -j oe
#PBS -o trim.out
sickle pe -c ../${in_reads} -t sanger -m ${prefix}_pe.fastq -s ${prefix}_se.fastq -l 60 -q 20 -n
qsub ec.sh
TrimmingScriptWriting
chmod u+x trim.sh

#==================================
# error correction
#==================================
cat > ec.sh <<ErrorCorrectionScriptWriting
#!/bin/bash

#PBS -N ec_${prefix}
#PBS -q medium
#PBS -l nodes=1:ppn=48
#PBS -l walltime=24:00:00
#PBS -d ${work_dir}/${prefix}
#PBS -j oe
#PBS -o ec.out

bash /home/cjg/Software/BBTools/ecc.sh threads=48 ecclimit=7 ecr=140 eclt=3 echt=16  in=${prefix}_pe.fastq extra=${prefix}_se.fastq out=${prefix}_pe_trimmed_corrected_\#.fastq > ${prefix}_pe_trimmed_correct.log
bash /home/cjg/Software/BBTools/ecc.sh threads=48 ecclimit=7 ecr=140 eclt=3 echt=16  in=${prefix}_se.fastq extra=${prefix}_pe.fastq out=${prefix}_se_trimmed_corrected.fastq  > ${prefix}_se_trimmed_correct.log 
qsub merge.sh
ErrorCorrectionScriptWriting
chmod u+x ec.sh

#==================================
# merge
#==================================
cat > merge.sh <<MergePariedEndReadsScriptWriting
#!/bin/bash

#PBS -N merge_${prefix}
#PBS -q medium
#PBS -l nodes=1:ppn=16
#PBS -l walltime=24:00:00
#PBS -d ${work_dir}/${prefix}
#PBS -j oe
#PBS -o merge.out

# -m min-overlap (default 10)
# -M max-overlap  = 2.5 * fragment-len-stddev + overlap
# -r read-len
# -f fragment-len
# -s fragment-len-stddev
flash -r 251 -f 400 -s 40 -o ${prefix}_flash_merge -d $PWD --interleaved-output -t 16 ${prefix}_pe_trimmed_corrected_1.fastq ${prefix}_pe_trimmed_corrected_2.fastq 

#qsub dup_con.sh
MergePariedEndReadsScriptWriting
chmod u+x merge.sh

merged_fastq=flash_merge.extendedFrags.fastq
#==================================
# remove duplicated and contained reads
#==================================
cat > dup_con.sh <<DeduplicationScriptWriting
#!/bin/bash

#PBS -N dup_con_${prefix}
#PBS -q medium
#PBS -l nodes=1:ppn=40
#PBS -l walltime=24:00:00
#PBS -d ${work_dir}/${prefix}
#PBS -j oe
#PBS -o dup_con.out

/chongle/qiuming/align_test/Release/align_test -i RemoveContainedReads --subject ${merged_fastq} --query ${merged_fastq} -ht omega -l 40 -t 40 --ID 0 --out ${prefix}_unique.fasta
DeduplicationScriptWriting
chmod u+x dup_con.sh

#qsub trim.sh
