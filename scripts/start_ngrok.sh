#!/usr/bin/env bash
set -euo pipefail

# Configurable port (change if your app uses another one)
PORT="${1:-4000}"

echo "Starting ngrok tunnel to http://127.0.0.1:$PORT … (Ctrl+C to stop)"

# Run ngrok and capture its output line by line
ngrok http "http://127.0.0.1:$PORT/" --log=stdout | while IFS= read -r line; do
    echo "$line"

    # Look for the public ngrok URL
    if [[ $line =~ https://[a-z0-9-]+\.ngrok(-free)?\.(io|app|com) ]]; then
        URL="${BASH_REMATCH[0]}"

        # Copy to clipboard depending on OS
        if command -v pbcopy >/dev/null 2>&1; then
            # macOS
            printf '%s' "$URL" | pbcopy
        elif command -v xclip >/dev/null 2>&1; then
            # Linux with xclip
            printf '%s' "$URL" | xclip -selection clipboard
        elif command -v clip.exe >/dev/null 2>&1; then
            # Windows / WSL
            printf '%s' "$URL" | clip.exe
        else
            echo "Warning: No clipboard tool found (install pbcopy/xclip/clip)"
        fi

        echo ""
        echo "Public URL copied to clipboard: $URL"
        echo ""
    fi
done

# Graceful shutdown on Ctrl+C
trap 'echo -e "\nShutting down ngrok…"; kill $! 2>/dev/null || true' INT TERM

wait