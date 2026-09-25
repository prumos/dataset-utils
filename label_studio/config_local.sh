#!/usr/bin/env bash

BASE_DIR="$(pwd)"
HOST_URL=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        -b|--base-dir)
            if [[ -z "${2:-}" ]]; then
                echo "Error: $1 requires a directory argument." >&2
                return 1
            fi
            BASE_DIR="$2"
            shift 2
            ;;
        --host)
            if [[ -z "${2:-}" ]]; then
                echo "Error: $1 requires a hostname argument." >&2
                return 1
            fi
            HOST_URL="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [-b|--base-dir DIR] [--host HOSTNAME]"
            return 0
            ;;
        *)
            echo "Error: unknown option: $1" >&2
            echo "Usage: $0 [-b|--base-dir DIR] [--host HOSTNAME]" >&2
            return 1
            ;;
    esac
done

if [[ ! -d "$BASE_DIR" ]]; then
    echo "\"$BASE_DIR\" is not a directory." >&2
    return 1
fi

if [[ -n "$HOST_URL" && ! "$HOST_URL" =~ ^[hH][tT][tT][pP][sS]?:// ]]; then
    echo "Not a HTTP[S] hostname: \"$HOST_URL\"" >&2
    return 1
fi

BASE_DIR="$(cd "$BASE_DIR" && pwd)"

export LABEL_STUDIO_BASE_DATA_DIR="$BASE_DIR/label_studio/app"
export LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED="true"
export LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT="$BASE_DIR/label_studio/local_store"
export LABEL_STUDIO_PORT="8080"
if [[ -n "$HOST_URL" ]]; then
    export LABEL_STUDIO_HOST="$HOST_URL"
    export CSRF_TRUSTED_ORIGINS="$HOST_URL"
fi

echo "Label Studio environment configured:"
echo "  LABEL_STUDIO_BASE_DATA_DIR=$LABEL_STUDIO_BASE_DATA_DIR"
echo "  LABEL_STUDIO_PORT=$LABEL_STUDIO_PORT"
echo "  LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED=$LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED"
echo "  LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT=$LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT"
if [[ -n "$HOST_URL" ]]; then
    echo "  LABEL_STUDIO_HOST=$HOST_URL" 
    echo "  CSRF_TRUSTED_ORIGINS=$HOST_URL"
fi
