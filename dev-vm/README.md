# Dev VM (KVM + QEMU + Libvirt)
## Host Configuration
Ensure the shared directory exists:
```bash
mkdir -p ~/vm/shared/debian
```

Install required packages:
```bash
# Fedora
sudo dnf group install --with-optional virtualization

# Debian
sudo apt install virt-viewer libvirt-daemon-system virtinst
```

## Creating the VM
The VM can be created with the command below (current configuration for Debian 13). This includes SSD optimizations (TRIM, alignment, writeback cache), 3D acceleration (Virtio-GPU), and improved I/O (CPU passthrough, IO threads).

**Note:** The disk below uses raw for when on BTRFS or ZFS file systems. Use QCOW2 when on EXT.

```bash
virt-install \
  --name debian-dev \
  --vcpus 4 \
  --memory 8192 \
  --cpu host-passthrough \
  --machine q35 \
  --boot uefi \
  --iothreads 1 \
  --disk size=32,format=raw,bus=scsi,discard=unmap,cache=none,io=native,physical_block_size=4096,logical_block_size=512 \
  --controller type=scsi,model=virtio-scsi,driver.iothread=1 \
  --cdrom /var/lib/libvirt/iso/debian-13.iso \
  --os-variant debian13 \
  --filesystem "${HOME}/vm/shared/debian-dev",host_share,driver.type=virtiofs \
  --memorybacking source.type=memfd,access.mode=shared \
  --graphics spice,listen=none,gl.enable=yes,rendernode=/dev/dri/renderD128 \
  --video virtio \
  --sound default \
  --channel unix,target.type=virtio,target.name=org.qemu.guest_agent.0 \
  --channel spicevmc \
  --rng /dev/urandom \
  --network network=default,model=virtio,driver.queues=4 \
  --noautoconsole
```
For QCOW2 disk:
```bash
  --disk size=32,bus=scsi,discard=unmap,cache=writeback,physical_block_size=4096,logical_block_size=512 \
```

## Connecting to the VM
The VM can be connected to using `virt-viewer`:
```bash
virt-viewer --attach debian-dev
```

## VM Configuration
### Packages
Install the following packages for better integration:
```bash
sudo apt update
sudo apt install spice-vdagent qemu-guest-agent
sudo reboot
```

### Shared Directory
Add the mount to `/etc/fstab` to mount on boot:
```bash
sudo mkdir -p /mnt/host
echo "host_share /mnt/host virtiofs defaults,noatime 0 0" | sudo tee -a /etc/fstab
sudo mount -a
```

## VM Management

| Action | Command |
| :--- | :--- |
| **Start** | `virsh start debian-dev` |
| **Connect** | `virt-viewer --attach debian-dev` |
| **Shutdown** | `virsh shutdown debian-dev` |
| **Force Kill** | `virsh destroy debian-dev` |
| **Snapshot** | `virsh snapshot-create-as debian-dev "snapshot-name"` |
| **Delete** | `virsh undefine debian-dev --remove-all-storage` |

SSH after the QEMU guest agent is running using the VM's IP:
```bash
virsh domifaddr debian-dev --source agent
```

## Settings Explained
- `host-passthrough`: Passes the CPU model to the guest for optimal compilation.
- `discard=unmap`: TRIM support for SSDs.
- `cache=writeback`: Uses host RAM to cache disk writes.
- `gl.enable=yes` / `video virtio`: Enables 3D acceleration.
- `virtio-fs`: Shared directories.
