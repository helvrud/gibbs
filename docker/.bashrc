export TIMEFORMAT=$'\nreal %3R\tuser %3U\tsys %3S\tpcpu %P\n'
export HISTFILE=~/.history/history.$HOSTNAME
export HISTCONTROL=ignoreboth
export HISTTIMEFORMAT=$TIMEFORMAT
export HISTIGNORE="&:bg:fg:ll:h"
export HOSTFILE=$HOME/.hosts	# Put a list of remote hosts in ~/.hosts
export PATH="$HOME/bin:$HOME/.local/bin:$PATH"
export PYTHONPATH="/usr/local/lib/python3/dist-packages/:$PYTHONPATH"
export LANG=en_US.UTF-8
#export LC_NUMERIC=en_US.UTF-8
#export LC_NUMERIC=C
#export LC_MESSAGES=POSIX

# the default umask is set in /etc/login.defs
#umask 022 
BROWSER="firefox"
TERMCMD="Terminal --geometry 100x70"
EDITOR="gedit"
export BROWSER EDITOR 

#black='\e[0;30m'	#BLACK='\e[1;30m'
#red='\e[0;31m'		#RED='\e[1;31m'
#green='\e[0;32m'	#GREEN='\e[1;32m'
#yelow='\e[0;33m'	#YELLOW='\e[1;33m'
#blue='\e[0;34m'	#BLUE='\e[1;34m'
#magenta='\e[0;35m'	#MAGENTA='\e[1;35m'
#cyan='\e[0;36m'	#CYAN='\e[1;36m'
#white='\e[0;37m'	#WHITE='\e[1;37m'
#NC='\e[0m'         # No Color

#echo -e "$(color ltyellow)This is $(color ltred)$(whoami)@$(hostname)$(color ltyellow) bash session; now is $(color ltred )$(date +%k:%M:%S)$(color ltyellow) $(date +%d%15B%15A)$(color off)\n"
#echo -e "$(color ltyellow)This is BASH $(color ltred)${BASH_VERSION%.*}$(color ltyellow) - ${DISPLAY} on $(color ltred)$DISPLAY${NC}$(color off)\n$(date)"
#date

PS1='\[\e[1;33m\]\# \u@\h \[\e[1;34m\]\W >>> \[\e[0;32m'; export PS1

 
 
# grep with color
alias grep='/bin/grep -i --color'
alias Grep='/bin/grep --color'
alias slocate='/usr/bin/slocate -i'
alias Slocate='/usr/bin/slocate'
alias locate='/usr/bin/locate -i'
alias Locate='/usr/bin/locate'

alias df='LC_MESSAGES=C df -h'
alias wget='wget -c'

# start an X session screen for a remote host
alias Xremote=remoteX
remoteX () {
  (
  for f in 1 2 3 4 5 6 7 8 9; do
    Xnest :$f -once -name $1 -query $1 2>/dev/null && break
  done
  ) &
}
#-----------------------------------
# File & strings related functions:
#-----------------------------------

# Find a file with a pattern in name:
function ff() { find . -type f -iname '*'$*'*' -ls ; }
# Find a file with pattern $1 in name and Execute $2 on it:
function fe() { find . -type f -iname '*'$1'*' -exec "${2:-file}" {} \;  ; }
# find pattern in a set of filesand highlight them:
function fstr()
{
    OPTIND=1
    local case=""
    local usage="fstr: find string in files.
Usage: fstr [-i] \"pattern\" [\"filename pattern\"] "
    while getopts :it opt
    do
        case "$opt" in
        i) case="-i " ;;
        *) echo "$usage"; return;;
        esac
    done
    shift $(( $OPTIND - 1 ))
    if [ "$#" -lt 1 ]; then
        echo "$usage"
        return;
    fi
    local SMSO=$(tput smso)
    local RMSO=$(tput rmso)
    find . -type f -name "${2:-*}" -print0 | xargs -0 grep -sn ${case} "$1" 2>&- | sed "s/$1/${SMSO}\0${RMSO}/gI" | more
}

function lowercase()  # move filenames to lowercase
{
    for file ; do
        filename=${file##*/}
        case "$filename" in
        */*) dirname==${file%/*} ;;
        *) dirname=.;;
        esac
        nf=$(echo $filename | tr A-Z a-z)
        newname="${dirname}/${nf}"
        if [ "$nf" != "$filename" ]; then
            mv "$file" "$newname"
            echo "lowercase: $file --> $newname"
        else
            echo "lowercase: $file not changed."
        fi
    done
} 

# tailoring 'less'
alias more='less'
export PAGER=less
#export LESSCHARSET='latin1'
export LESSOPEN='|/usr/bin/lesspipe.sh %s 2>&-' # Use this if lesspipe.sh exists
export LESS='-i -z-4 -M -X -F -R -P%t?f%f :stdin .?pb%pb\%:?lbLine %lb:?bbByte %bb:-...'

alias дд='ll'
alias св='cd'

alias ev='evince'
alias i='sudo apt-get install'
alias android-on="mtpfs -o allow_other /media/Android"
alias android-off="fusermount -u /media/Android"

#alias eshelp='ev /home/kvint/espresso/es-build/doc/ug/ug.pdf'
#alias gs='git status '
alias ga='git add '
alias gb='git branch '
alias gc='git commit'
alias gd='git diff'
alias go='git checkout '
alias gk='gitk --all&'
alias gx='gitx --all'

alias got='git '
alias get='git '
alias l='~/bin/l'
alias ll='~/bin/ll'
alias la='~/bin/la'
alias scite='SciTE'
alias vz='veusz'
alias py='python3'
alias ipy='ipython3'
alias lo='libreoffice'
alias gq='geeqie'



alias i='sudo apt-get install '
#alias mail='mail -S from=helvrud@gmail.com'

# added by Miniconda3 4.3.11 installer
#export PATH="/home/kvint/miniconda3/bin:$PATH"

# added by Miniconda2 4.3.11 installer
#export PATH="/home/kvint/.local/miniconda2/bin:$PATH"
alias eshelp="firefox ~/reaction/espresso/es-build/doc/sphinx/html/index.html"

