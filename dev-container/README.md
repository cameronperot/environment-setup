# Dev Container
This dev container is designed for LLM-assisted coding to restrict the data and information the agent has access to and reduce the chance of harmful changes to the host system.

Note: Containers are not a security measure. If you need security isolation then consider using a VM.

## Building
The Containerfile copies the repository root into the image, so the build context is the
repository root (the parent of this directory). Run the provided script from anywhere:
```bash
./dev-container/build.sh
```
`build.sh` passes the invoking user's UID/GID as build args, so the image's dev user (`user`, homed at `/home/user`) is created with the builder's numeric identity. Containers run with `--userns keep-id`, which maps the host user's UID to the same UID inside the container, so the image must be rebuilt by whoever uses it — or after a host UID change — for home ownership and bind mounts to resolve correctly.

`make container-build` delegates to the same script.

## Usage
`c` (from `dotfiles/bin`, deployed to `~/bin` by `install.py`) runs a command in the running
container whose bind mount best matches the current directory, or with `-n` in a throwaway container from `dev:latest`:
```bash
c some_executable       # exec into the running container (compose-dev.yml)
c -n some_executable    # new throwaway container
```
With `-n` the repository root is mounted at its host path and the current directory is the working directory, so git worktrees of `.bare` repos work inside: the directory containing `.bare` is what gets mounted, and every worktree registered there resolves. Outside git the current directory itself is mounted. The agent dotfiles under `$AGENT_CONFIG_DIR`, the ssh-agent socket and the API-key variables are passed through. `~/bin` is on `PATH` in the image, so `agent-sandbox`, `c` and `git-bareify` are reachable from any entry point, e.g. `c -n agent-sandbox pi`.

`pi`, `omp` and `opencode` are shadowed in `~/bin` (symlinks to `agent-shadow`, which execs the sibling `agent-sandbox` with the invoked name), so from the rebuilt image every entry point — `podman exec` (i.e. `c pi`), interactive zsh, plain bash — launches them inside the sandbox. To exec an agent unsandboxed for a single invocation, set `AGENT_SANDBOX_DISABLE=1` (e.g. `c env AGENT_SANDBOX_DISABLE=1 pi ...`); invoking an agent by absolute path bypasses the shadow entirely.

A compose file running Jupyter lab is also provided for a longer running environment:
```bash
podman-compose -f compose.yml up
```
`compose-dev.yml` additionally mounts the signing-agent socket from the host runtime directory, which depends on the host UID; it reads `HOST_UID` from the environment (defaulting to 1000):
```bash
HOST_UID=$(id -u) podman-compose -f compose-dev.yml up
```

## LLM-Agent Commit Signing
### 1. Generate the Isolated Key (Host)
```zsh
ssh-keygen -t ed25519 -f ~/.ssh/llm_agent_ed25519 -C "llm-agent" -N ""
```

---

### 2. Add to GitHub (Host)
1. Copy the public key:
   ```zsh
   cat ~/.ssh/llm_agent_ed25519.pub
   ```
2. Go to **GitHub → Settings → SSH and GPG keys → New SSH Key**.
3. Set **Key type** to **Signing Key** and paste the key.

---

### 3. Create the Systemd User Service (Host)
Create `~/.config/systemd/user/llm-ssh-agent.service`:

```ini
[Unit]
Description=Isolated SSH Agent for LLM Coding Agent
After=network.target

[Service]
Type=simple
Environment=SSH_AUTH_SOCK=%t/llm-agent.sock
ExecStartPre=/usr/bin/rm -f %t/llm-agent.sock
ExecStart=/usr/bin/ssh-agent -D -a %t/llm-agent.sock
ExecStartPost=/usr/bin/sh -c 'for i in $(seq 1 50); do [ -S "$SSH_AUTH_SOCK" ] && break; sleep 0.05; done; ssh-add %h/.ssh/llm_agent_ed25519'
Restart=on-failure

[Install]
WantedBy=default.target
```

Enable and start the service:
```zsh
systemctl --user daemon-reload
systemctl --user enable --now llm-ssh-agent.service
```

---

### 4. Run the Container

Pass these args when running the container:
```zsh
-v "/run/user/$(id -u)/llm-agent.sock:/run/ssh-agent.sock:z" \
-e SSH_AUTH_SOCK=/run/ssh-agent.sock \
```
---

### 5. Configure Git & Local Verification (Inside Container)

Run these inside the container to set up signing and local signature verification:

```bash
# 1. Configure SSH signing via the mounted socket
git config --global gpg.format ssh
git config --global commit.gpgsign true
git config --global user.signingkey "$(ssh-add -L)"

# 2. Configure local signature verification (allowed_signers)
mkdir -p ~/.ssh
echo "$(git config user.email) $(git config user.signingkey -L)" > ~/.ssh/allowed_signers
git config --global gpg.ssh.allowedSignersFile ~/.ssh/allowed_signers
```

---

### 6. Verify

Create a signed commit and check the signature:
```bash
git commit --allow-empty -m "test: verify signature"
git log --show-signature -1
```

**Expected output:**
```text
Good "git" signature for your-github-verified-email@example.com with ED25519 key SHA256:...
```
