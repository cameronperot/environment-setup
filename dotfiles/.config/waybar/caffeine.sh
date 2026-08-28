#!/usr/bin/env bash
# Toggle "caffeine" mode: hold a logind inhibitor against idle/sleep.
# Called by waybar: `caffeine.sh status` (JSON for the module) or `caffeine.sh toggle`.

PIDFILE="${XDG_RUNTIME_DIR:-/tmp}/waybar-caffeine.pid"

is_active() {
    [[ -f $PIDFILE ]] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null
}

case "$1" in
toggle)
    if is_active; then
        # negative PID: kill the whole process group (systemd-inhibit + sleep)
        kill -- -"$(cat "$PIDFILE")" 2>/dev/null
        rm -f "$PIDFILE"
    else
        setsid systemd-inhibit --what=idle:sleep sleep infinity >/dev/null 2>&1 &
        echo $! >"$PIDFILE"
    fi
    pkill -RTMIN+8 waybar
    ;;
*)
    if is_active; then
        echo '{"text": " ● ", "class": "good", "tooltip": "Caffeine: idle/sleep inhibited — click to disable"}'
    else
        echo '{"text": " ○ ", "class": "", "tooltip": "Caffeine: off — click to inhibit idle/sleep"}'
    fi
    ;;
esac
