# Dev Container
This dev container is designed for LLM-assisted coding to restrict the data and information the agent has access to and reduce the chance of harmful changes to the host system.

Note: Containers are not a security measure. If you need security isolation then consider using a VM.

## Building
The Containerfile copies the repository root into the image, so the build context is the
repository root (the parent of this directory). Run the provided script from anywhere:
```bash
./dev-container/build.sh
```

## Usage
This is best used with the following alias that will run a container and mount the current working directory to `/work`:
```bash
alias c='podman run \
  -it \
  --rm \
  --userns keep-id \
  --security-opt label=disable \
  -v dev-antidote:/home/user/.antidote \
  -v ${PWD}:/work \
  dev:latest'
```
The alias can be used to run `some_executable` in the current working directory with:
```bash
c some_executable
```

A compose file running Jupyter lab is also provided for a longer running environment:
```bash
podman-compose -f compose.yml up
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
