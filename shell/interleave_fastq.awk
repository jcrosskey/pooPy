BEGIN{
	RS="\n@";
	OFS="\t";
	FS="\n";
	ORS="\n";
}
{
	if(FNR==NR){
		a[FNR] = $0;
		next;
	}
	else{
		if(FNR==1){
			print $0
			print a[FNR]
		}
		else{
			if(NR == 2*FNR){
				print "@"$0"@"a[FNR]
			}
			else{
				print "@"$0
				print "@"a[FNR]
			}
		}
	}
}
