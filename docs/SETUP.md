# Setup: Frappe (`develop`) on a VirtualBox VM

This is the procedure used to install the development version of Frappe inside a VirtualBox VM on a Windows host, and to run the HR Cost app on it.

"Development version" here means both of these:

- the **`develop` branch** of [frappe/frappe](https://github.com/frappe/frappe), which is the repo's default branch and currently `17.0.0-dev`
- a site running in **developer mode**, so DocTypes and reports created in the app are exported to its source code

## Versions used

| Component | Version | Notes |
|---|---|---|
| Host OS | Windows 10/11 x64 | |
| Hypervisor | Oracle VirtualBox 7.2.18 | |
| Guest OS | Ubuntu Server 24.04.5 LTS | |
| Frappe | `develop` @ `407b551` (2026-09-27), `17.0.0-dev` | `bench list-apps` shows it as `17.x.x-develop` |
| bench CLI | 5.31.0 | installed with `uv tool` |
| Python | 3.14.7 | `develop` requires `>=3.14,<3.15`; Ubuntu 24.04 ships 3.12, so Python comes from `uv` |
| Node.js | 24.21.0 | `develop` requires `>=24` |
| Yarn | 1.22.22 | |
| MariaDB | 10.11.14 (Ubuntu package) | Frappe's version check warns outside 10.6–11.8; upstream CI tests on 11.8 |
| Redis | 7.0.15 (Ubuntu package) | |

> `develop` changes daily. If a step fails with a version error, compare it with `pyproject.toml` (`requires-python`) and `package.json` (`engines.node`) in the Frappe repo.

---

## 1. Host prerequisites (Windows)

1. **Hardware virtualisation is on** (Intel VT-x / AMD-V in the BIOS/UEFI). You can check this in Task Manager → Performance → CPU → *Virtualization: Enabled*.
2. **Install VirtualBox 7.x** from <https://www.virtualbox.org/wiki/Downloads> (*Windows hosts*).
3. **Download Ubuntu Server 24.04 LTS** (`ubuntu-24.04.x-live-server-amd64.iso`) from <https://ubuntu.com/download/server>.
4. Recommended resources: 16 GB RAM on the host (8 GB of it goes to the VM) and about 40 GB of free disk.

> **If the VM is very slow**, check whether Hyper-V, WSL2 or *Core isolation → Memory integrity* is turned on in Windows. When one of them is on, VirtualBox has to run on top of the Windows Hypervisor Platform and gets noticeably slower (a green turtle icon appears in the VM's status bar). Turning those features off, or accepting the slowdown, are both valid options for a dev VM.

## 2. Create the VM

In VirtualBox Manager, click **New**:

| Setting | Value |
|---|---|
| VM Name | `frappe-dev-ub24` |
| ISO Image | the Ubuntu Server ISO |
| OS / OS Distribution / OS Version | Linux / Ubuntu / Ubuntu 24.10 (Oracular Oriole) (64-bit) |
| Proceed with Unattended Installation | **Unticked**, so you choose the options yourself in the installer |
| Base memory | **8192 MB** (minimum 4096. Building the front-end assets with Node uses a lot of memory) |
| Processors | **4** (minimum 2) |
| Hard disk | **40 GB** VDI, dynamically allocated |

Before starting the VM, go to **Settings → Network → Adapter 1**: keep *Attached to: NAT*, open **Advanced → Port Forwarding** and add these rules:

| Name | Protocol | Host IP | Host Port | Guest IP | Guest Port |
|---|---|---|---|---|---|
| ssh | TCP | 127.0.0.1 | 2222 | *(empty)* | 22 |
| frappe-web | TCP | 127.0.0.1 | 8000 | *(empty)* | 8000 |
| frappe-socketio | TCP | 127.0.0.1 | 9000 | *(empty)* | 9000 |

Binding the host side to `127.0.0.1` means only your own PC can reach the VM, not the rest of your LAN. Port 9000 is Frappe's realtime (Socket.IO) service, which the browser connects to directly.

The same rules from a Windows terminal (with the VM powered off):

```powershell
& "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe" modifyvm frappe-dev-ub24 `
  --natpf1 "ssh,tcp,127.0.0.1,2222,,22" `
  --natpf1 "frappe-web,tcp,127.0.0.1,8000,,8000" `
  --natpf1 "frappe-socketio,tcp,127.0.0.1,9000,,9000"
```

## 3. Install Ubuntu Server

Start the VM and go through the installer:

1. Language: English. Installer update: skip if offered.
2. Type of install: **Ubuntu Server** (not the minimized one).
3. Network: keep the DHCP address on `enp0s3`. Proxy: none. Mirror: default.
4. Storage: *Use an entire disk*. For a disposable dev VM, untick *Set up this disk as an LVM group* so the whole disk is used for `/`.
5. Profile: server name `frappe-dev`, username **`frappe`**, and a password.
6. SSH: tick **Install OpenSSH server**.
7. Featured snaps: none. Wait for the install to finish, then choose **Reboot Now**. If the VM boots into the installer again, remove the ISO under *Devices → Optical Drives* and reboot.

From here on, work from a **Windows Terminal / PowerShell** window over SSH, which makes copy and paste much easier than the VM console:

```powershell
ssh -p 2222 frappe@127.0.0.1
```

## 4. System packages

Update the system (and set your time zone):

```bash
sudo apt update && sudo apt -y upgrade
sudo timedatectl set-timezone America/Toronto   # optional
sudo reboot                                     # if a new kernel was installed
```

Then install the packages:

```bash
sudo apt install -y git curl build-essential pkg-config \
  mariadb-server mariadb-client libmariadb-dev \
  redis-server
```

| Package(s) | Why |
|---|---|
| `git` | bench clones Frappe and apps with git |
| `build-essential`, `pkg-config`, `libmariadb-dev` | compile the `mysqlclient` Python package, which has no Linux wheel |
| `mariadb-server`, `mariadb-client` | database |
| `redis-server` | bench runs its own Redis instances for cache and queue (ports 13000/11000) using this binary |

`wkhtmltopdf` is only needed to print documents as PDF, and this app doesn't do that, so it is skipped.

## 5. MariaDB root password

`bench new-site` connects to MariaDB as `root` **with a password** to create the site's database and user. On Ubuntu, root uses socket authentication and has no usable password by default, so set one:

```bash
sudo mariadb -e "SET PASSWORD FOR 'root'@'localhost' = PASSWORD('<db-root-password>');"
```

This keeps socket login working (`sudo mariadb` still works without a password) and adds password login next to it. To check:

```bash
mariadb -h 127.0.0.1 -u root -p -e "select version();"
```

(`sudo mariadb-secure-installation`, the interactive tool in the official docs, does the same thing: answer **n** to *Switch to unix_socket authentication* and **Y** to *Change the root password*.)

Many older guides also add `utf8mb4` settings to `my.cnf`. That is **no longer needed on `develop`**: Frappe creates each site database with `CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci` itself (`frappe/database/db_manager.py`).

## 6. Node.js 24 and Yarn (via nvm)

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
source ~/.bashrc
nvm install 24
npm install -g yarn
node -v    # v24.x
yarn -v    # 1.22.x
```

Ubuntu's own `nodejs` package is too old. With Node < 24, `yarn install` fails with *"The engine "node" is incompatible"*.

## 7. Python 3.14 (via uv) and the bench CLI

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
uv python install 3.14
uv tool install frappe-bench
bench --version
```

The system `python3` (3.12) is left alone. Instead, bench is pointed at uv's 3.14 explicitly in the next step. The official docs use `uv python install 3.14 --default`, which also works, but it makes `python3` mean 3.14 for your user.

## 8. Create the bench on `develop`

```bash
cd ~
bench init --frappe-branch develop --python "$(uv python find 3.14)" frappe-bench
cd ~/frappe-bench
```

This clones Frappe, creates the virtualenv (`env/`), installs the Python and JS dependencies and builds the assets. It takes a few minutes. Near the end you will see `WARN Cannot connect to redis_cache…`. That is expected: the bench's own Redis isn't running yet.

`--python` pins the interpreter explicitly. Without it, bench asks uv for `python3`, and uv resolves that to *any* Python 3, preferring the ones it manages. After step 7 that usually means 3.14, but only implicitly. If 3.14 isn't installed through uv (or uv is disabled with `BENCH_DISABLE_UV=1`), bench falls back to the system Python 3.12, and installing Frappe fails because `develop` requires Python 3.14.

## 9. Create a site and turn on developer mode

```bash
cd ~/frappe-bench
bench new-site hr.localhost \
  --db-root-password '<db-root-password>' \
  --admin-password '<admin-password>' \
  --set-default
bench --site hr.localhost set-config developer_mode 1
bench --site hr.localhost clear-cache
```

About `--set-default`: normally Frappe picks the site from the request's `Host` header. From Windows the browser sends `Host: localhost:8000`, which doesn't match `hr.localhost`, so you would get a 404 *"localhost does not exist"*. `--set-default` writes `default_site` to `sites/common_site_config.json`. `bench serve` then starts the dev server pinned to that site, and it answers every request with `hr.localhost` whatever the host name. If you forgot the flag, run `bench use hr.localhost` and restart `bench start`.

## 10. Make the dev server reachable from Windows

**This step is easy to miss.** On `develop`, `bench serve` (the `web` process in the Procfile) binds to **`127.0.0.1` by default** (`frappe/app.py`: `bind_addr or os.environ.get("FRAPPE_BIND_ADDR") or "127.0.0.1"`). VirtualBox NAT sends forwarded connections to the VM's network interface (`10.0.2.15`), not to its loopback address, so with the default setting the browser on Windows can't connect.

Set the bind address once for your user:

```bash
echo 'export FRAPPE_BIND_ADDR=0.0.0.0' >> ~/.bashrc
source ~/.bashrc
```

(This is safer than editing the Procfile, because `bench setup procfile` would overwrite that change.) Exposing the dev server on all interfaces is fine here: the VM sits behind NAT, and the port-forward rules only listen on the host's `127.0.0.1`.

## 11. Start Frappe and finish the setup wizard

```bash
cd ~/frappe-bench
bench start
```

Keep this running. Optionally start it inside `tmux new -s bench` so it survives an SSH disconnect.

On Windows, open **<http://localhost:8000>** and log in as `Administrator` with `<admin-password>`. A new site shows a **setup wizard** first: choose language, country, **time zone** and **currency** (for example America/Toronto and CAD), then click *Complete Setup*. The currency you pick here is what the app's Currency fields display.

## 12. Install the HR Cost app

Stop `bench start` first (**Ctrl+C**). bench installs apps in editable mode, which adds the app's folder to Python's import path through a `.pth` file, and Python only reads `.pth` files when a process starts. The scheduler re-reads the installed apps on every tick, so once the app is added it fails with `ModuleNotFoundError: No module named 'hr_cost'`, and `bench start` then stops every other process with it.

```bash
cd ~/frappe-bench
bench get-app https://github.com/Suyu0114/hr_cost --branch main
bench --site hr.localhost install-app hr_cost
bench --site hr.localhost execute hr_cost.demo.make_demo_data   # optional sample data
bench start
```

Then click the **HR Cost** tile on the desk home, or open <http://localhost:8000/desk/work-record>. Either way the desk shows the Work Record list in the **HR Cost** sidebar, and the address bar changes to `/desk/hr-cost/work-record`.

`/desk/hr-cost` on its own gives *"Page hr-cost not found"*. On `develop`, a one-segment desk route opens a **Workspace** of that name, and the app ships none. Its sidebar is computed from the module's DocTypes and reports instead, and is reached through them (`/desk/hr-cost/<doctype>`).

### How the app itself was created (for reference)

```bash
bench new-app hr_cost          # title "HR Cost", MIT, GitHub workflow = yes, branch main
bench --site hr.localhost install-app hr_cost
```

The Employee and Work Record DocTypes and the *Daily HR Cost* Script Report were then created in module **HR Cost** with developer mode on. Frappe writes them to `apps/hr_cost/hr_cost/hr_cost/{doctype,report}/…` as JSON and Python/JS files, and those files were then edited to add the business logic and tests.

## 13. Run the tests

Run these in a second SSH session while `bench start` is running. The tests need the bench's Redis. Without it they fail with an unhelpful `AssertionError: Should not fail silently in tests`.

```bash
cd ~/frappe-bench
bench --site hr.localhost set-config allow_tests true
bench --site hr.localhost run-tests --app hr_cost
# Ran 23 tests … OK
```

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| Browser: *connection refused / reset* on `localhost:8000` | `bench start` isn't running, a port-forward rule is missing, or `FRAPPE_BIND_ADDR` isn't set (check with `ss -ltn \| grep 8000` in the VM: it must show `0.0.0.0:8000`) |
| Browser: 404 *"localhost does not exist."* | No default site. Run `bench use hr.localhost`, then restart `bench start` |
| `bench init`: *the current Python version (3.12.x) does not satisfy Python>=3.14,<3.15* | bench got the system Python 3.12. Check that `uv python find 3.14` works and pass it with `--python` (step 8) |
| `yarn install`: *The engine "node" is incompatible with this module. Expected version ">=24"* | Node < 24. Run `nvm install 24 && nvm use 24` |
| `new-site`: *Access denied for user 'root'@'localhost'* (error 1698 or 1045) | Wrong or unset MariaDB root password (step 5). When `new-site` then asks whether to roll back the site, answer **y**. If you answered no, delete `sites/<site-name>/` or re-run with `--force` |
| `bench start`: *Address already in use* on 11000 / 13000, or *Port 8000 is in use* | An earlier `bench start` is still running or was suspended with **Ctrl+Z** (a suspended process keeps its ports). Find it with `ps -eo pid,stat,cmd \| grep -E "honcho\|bench_helper"` (`T` = suspended) and stop it. `pkill -f "bench start"` misses it, because the process is named `honcho start`. Stop `bench start` with Ctrl+C |
| All processes stop and the log shows `ModuleNotFoundError: No module named 'hr_cost'` | An app was added while `bench start` was running. Start it again |
| Clicking the HR Cost tile: *Page hr-cost not found* | The tile's `route` in `hooks.py` is `/desk/hr-cost`, which only resolves to a Workspace named HR Cost, and the app ships none. Use `/desk/work-record` (step 12), then `bench --site hr.localhost clear-cache` |
| Tests fail with *Should not fail silently in tests* | Redis isn't running. Start `bench start` in another session |
| Windows: port 8000 already in use | Free port 8000 on Windows. Keep host port = guest port: in developer setups the realtime service authenticates by calling the web server back on the browser's origin port, so remapping only the host port (e.g. 8080 → 8000) breaks realtime features without an obvious error |
| VM very slow, turtle icon | Hyper-V / VBS is on in Windows (see step 1) |
