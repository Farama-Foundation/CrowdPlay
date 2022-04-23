# /bin/bash
ls | grep .bz2 | parallel "[ ! -e {.}.gz ] && bzcat {} | gzip -1 -c > {.}.gz"