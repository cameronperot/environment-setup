#!/usr/bin/env bash
#
# entrypoint.sh — image entrypoint for dev:latest.
#
# Under crun the OCI process.user is already applied and the command is exec'd
# unchanged. Under krun, libkrun's guest init execs the workload as root whatever
# process.user says; crun leaves the OCI config in the guest rootfs as
# /.krun_config.json, so read the intended user from it and drop to it first,
# after closing the TIOCSTI escape that agent-sandbox refuses to run with and
# disabling commit signing, since the host ssh-agent socket cannot cross the VM
# boundary.

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
    # The bind-mounted ssh-agent socket is a dead inode over virtio-fs, so
    # signing cannot work in the guest: turn it off in the user's gitconfig
    home="$(getent passwd "${uid}" | cut -d: -f6)"
    setpriv --reuid="${uid}" --regid="${gid}" "${groups_arg}" -- \
        git config --file "${home}/.gitconfig" commit.gpgsign false
    exec setpriv --reuid="${uid}" --regid="${gid}" "${groups_arg}" -- "$@"
fi

exec "$@"
