# Installation Log: Frappe VM Setup

> **Purpose**: Record of the actual VM setup process, with screenshots, the values each step produced and the problems hit along the way.
> The commands are in [SETUP.md](SETUP.md), which describes the *reference* procedure. Each step below links to the SETUP.md step it followed.

**Date started**: 2026-09-27
**Host machine**: Windows, 32 GB RAM
**VirtualBox version**: 7.2.18 r175117 (Qt6.8.0)
**Frappe version installed**: `develop` @ `407b551` (2026-09-27), `17.0.0-dev` (`bench list-apps` shows it as `17.x.x-develop`)

---

## Step 1: Host Prerequisites

Checklist: [SETUP.md step 1](SETUP.md#1-host-prerequisites-windows).

| Check | Result | Notes |
|---|---|---|
| VirtualBox version | ✅ 7.2.18 | Already upgraded, meets 7.x requirement |
| Host RAM | ✅ 32 GB | Well above 16 GB recommendation |
| Hardware virtualisation (VT-x/AMD-V) | ✅ Enabled | AMD Ryzen AI 9 HX 370, so **AMD-V** (VT-x is the Intel name). `Win32_Processor.VirtualizationFirmwareEnabled = True`. GUI: Task Manager → Performance → CPU → *Virtualization: Enabled* |
| Hyper-V | ✅ Not installed | `Get-WindowsOptionalFeature` (needs admin, but not manually enabled). The Windows hypervisor still runs because of VBS (next rows) |
| WSL2 | ✅ Not installed | `wsl --status` → "not installed" |
| Core Isolation (Memory Integrity) | ⚠️ **On** | `Win32_DeviceGuard`: `VirtualizationBasedSecurityStatus = 2` (VBS running), `SecurityServicesRunning = {2,3,4}` (2 = Memory Integrity / HVCI, 3 = System Guard Secure Launch, 4 = SMM Firmware Measurement). Registry `…\DeviceGuard\Scenarios\HypervisorEnforcedCodeIntegrity\Enabled = 1`. GUI: Windows Security → Device security → Core isolation details |
| VirtualBox execution engine | ⚠️ Windows Hypervisor Platform (NEM) | `VBox.log`: `HM: HMR3Init: Attempting fall back to NEM: AMD-V is not available`. Because VBS owns AMD-V, VirtualBox runs on top of the Windows hypervisor (green turtle icon), which is slower than native AMD-V |
| Ubuntu Server 24.04 LTS ISO | ✅ Downloaded | `ubuntu-24.04.5-live-server-amd64.iso` |

Memory Integrity was left on. Everything still works (the install completed and the 23 tests run in ~2.5 s), so turning it off is optional.

---

## Step 2: Create the VM

Settings: [SETUP.md step 2](SETUP.md#2-create-the-vm).

- [x] All VM settings as listed there (`frappe-dev-ub24`, 8192 MB, 4 CPUs, 40 GB, unattended installation unticked)
- [x] The three NAT port-forwarding rules (ssh 2222 → 22, frappe-web 8000 → 8000, frappe-socketio 9000 → 9000), all on host IP `127.0.0.1`

![VM creation — OS and ISO settings](screenshots/image1.png)

![VM creation — Hardware settings (8192 MB RAM, 4 CPUs)](screenshots/image2.png)

![Network settings and Port Forwarding rules](screenshots/image3.png)

**Issues encountered:**

1. ❌ First attempt used Ubuntu 26.04 ISO instead of 24.04 LTS
2. ❌ "Proceed with Unattended Installation" was checked — should be unchecked
3. ❌ VM started before Port Forwarding was configured
4. ❌ Unattended install failed with errors in console
5. 🔧 **Resolution**: Power off VM → Delete all files → Recreate with correct ISO and settings

**Boot:**

![GRUB boot menu — select "Try or Install Ubuntu Server"](screenshots/image4.png)

---

## Step 3: Install Ubuntu Server

Installer choices: [SETUP.md step 3](SETUP.md#3-install-ubuntu-server). Values on this VM:

- [x] Keyboard: English (US)
- [x] Network: DHCP on `enp0s3` → `10.0.2.15/24`
- [x] Storage: Use entire disk (LVM unticked) → 39.07 GB ext4 on `/`
- [x] Profile: Your name `suyu`, server name `frappe-dev`, username `frappe`
- [x] Reboot completed successfully

**Ubuntu version installed**: 24.04.5 LTS (GNU/Linux 6.8.0-142-generic x86_64)

**SSH access verified from Windows:**

```
PS> ssh -p 2222 frappe@127.0.0.1
Welcome to Ubuntu 24.04.5 LTS (GNU/Linux 6.8.0-142-generic x86_64)
frappe@frappe-dev:~$
```

---

## Step 4: System Packages

Commands: [SETUP.md step 4](SETUP.md#4-system-packages).

- [x] System updated
- [x] Timezone set to America/Toronto
- [x] Packages installed

---

## Step 5: MariaDB Root Password

Commands: [SETUP.md step 5](SETUP.md#5-mariadb-root-password).

- [x] Root password set
- [x] Verified: `mariadb -h 127.0.0.1 -u root -p -e "select version();"` → **10.11.14-MariaDB**

---

## Step 6: Node.js 24 and Yarn (via nvm)

Commands: [SETUP.md step 6](SETUP.md#6-nodejs-24-and-yarn-via-nvm).

- [x] nvm installed (v0.40.3)
- [x] Node.js 24.x installed — actual version: **v24.21.0**
- [x] Yarn installed — actual version: **1.22.22**

---

## Step 7: Python 3.14 (via uv) and bench CLI

Commands: [SETUP.md step 7](SETUP.md#7-python-314-via-uv-and-the-bench-cli).

- [x] uv installed — version: **0.12.19**
- [x] Python 3.14 installed — actual version: **3.14.7** (`/home/frappe/.local/share/uv/python/cpython-3.14-linux-x86_64-gnu/bin/python3.14`)
- [x] bench CLI installed — actual version: **5.31.0**

---

## Step 8: Create the bench (develop branch)

Commands: [SETUP.md step 8](SETUP.md#8-create-the-bench-on-develop).

- [x] bench init completed
- [x] Expected warning: "Cannot connect to redis_cache" (OK at this stage)

---

## Step 9: Create Site + Developer Mode

Commands: [SETUP.md step 9](SETUP.md#9-create-a-site-and-turn-on-developer-mode).

- [x] Site created (`hr.localhost`, set as default site)
- [x] Developer mode enabled

---

## Step 10: Bind Address for Windows Access

Commands: [SETUP.md step 10](SETUP.md#10-make-the-dev-server-reachable-from-windows).

- [x] FRAPPE_BIND_ADDR set to 0.0.0.0 (verified in step 11: `web.1` logs `Running on all addresses (0.0.0.0)`)

---

## Step 11: Start Frappe + Setup Wizard

Commands: [SETUP.md step 11](SETUP.md#11-start-frappe-and-finish-the-setup-wizard).

- [x] `bench start` running inside `tmux` (session `bench`)
- [x] http://localhost:8000 accessible from Windows browser
- [x] Setup wizard completed (language, country, timezone, currency)

`bench start` output: web on `0.0.0.0:8000` (reachable as `127.0.0.1` and `10.0.2.15`), realtime on `ws://0.0.0.0:9000`. Requests from Windows arrive from `10.0.2.2`, the VirtualBox NAT gateway.

![bench start in tmux, login page on localhost:8000](screenshots/image17.png)

**Setup wizard choices:**

| Field | Value |
|---|---|
| Language | English |
| Country | Canada |
| Timezone | America/Toronto |
| Currency | CAD |

> The screenshot below shows America/Atikokan, which is what was first picked in the wizard. It was then changed to **America/Toronto** in System Settings → Time Zone, to match SETUP.md, the VM's OS time zone and `site_config.json`.

![Setup wizard](screenshots/image18.png)

---

## Step 12: Install HR Cost App

At this point the app had no git remote yet, so instead of `bench get-app` ([SETUP.md step 12](SETUP.md#12-install-the-hr-cost-app)) the folder was copied from Windows with `scp`. `bench get-app` would also have pip-installed the app and added it to `sites/apps.txt`. With `scp`, both have to be done by hand.

From Windows (PowerShell):

```powershell
scp -r -P 2222 "$HOME\Desktop\myProject\vm_linux_hr\hr_cost" frappe@127.0.0.1:/home/frappe/frappe-bench/apps/
```

In the VM, with `bench start` stopped:

```bash
cd ~/frappe-bench
bench pip install -e apps/hr_cost                    # put hr_cost on the bench's Python path
printf "frappe\nhr_cost\n" > sites/apps.txt          # register it with the bench
bench --site hr.localhost install-app hr_cost
bench --site hr.localhost migrate
bench --site hr.localhost execute hr_cost.demo.make_demo_data
bench start
```

- [x] App copied to `~/frappe-bench/apps/hr_cost`
- [x] `bench pip install -e apps/hr_cost` → `+ hr-cost==0.0.1`
- [x] `sites/apps.txt` = `frappe`, `hr_cost`
- [x] `install-app` → `Installing hr_cost... Updating DocTypes for hr_cost`
- [x] `migrate` completed
- [x] `bench --site hr.localhost list-apps` → `frappe 17.x.x-develop (407b551)`, `hr_cost 0.0.1`
- [x] Demo data → `Created 3 employees and 49 work records.`
- [x] Daily HR Cost report (current month): 19 days with work, 346.5 hours, total **CAD 8,981.00**
- [x] HR Cost tile opens the Work Record list in the HR Cost sidebar (after the route fix below)

**Issues encountered:**

1. ❌ `install-app` → `ModuleNotFoundError: No module named 'hr_cost'`
   The copied folder isn't a Python package the bench knows about yet.
   🔧 `bench pip install -e apps/hr_cost`
2. ❌ `install-app` → `App hr_cost not in apps.txt`
   🔧 First tried `echo "hr_cost" >> sites/apps.txt`, but `apps.txt` had no trailing newline, so the file became `frappehr_cost` and the next attempt failed with `No module named 'frappehr_cost'`. Rewriting the whole file with `printf "frappe\nhr_cost\n" > sites/apps.txt` fixed it.
3. ❌ `bench start` → `Could not create server TCP listening socket 127.0.0.1:11000 / 13000: bind: Address already in use`, then `Port 8000 is in use by another program`
   An earlier `bench start` (started 21:48) had been suspended with **Ctrl+Z** rather than stopped with Ctrl+C. A suspended process keeps its ports. `pkill -f redis-server` and `pkill -f "bench start"` freed the ports, but they missed the suspended `honcho start` process and its RQ worker. That worker kept taking jobs from the queue with a Python path from before `hr_cost` was installed.
   🔧 Stopped the leftover `honcho` process group (`kill` by PID). Check for leftovers with `ps -eo pid,stat,etimes,cmd | grep -E "honcho|bench_helper"`, where a `T` in the STAT column means suspended.
4. ❌ Clicking the **HR Cost** tile → *"Not found: Page hr-cost not found"*
   `hooks.py` sent the tile to `/desk/hr-cost`. On this `develop` build, a one-segment desk route resolves to a **Workspace** of that name (`router.js`: *"A one-segment route never carries a shell"*), and the app ships no Workspace. The site had none either (`frappe.get_all("Workspace")` listed only Frappe's own 8). The HR Cost sidebar isn't a document at all: Frappe computes it from the module's DocTypes and reports (`sidebar.get_computed_base("HR Cost")` → Employee, Work Record, Reports → Daily HR Cost). It is reached through them, as `/desk/hr-cost/<doctype>`.
   🔧 Changed the tile's route in `hooks.py` to `/desk/work-record`. The router then writes the shell in front, giving `/desk/hr-cost/work-record`. Copied the file to the VM, then ran `bench --site hr.localhost clear-cache`. `frappe.apps.get_apps()` now returns `route: /desk/work-record`.

---

## Step 13: Run Tests

Commands: [SETUP.md step 13](SETUP.md#13-run-the-tests).

- [x] `bench start` running in the tmux session (the tests need its Redis)
- [x] **Ran 23 tests in 2.455s — OK**
  - Work Record: 9 · Employee: 6 · Daily HR Cost report: 8
  - One `V17FrappeDeprecationWarning` (`limit_page_length`) is printed during `test_user_without_access_cannot_read_costs`. It comes from Frappe's own `frappe/model/qb_query.py`. The app's code doesn't use `limit_page_length`.

---

## Step 14: Push to GitHub

The repository was created in the VM and pushed from there, so `~/frappe-bench/apps/hr_cost` in the VM is the working copy from now on. It is edited through VS Code Remote-SSH.

Windows `~/.ssh/config`, so that `ssh frappe-dev` and VS Code Remote-SSH log in with the key:

```
Host frappe-dev
    HostName 127.0.0.1
    Port 2222
    User frappe
    IdentityFile ~/.ssh/frappe_dev_ed25519
    IdentitiesOnly yes
```

In the VM (VS Code terminal):

```bash
git config --global user.name "<name>"
git config --global user.email "<email>"
git config --global init.defaultBranch main
ssh-keygen -t ed25519 -C "<email>" -f ~/.ssh/id_ed25519 -N ""
cat ~/.ssh/id_ed25519.pub     # GitHub → Settings → SSH and GPG keys → New SSH key
ssh -T git@github.com         # answer "yes" to the host key prompt

cd ~/frappe-bench/apps/hr_cost
git init
git add .
git commit -m "Initial commit: HR Cost app"
git remote add origin git@github.com:Suyu0114/hr_cost.git
git push -u origin main
```

- [x] Windows and VM copies compared with `md5sum`. Only `.gitignore` and `docs/setup-procedure.docx` differed, and the newer Windows versions were copied to the VM
- [x] `~$*` added to `.gitignore`: Word keeps a hidden lock file (`docs/~$tup-procedure.docx`) next to an open document, and one had been copied to the VM
- [x] `ssh -T git@github.com` → `Hi Suyu0114! You've successfully authenticated`. The accepted host key `SHA256:+DiY3wvvV6TuJJhbpZisF/zLDA0zPMSvHdkr4UvCOqU` matches `SHA256_ED25519` in <https://api.github.com/meta>
- [x] Initial commit `2531d07` (52 files) pushed to <https://github.com/Suyu0114/hr_cost> (public)
- [x] CI (`.github/workflows/ci.yml`) passed on GitHub Actions: a fresh `develop` bench with MariaDB 11.8, then `run-tests --app hr_cost` ([run 36380208229](https://github.com/Suyu0114/hr_cost/actions/runs/36380208229))

**Issues encountered:**

1. ❌ VS Code Remote-SSH stopped at `frappe@127.0.0.1's password:` and the attempt was cancelled.
   The `frappe-dev` host entry had no `IdentityFile`, so VS Code didn't offer the key and asked for the password in a small box at the top of the window, which is easy to miss.
   🔧 Added `IdentityFile` and `IdentitiesOnly yes` (above).
2. ❌ The VM stopped responding for minutes at a time. At about 23:20, key login hung right after `Offering public key` and `/api/method/ping` returned HTTP 500. At 02:38, VS Code Remote-SSH failed with `kex_exchange_identification: read: Connection reset`. Each time the VM console looked normal afterwards (`uptime`, `free -m`, `df -h /`).
   `VBox.log` shows the VM getting no CPU time: `Guest seems to be unresponsive. Last heartbeat received 664 seconds ago` (about 23:19–23:30) and `TM: Not bothering to attempt catching up a 1 403 071 657 831 ns lag` (02:10–02:33). The second gap matches Windows **Modern Standby** to the second: the System log has Kernel-Power 506 *entering Modern Standby* at 01:35 and 507 *exiting* at 02:33:46. There is no standby event around 23:20, so the cause of the first gap is still open.
   🔧 Keep Windows awake while the VM is in use (Settings → System → Power & battery → Screen, sleep & hibernate timeouts → sleep *Never* when plugged in). When a connection fails, check the VM console first, and give the VM a minute after Windows wakes up.
3. ⚠️ The first push went to `https://github.com/Suyu0114/hr_cost.git`. It worked in the VS Code terminal because VS Code passes its own GitHub sign-in to git, but it would fail from a plain `ssh` session.
   🔧 `git remote set-url origin git@github.com:Suyu0114/hr_cost.git`, so pushes use the VM's own key.

---

## Post-install notes

| Item | Value / note |
|---|---|
| Time zone | ✅ **America/Toronto** in System Settings (changed from the wizard's America/Atikokan), `site_config.json` and the VM OS |
| Scheduler | Enabled (`bench --site hr.localhost scheduler status`) |
| Redis warning | `WARNING Memory overcommit must be enabled!` on every `bench start`. Harmless on a dev VM. To silence it: `sudo sysctl vm.overcommit_memory=1` (add it to `/etc/sysctl.conf` to keep it) |
| SSH key | `~/.ssh/frappe_dev_ed25519` on Windows is authorised in the VM's `~/.ssh/authorized_keys`, and is the `IdentityFile` of `Host frappe-dev` in `~/.ssh/config` (`ssh frappe-dev`) |
| Git remote | `git@github.com:Suyu0114/hr_cost.git`. The VM's own `~/.ssh/id_ed25519` is registered on GitHub |

---

## Appendix: Troubleshooting Encountered

| Issue | Resolution |
|---|---|
| First VM created with wrong ISO (26.04 instead of 24.04 LTS) | Deleted VM, re-downloaded 24.04 LTS ISO |
| Unattended install checked by mistake | Recreated VM with checkbox unchecked |
| VM started before port forwarding configured | Deleted and recreated VM |
| `install-app`: *No module named 'hr_cost'* after copying with `scp` | `bench pip install -e apps/hr_cost` |
| `install-app`: *App hr_cost not in apps.txt* / *No module named 'frappehr_cost'* | `printf "frappe\nhr_cost\n" > sites/apps.txt` (`echo >>` joined it onto the last line) |
| `bench start`: *Address already in use* on 11000 / 13000 / 8000 | An old `bench start` was suspended with Ctrl+Z. Stop the leftover `honcho` process group, and always stop `bench start` with Ctrl+C |
| HR Cost tile: *Page hr-cost not found* | Tile route changed from `/desk/hr-cost` to `/desk/work-record` in `hooks.py` |
| SSH hangs, or VS Code: *kex_exchange_identification: read: Connection reset* | The VM was paused, for example while Windows was in Modern Standby (`VBox.log`: *Guest seems to be unresponsive*). Keep Windows awake while using the VM, and check the VM console first |
| VS Code Remote-SSH asks for a password | Add `IdentityFile ~/.ssh/frappe_dev_ed25519` and `IdentitiesOnly yes` to `Host frappe-dev` in `~/.ssh/config` |
| First push went over HTTPS, using VS Code's GitHub sign-in | `git remote set-url origin git@github.com:Suyu0114/hr_cost.git` |
