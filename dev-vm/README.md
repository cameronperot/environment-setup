# Dev VM (KVM + QEMU + libvirt)

Debian 13 guest with CPU passthrough, virtio-blk with an I/O thread, and a virtiofs shared directory. Runs headless over a serial console, or with an optional SPICE display and Virtio-GPU 3D acceleration.

## 1. Host Setup

Install the virtualization stack:

```bash
# Fedora
sudo dnf group install --with-optional virtualization

# Debian
sudo apt install virt-viewer libvirt-daemon-system virtinst
```

Create the shared directory:

```bash
mkdir -p ~/vm/shared/debian-dev
```

### btrfs: disable CoW on the image directory

qcow2 is itself copy-on-write. Storing it on a CoW filesystem nests two CoW layers, which fragments the image and degrades I/O. Mark the libvirt image directory NOCOW **before** creating the disk:

```bash
sudo chattr +C /var/lib/libvirt/images
lsattr -d /var/lib/libvirt/images   # expect a 'C' in the attribute list
```

- The attribute only applies to files created after it is set. New images inherit it from the directory.
- To fix an existing image: shut down the VM, `mv` the file aside, `cp` it back into the NOCOW directory, then delete the original. `cp --reflink=never` guarantees a full copy.
- NOCOW files are excluded from btrfs checksumming and compression. qcow2 has its own integrity metadata, so this is an acceptable trade.
- ZFS: NOCOW is not available. Set `recordsize=64K` on the dataset instead to match the qcow2 cluster size. ZFS older than 2.3 does not support O_DIRECT, so use `cache=writeback` in place of `cache=none`.

## 2. Create the VM

Common flags. The command is incomplete on its own; append one of the console variants below.

```bash
virt-install \
  --name debian-dev \
  --vcpus 4 \
  --memory 8192 \
  --cpu host-passthrough \
  --machine q35 \
  --boot uefi \
  --iothreads 1 \
  --disk size=64,format=qcow2,bus=virtio,discard=unmap,cache=none,io=native,driver.iothread=1 \
  --osinfo detect=on,name=debian13 \
  --filesystem "${HOME}/vm/shared/debian-dev",host_share,driver.type=virtiofs \
  --memorybacking source.type=memfd,access.mode=shared \
  --channel unix,target.type=virtio,target.name=org.qemu.guest_agent.0 \
  --rng /dev/urandom \
  --network network=default,model=virtio,driver.queues=4 \
  --noautoconsole \
```

### Headless (serial console)

`--location` extracts the kernel and initrd from the ISO so `--extra-args` can redirect the installer to the serial port. The installer carries `console=ttyS0` into the installed GRUB config, so the serial console keeps working after reboot.

```bash
  --location /var/lib/libvirt/iso/debian-13.iso \
  --extra-args "console=ttyS0,115200n8" \
  --graphics none \
  --console pty,target.type=serial
```

Attach to the installer (exit with `Ctrl+]`):

```bash
virsh console debian-dev
```

### Graphical (SPICE + 3D)

Confirm the render node belongs to the GPU driving the display, then substitute it in `rendernode=`:

```bash
ls -l /dev/dri/by-path/
```

```bash
  --cdrom /var/lib/libvirt/iso/debian-13.iso \
  --graphics spice,listen=none,gl.enable=yes,rendernode=/dev/dri/renderD128 \
  --video virtio \
  --sound default \
  --channel spicevmc
```

Open the installer console:

```bash
virt-viewer --attach debian-dev
```

## 3. Guest Setup

Install the guest agent (IP reporting, graceful shutdown). Add `spice-vdagent` on graphical VMs for clipboard sharing and dynamic resolution:

```bash
sudo apt update
sudo apt install qemu-guest-agent # headless
sudo apt install qemu-guest-agent spice-vdagent # graphical
sudo reboot
```

Mount the shared directory on boot:

```bash
sudo mkdir -p /mnt/host
echo "host_share /mnt/host virtiofs defaults,noatime,nofail 0 0" | sudo tee -a /etc/fstab
sudo mount -a
```

`nofail` lets the guest boot when the share is absent, e.g. after moving the image to another host.

`discard=unmap` only shrinks the image when the guest issues TRIM. Debian's `fstrim.timer` does this weekly. To trim immediately:

```bash
sudo fstrim -av
```

## 4. Daily Use

| Action | Command |
| :--- | :--- |
| Start | `virsh start debian-dev` |
| Console (headless) | `virsh console debian-dev` |
| Console (graphical) | `virt-viewer --attach debian-dev` |
| Get IP (needs guest agent) | `virsh domifaddr debian-dev --source agent` |
| Shutdown | `virsh shutdown debian-dev` |
| Force kill | `virsh destroy debian-dev` |
| Start with host | `virsh autostart debian-dev` |
| Snapshot | `virsh snapshot-create-as debian-dev "snapshot-name"` |
| Delete VM and disk | `virsh undefine debian-dev --nvram --remove-all-storage` |

Internal snapshots are rejected on UEFI VMs with raw NVRAM on most libvirt versions. If the snapshot command errors, take an external disk-only snapshot instead:

```bash
virsh snapshot-create-as debian-dev "snapshot-name" --disk-only --atomic
```

## Reference: Key Options

| Option | Purpose |
| :--- | :--- |
| `--osinfo detect=on,name=debian13` | Detects the OS from the install media, falling back to the name if the host osinfo-db is older. |
| `--cpu host-passthrough` | Exposes the host CPU model and flags to the guest. |
| `format=qcow2` | Thin-provisioned disk with snapshot support. Pair with NOCOW on btrfs. |
| `discard=unmap` | Passes TRIM through so freed guest blocks shrink the image. |
| `cache=none,io=native` | Bypasses the host page cache and uses Linux AIO. |
| `bus=virtio` | virtio-blk. Lower overhead than virtio-scsi for a single disk. |
| `driver.iothread=1` | Dedicated I/O thread for the disk. |
| `--graphics none` + `--console pty` | Headless: serial console only, no display device. |
| `gl.enable=yes` + `--video virtio` | Graphical: Virtio-GPU 3D acceleration over SPICE. |
| `driver.type=virtiofs` | Low-overhead shared directory. Requires `memfd` shared memory backing. |
| `driver.queues=4` | Multi-queue virtio-net, one queue per vCPU. |
