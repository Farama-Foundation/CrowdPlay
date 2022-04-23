# /bin/bash
ls | grep .gz | parallel "[ ! -e {.} ] && gzcat {} > {.}"
ls | grep .bz2 | parallel "[ ! -e {.} ] && bzcat {} > {.}"