# Bash completion for Resiris.
_resiris()
{
    local cur prev
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"

    local options="--enable-frontend-visibility --disable-frontend-visibility --help --version"

    if [[ "$cur" == --* ]]; then
        COMPREPLY=( $(compgen -W "$options" -- "$cur") )
        return 0
    fi

    # Complete Resiris source files.
    local files
    files=$(compgen -f -- "$cur")
    COMPREPLY=()
    while IFS= read -r file; do
        [[ "$file" == *.resy ]] && COMPREPLY+=("$file")
    done <<< "$files"
}

complete -F _resiris resiris
