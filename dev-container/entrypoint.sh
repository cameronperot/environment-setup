#!/usr/bin/env bash
#
# entrypoint.sh — image entrypoint for dev:latest.
#
# Under crun the OCI process.user is already applied and the command is exec'd
# unchanged. Under krun, libkrun's guest init execs the workload as root whatever
# process.user says; crun leaves the OCI config in the guest rootfs as
# /.krun_config.json, so read the intended user from it and drop to it first,
# after closing the TIOCSTI escape that agent-sandbox refuses to run with and
# bridging the TCP signer, since virtio-fs cannot pass the host ssh-agent
# socket through.

set -euo pipefail

if [[ -e /.krun_config.json && "$(id -u)" -eq 0 ]]; then
    # libkrunfw's guest kernel ships CONFIG_LEGACY_TIOCSTI=y
    echo 0 >/proc/sys/dev/tty/legacy_tiocsti
    user="$(jq -r '.process.user | "\(.uid) \(.gid) \((.additionalGids // []) | map(tostring) | join(","))"' /.krun_config.json)" || {
        echo "entrypoint: cannot read process.user from /.krun_config.json" >&2
        exit 1
    }
    read -r uid gid groups <<<"${user}"
    groups_arg="--clear-groups"
    [[ -n "${groups}" ]] && groups_arg="--groups=${groups}"
    # virtio-fs passes files but not Unix-socket endpoints, so the signer is
    # reached over TCP: `c -k` has pasta forward guest connections on port 7777
    # to the host's loopback (see dev-container/README.md). Bridge it to the
    # socket path SSH_AUTH_SOCK expects; /run rejects the bind in the guest,
    # hence /tmp.
    socat UNIX-LISTEN:/tmp/ssh-agent.sock,fork,mode=0666 TCP:127.0.0.1:7777 &
    exec setpriv --reuid="${uid}" --regid="${gid}" "${groups_arg}" -- "$@"
fi

exec "$@"
