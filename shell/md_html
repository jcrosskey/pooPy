#!/bin/bash
filename=$1
filebase="${filename%\.md}"
html_file="${filebase}.html"
pandoc --mathjax -s $filename -o $html_file
