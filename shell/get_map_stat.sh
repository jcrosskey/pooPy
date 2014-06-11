#!/bin/bash

if [ $# -gt 0 ]; then # if command line specifies which sam file to use
	samfile=$1
else # otherwise autodetect
	echo "no sam file specified, autodetection"
	# check how many sam files are in the directory, only do it when there is one sam file
	numfile=$(find . -name "*.sam" -type f | wc -l)
	if [ $numfile -gt 1 ]; then
		echo "$numfile sam files found, specify which one"
		exit 0
	else
		samfile=$(ls *sam)
	fi
fi

echo "sam file is $samfile"
prefix=`basename $samfile .sam`

cat > qsub_samstat << EOF
#!/bin/bash

#PBS -l walltime=300:00:00
#PBS -l nodes=1:ppn=1
#PBS -q large
#PBS -N samStat

cd $PWD

python /chongle/shared/software/pooPy/trunk/src/samStat.py -i $samfile -o$samfile.stat

exit 0;

EOF
qsub qsub_samstat

