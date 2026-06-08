# FDB Applet

<div align="justify">

A computational tool for the representation theory of gentle, string, and (in future releases) biserial algebras.

**Version:** 1.0 &nbsp;·&nbsp; **Release date:** June 2026

---


## **Table of Contents**

1. [About the FDB Applet](#1-about-the-fdb-applet)
2. [Quick start](#2-quick-start)
3. [Installation](#3-installation)
   - [3.1 Windows](#31-windows)
   - [3.2 macOS](#32-macos)
   - [3.3 Other operating systems (Linux, BSD, etc.)](#33-other-operating-systems-linux-bsd-etc)
4. [Loading a sample algebra inside the applet](#4-loading-a-sample-algebra-inside-the-applet)
5. [Online version](#5-online-version)
6. [Citing the FDB Applet](#6-citing-the-fdb-applet)

---


## **1. About the FDB Applet**

The FDB Applet has been developed exclusively as a computational tool intended to facilitate research on problems arising in the representation theory of gentle algebras and string algebras. Furthermore, the long-term objective of this project is to incorporate additional functionalities relevant to the study of biserial algebras. This constitutes one of the two principal motivations for the inclusion of the letter "B" in the name "FDB," standing for "Finite-Dimensional Biserial." The second motivation is explained below.

In the development of the FDB Applet, we have benefited substantially from the highly valuable and elegant FD Applet developed and released in 2023 by Haruhisa Enomoto, available at [FD Applet by Haruhisa Enomoto](https://haruhisa-enomoto.github.io/fd-applet/?utm_source=chatgpt.com#about-fd-applet). We wish to expressly acknowledge the significant conceptual, structural, and practical inspiration provided by the FD Applet. The present project owes a considerable intellectual and organizational debt to this prior contribution, for which we are sincerely grateful. FDB Applet contains various important portions translated or adapted from FD Applet, which was developed by Haruhisa Enomoto and released under the MIT License. This also explains the second motivation for the inclusion of the letter "B" in the name "FDB Applet," as the present software may be viewed, in a broad conceptual sense, as a secondary branch or extended continuation of the original FD Applet framework.

***Why a new applet?*** Noting that the aforementioned FD Applet does not appear to have undergone substantial updates since mid-2023, we contacted the original developer in order to propose the incorporation of additional functionalities and extensions. After some correspondence, we understood that the latest version of FD Applet from July 2023 might no longer go through further developments. Consequently, we were motivated to implement functionalities addressing developments that have emerged in recent years, particularly those connected with the extensive study of bricks and related phenomena, which occupy a central position in our ongoing research program. It is our hope that the FD Applet and FDB Applet will ultimately contribute to future collaborative initiatives and evolve into a useful computational resource for the broader research community.

From the implementation perspective, the development process initially involved the translation of substantial portions of the original FD Applet codebase from Kotlin into Python with the assistance of [Claude](https://claude.ai?utm_source=chatgpt.com), followed by the integration of additional computational functionalities and extensions. Both the software development process and the preparation of the accompanying documentation benefited significantly from the foundational contribution of the FD Applet and from the technical assistance provided by Claude.

Users are kindly advised that the current version of the FDB Applet remains under active development and may therefore still contain mathematical inaccuracies, technical defects, or partially implemented functionalities. In particular, certain tabs or features may not yet perform their intended operations in the present release, although such functionalities are expected to be completed and incorporated in forthcoming versions of the software.

Should users identify any mathematical inaccuracies, computational inconsistencies, or technical malfunctions, they are warmly encouraged to communicate their observations and suggestions to the developer, Kaveh Mousavand, at [kaveh.mousavand@oist.jp](mailto:kaveh.mousavand@oist.jp).

**License:** MIT — see the [`LICENSE`](./LICENSE) file in this distribution.

---


## **2. Quick start**

For users already comfortable with a command line, the entire desktop installation reduces to the following five steps (assuming Python 3.10+ is already installed):

```bash
unzip FDB-Applet.zip
cd FDB-Applet
python3 -m pip install fastapi uvicorn
python3 -m uvicorn fd_applet_python.server:app --port 8000
# then double-click  fd_applet_python/fd_applet_visual.html
```

On Windows, replace `python3` with `python`. If you do not want to install anything at all, jump to [§5, Online version](#5-online-version) and simply double-click `fd_applet_browser.html`.

A platform-by-platform walkthrough, including download links and troubleshooting, follows in [§3](#3-installation).

---


## **3. Installation**

The desktop version of the FDB Applet runs a small local server (FastAPI + uvicorn) on your computer and uses your existing web browser as the user interface. Once installed, no internet connection is required to use it.

The following subsections give complete, copy-pasteable instructions for **Windows**, **macOS**, and **other operating systems**.

### **Common files**

The zip you downloaded contains:

```
FDB-Applet/
├── README.md                       ← this file
├── README.txt                      ← plain-text README
├── LICENSE                         ← MIT License
├── fd_applet_browser.html          ← online (no-install) version
├── fd_applet_python/               ← Python source for the desktop version
│   ├── server.py                   ← FastAPI backend
│   ├── fd_applet_visual.html       ← desktop user-interface page
│   ├── algebra/                    ← math engine (string/gentle/RF algebras)
│   ├── quiver/                     ← quiver/word/monomial utilities
│   └── …
└── examples/                       ← (if present) sample algebra JSON files
```

### **3.1 Windows**

#### **3.1.1 Requirements**

| Component | Minimum version | Download |
|-----------|-----------------|----------|
| Windows | 10 or 11 | already installed on your PC |
| Python | 3.10 or newer | <https://www.python.org/downloads/windows/> |
| A modern web browser | any current build | Edge (preinstalled), [Chrome](https://www.google.com/chrome/), or [Firefox](https://www.mozilla.org/firefox/) |

You will also install two Python packages — `fastapi` and `uvicorn` — during the steps below. They are downloaded automatically from <https://pypi.org/>.

#### **3.1.2 Step-by-step installation**

1. **Install Python.** Go to <https://www.python.org/downloads/windows/> and click the yellow *"Download Python 3.x.x"* button. Run the installer. On the very first installer screen, **tick the checkbox** *"Add python.exe to PATH"* at the bottom, then click *"Install Now"* and wait for the installer to finish.

2. **Unzip the FDB Applet folder.** Right-click the zip you downloaded and choose *"Extract All…"*. Pick a convenient location, for example your Desktop. After extraction you should have a folder called `FDB-Applet` containing `fd_applet_python\`, `README.md`, and `fd_applet_browser.html`.

3. **Open a terminal in that folder.** In File Explorer, hold **Shift** and right-click on an empty area inside the `FDB-Applet` folder, then choose *"Open in Terminal"* (Windows 11) or *"Open PowerShell window here"* (Windows 10). A blue/black window appears.

   *Confirm you are in the right place.* Type `dir` and press **Enter**. The listing **must include `fd_applet_python`**. If you instead see another `FDB-Applet` folder, *"Extract All…"* created a doubly-nested folder — type `cd FDB-Applet` and run `dir` again. If you see neither, close the terminal and reopen it from the correct folder.

4. **Verify Python is installed.** Type the following and press **Enter**:
   ```powershell
   python --version
   ```
   You should see something like `Python 3.12.4`. If you see `'python' is not recognized…`, see the troubleshooting section below.

5. **Install the required Python packages.** In the same terminal type:
   ```powershell
   python -m pip install --upgrade pip
   python -m pip install fastapi uvicorn
   ```
   Wait for both commands to finish. You can ignore any yellow warnings as long as the last line says something like `Successfully installed …`.

6. **Start the FDB Applet server.** Still in the same terminal:
   ```powershell
   python -m uvicorn fd_applet_python.server:app --port 8000
   ```
   The terminal should print a few lines ending with `Application startup complete.` followed by `Uvicorn running on http://0.0.0.0:8000`. **Leave this window open** — closing it stops the applet.

7. **Open the user interface.** In File Explorer, double-click `fd_applet_python\fd_applet_visual.html`. It opens in your default browser and connects to the local server you started in step 6.

8. **(Optional) Stop the applet.** When you are done, switch back to the terminal window and press **Ctrl + C** to stop the server. You may then close the terminal.

To use the applet again later, you only need steps 3, 6, and 7.

#### **3.1.3 Troubleshooting (Windows)**

| Symptom | Probable cause and fix |
|---------|-----------------------|
| `'python' is not recognized as an internal or external command` | The "Add to PATH" checkbox was not ticked during install. Re-run the Python installer, choose *"Modify"*, and tick *"Add Python to environment variables"*. Then close and reopen the terminal. |
| `ModuleNotFoundError: No module named 'fastapi'` after step 6 | Step 5 was skipped or ran in a different Python environment. Repeat step 5 in the same terminal that you use for step 6. |
| `ModuleNotFoundError: No module named 'fd_applet_python'` at step 6 | Your terminal's current directory is not the `FDB-Applet` folder. Type `dir` — if `fd_applet_python` is missing from the listing, use `cd` to move into the folder that contains it. *"Extract All…"* sometimes creates a doubly-nested folder, in which case `cd FDB-Applet` fixes it. As a bulletproof fallback, append <code>--app-dir "C:\full\path\to\FDB-Applet"</code> to the uvicorn command. |
| `[Errno 10048] Only one usage of each socket address … 8000` | Another program is already using port 8000. Either stop that program, or start the applet on a different port, e.g. `python -m uvicorn fd_applet_python.server:app --port 8765`, and use `http://localhost:8765` instead. |
| The browser page opens but every tab shows "✗ Error: Failed to fetch" | The local server in step 6 is not running, or you closed the terminal. Repeat step 6 to start it again. |
| Windows SmartScreen or your antivirus blocks `python.exe` | Click *"More info" → "Run anyway"* on the SmartScreen dialog, or add an exception for Python in your antivirus settings. |
| The browser keeps showing an old version after you update the zip | Press **Ctrl + Shift + R** to do a hard refresh of the page. |

### **3.2 macOS**

#### **3.2.1 Requirements**

| Component | Minimum version | Download |
|-----------|-----------------|----------|
| macOS | 11 (Big Sur) or newer | already installed on your Mac |
| Python | 3.10 or newer | <https://www.python.org/downloads/macos/> |
| A modern web browser | any current build | Safari (preinstalled), [Chrome](https://www.google.com/chrome/), or [Firefox](https://www.mozilla.org/firefox/) |

You will also install `fastapi` and `uvicorn` from <https://pypi.org/> during the steps below.

#### **3.2.2 Step-by-step installation**

1. **Install Python.** Go to <https://www.python.org/downloads/macos/> and click the *"Download Python 3.x.x"* button. Open the downloaded `.pkg` file and follow the installer. After it finishes, also double-click `Applications/Python 3.x/Install Certificates.command` once — this is the recommended step that the installer mentions at the end.

   *Alternative for advanced users:* if you have [Homebrew](https://brew.sh/) installed, you can instead run `brew install python` in Terminal.

2. **Unzip the FDB Applet folder.** Double-click the zip you downloaded; macOS automatically extracts it into a folder called `FDB-Applet`. Move that folder somewhere you can find it again, for example your Desktop or your `Documents` folder.

3. **Open a Terminal in that folder.** In Finder, right-click (or Control-click) the `FDB-Applet` folder and choose *"New Terminal at Folder"*. A Terminal window opens already `cd`'d into the folder.

   *Or, manually:* open **Terminal.app** (in `Applications/Utilities/`) and type `cd ` (with a trailing space), then drag the `FDB-Applet` folder onto the Terminal window, then press **Enter**.

   *Confirm you are in the right place.* Type `ls` and press **Return**. The listing **must include `fd_applet_python`**. If you instead see another `FDB-Applet` folder, the unzip created a doubly-nested folder — type `cd FDB-Applet` and run `ls` again.

4. **Verify Python is installed.**
   ```bash
   python3 --version
   ```
   You should see `Python 3.10.x` or newer. If not, repeat step 1.

5. **Install the required Python packages.**
   ```bash
   python3 -m pip install --upgrade pip
   python3 -m pip install fastapi uvicorn
   ```
   You may see a warning about installing into the "system" Python — that is fine for a personal install. If pip refuses with a *"externally-managed-environment"* error, see the troubleshooting section below.

6. **Start the FDB Applet server.**
   ```bash
   python3 -m uvicorn fd_applet_python.server:app --port 8000
   ```
   You should see a line that ends with `Uvicorn running on http://0.0.0.0:8000`. **Leave this Terminal window open** — closing it stops the applet.

7. **Open the user interface.** In Finder, double-click `fd_applet_python/fd_applet_visual.html`. It opens in your default browser and connects to the local server.

8. **(Optional) Stop the applet.** Click on the Terminal window and press **Control + C**. You may then quit Terminal.

To use the applet again later, you only need steps 3, 6, and 7.

#### **3.2.3 Troubleshooting (macOS)**

| Symptom | Probable cause and fix |
|---------|-----------------------|
| `zsh: command not found: python3` | Python is not installed yet. Go back to step 1. |
| `error: externally-managed-environment` from pip | Recent macOS Python distributions discourage installing packages into the system Python. The simplest fix is to create a virtual environment first:<br>`python3 -m venv .venv`<br>`source .venv/bin/activate`<br>`python3 -m pip install fastapi uvicorn`<br>Then run step 6 from the **same** Terminal window (the one where you activated the venv). |
| `ModuleNotFoundError: No module named 'fd_applet_python'` at step 6 | Your Terminal's current directory does not contain `fd_applet_python`. Run `ls` to check, then `cd` into the right folder (often `cd FDB-Applet` if the unzip nested the folder). As a bulletproof fallback, append <code>--app-dir "/full/path/to/FDB-Applet"</code> to the uvicorn command. |
| `ssl.SSLCertVerificationError` while pip is downloading packages | You missed the `Install Certificates.command` step in step 1. Open `Applications/Python 3.x/`, double-click `Install Certificates.command`, then retry step 5. |
| `OSError: [Errno 48] Address already in use` on step 6 | Another program is using port 8000. Start the applet on a different port, e.g. `python3 -m uvicorn fd_applet_python.server:app --port 8765`, and use `http://localhost:8765` instead. |
| Browser tabs show "✗ Error: Failed to fetch" | The local server in step 6 is not running, or the Terminal was closed. Repeat step 6. |
| "FDB Applet" can't be opened because the developer cannot be verified | This message can appear when macOS Gatekeeper sees an unsigned helper script. Open **System Settings → Privacy & Security**, scroll to the bottom, and click *"Open Anyway"* for the blocked item, then try again. |
| The browser keeps showing an old version after you update the zip | Press **Cmd + Shift + R** to do a hard refresh of the page. |

### **3.3 Other operating systems (Linux, BSD, etc.)**

The FDB Applet is pure Python and runs on any platform where Python 3.10+, FastAPI, and uvicorn are available.

#### **3.3.1 Requirements**

| Component | Minimum version | Notes |
|-----------|-----------------|-------|
| Python | 3.10 or newer | install via your distribution's package manager (`apt`, `dnf`, `pacman`, `pkg`, …) or from <https://www.python.org/downloads/source/> |
| `pip` and `venv` modules | matching your Python | usually a separate package, e.g. `python3-pip` and `python3-venv` on Debian/Ubuntu |
| A modern web browser | any current build | Firefox, Chrome/Chromium, or any WebKit-based browser |

#### **3.3.2 Step-by-step installation**

1. **Install Python 3.10+ and pip.** Examples:
   ```bash
   # Debian / Ubuntu
   sudo apt update && sudo apt install -y python3 python3-pip python3-venv
   # Fedora / RHEL
   sudo dnf install -y python3 python3-pip
   # Arch Linux
   sudo pacman -S python python-pip
   # FreeBSD
   sudo pkg install python3 py39-pip
   ```

2. **Unzip the FDB Applet folder.**
   ```bash
   unzip FDB-Applet.zip
   cd FDB-Applet
   ls          # must list  fd_applet_python  among the entries
   ```
   If `ls` shows another `FDB-Applet` folder instead, the archive was nested — run `cd FDB-Applet` once more and re-check with `ls`.

3. **(Recommended) Create and activate a virtual environment.**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
   (You will need to run `source .venv/bin/activate` again each time you open a new terminal.)

4. **Install the required Python packages.**
   ```bash
   python3 -m pip install --upgrade pip
   python3 -m pip install fastapi uvicorn
   ```

5. **Start the FDB Applet server.**
   ```bash
   python3 -m uvicorn fd_applet_python.server:app --port 8000
   ```
   Leave this terminal open.

6. **Open the user interface.** In your file manager, double-click `fd_applet_python/fd_applet_visual.html`, or run:
   ```bash
   xdg-open fd_applet_python/fd_applet_visual.html   # most desktop Linux
   ```
   The page opens in your default browser and connects to the local server.

7. **(Optional) Stop the applet** with **Ctrl + C** in the terminal.

#### **3.3.3 Troubleshooting (Linux / other)**

| Symptom | Probable cause and fix |
|---------|-----------------------|
| `command not found: python3` | Python is not installed; see step 1. |
| `ModuleNotFoundError: No module named 'fastapi'` | The packages were installed into a different Python than the one you are running. If you used a venv in step 3, make sure it is still activated (`source .venv/bin/activate`). |
| `error: externally-managed-environment` from pip | Your distribution prefers virtual environments. Use the venv steps in 3–4. |
| `ModuleNotFoundError: No module named 'fd_applet_python'` at step 5 | Your shell's current directory does not contain `fd_applet_python`. Run `ls` to check, then `cd` to the folder containing it (often `cd FDB-Applet` if `unzip` nested the folder). As a bulletproof fallback, append <code>--app-dir "/full/path/to/FDB-Applet"</code> to the uvicorn command. |
| `Address already in use` on step 5 | Port 8000 is taken. Choose another port, e.g. `--port 8765`, and open `http://localhost:8765`. |
| Page loads but all tiles show "✗ Error: Failed to fetch" | The local server is not running, or you started it on a different port. Repeat step 5 with the matching port. |
| File manager refuses to open the HTML in a browser | Open the browser first, then drag `fd_applet_visual.html` onto the browser window. |

---


## **4. Loading a sample algebra inside the applet**

Once the user interface is open in your browser (after step 7 of the platform-specific installation in [§3](#3-installation), or by opening `fd_applet_browser.html` for the online version), the applet starts with an empty quiver. The following walkthrough builds and analyses the path algebra of the linear quiver

> **A₃:**&nbsp; 1 — *a* → 2 — *b* → 3,

which is the simplest non-trivial example and produces a small, readable output for every tile.

1. **Add vertices.** In the *Quiver* panel on the left, click the **"+ Vertex"** button three times. Three nodes labelled `1`, `2`, `3` appear on the canvas. You can drag them with the mouse to lay them out from left to right.

2. **Add arrows.** Click **"+ Arrow"**, then click on vertex `1` and then on vertex `2`. An arrow labelled `a` appears from `1` to `2`. Click **"+ Arrow"** again, then click on `2` and on `3`; an arrow labelled `b` appears.

3. **(Optional) Add relations.** For the plain A₃ path algebra leave the *Monomial relations* and *Binomial relations* boxes empty. If you would like to try a quotient, type, for example, `a*b` in the monomial-relations box and press **+** to add it; the algebra then becomes A₃ with `a·b = 0`.

4. **Load the algebra.** Click the green **"Load Algebra"** button at the bottom of the left panel. After a short moment the status line shows *"✓ GentleAlgebra"* (or *"✓ StringAlgebra"* depending on your relations), and the *Results* area on the right becomes active.

5. **Explore the tiles.** Click any tile in the *Results* grid. A few suggestions for A₃:

   - **Information** — confirms that A₃ is gentle, finite-dimensional, of dimension 6, and representation-finite with 6 indecomposables.
   - **Indecomposables & bands** — lists the 6 indecomposable modules, three simples plus the strings `a`, `b`, and `a*b`.
   - **τ-Phenomena → AR-quiver** — draws the Auslander–Reiten quiver, with the standard mesh structure for A₃.
   - **Hom / Ext tables** — shows the dim Hom and dim Ext¹ matrices on all indecomposables.
   - **Splitting classes → Brick-splitting** — shows, for each torsion class, the (semi)brick that labels it. For A₃ (and, more generally, for any hereditary algebra) every torsion class is brick-splitting, so the panel reports that all 14 torsion classes admit a brick label.
   - **Lattices & Quivers → Brick Quiver** — draws the brick quiver of the algebra, whose vertices are the indecomposable bricks and whose arrows record the irreducible morphisms between them. For A₃ all 6 indecomposables are bricks, and the diagram makes the six-vertex morphism structure immediately visible.
   - **Lattices & Quivers → Torsion-class lattice** — draws the lattice of torsion classes (14 classes, the Tamari lattice for A₃).

6. **Try another algebra.** To switch to a different example, simply edit the quiver / relations in the left panel and press **"Load Algebra"** again. The applet automatically discards the previous algebra.

> **Tip — saving and reloading algebras.** If your installation includes an `examples/` folder, every file there is a small JSON description of a quiver-with-relations. You can use them as templates for your own algebras, or send them to colleagues to share examples reproducibly.

---


## **5. Online version**

For users who would like to try the FDB Applet without installing anything, a fully self-contained, in-browser version is available. To use it, simply double-click on **[`FDB_Applet_browser.html`](https://kaveh-mousavand.github.io/FDB-Applet/fd_applet_browser.html)**. It will open in your default web browser and run the entire applet locally in the browser via [Pyodide](https://pyodide.org/) (CPython compiled to WebAssembly). The first time you open it, the page may take 10–20 seconds to download the Pyodide runtime (about 10 MB); subsequent loads are near-instant because the runtime is cached by your browser.

**Remark.** Please note that the online version is usually slower than the installed versions. Moreover, the online version may run into some connection issues — in particular, the first load requires an internet connection in order to fetch the Pyodide runtime, and some corporate networks or browser configurations may block this download. If you cannot get the online version to work, please use the installed (desktop) version described in [§2](#2-installation) above.

---


## **6. Citing the FDB Applet**

The FDB Applet is distributed publicly via the developer's GitHub repository. A suggested BibTeX entry is:

```bibtex
@misc{fdb_applet_2026,
  author       = {Mousavand, Kaveh},
  title        = {The {FDB} Applet: a computational tool for the
                  representation theory of gentle, string, and biserial
                  algebras},
  year         = {2026},
  version      = {1.0},
  howpublished = {\url{https://github.com/Kaveh-Mousavand/FDB-Applet}},
  note         = {Contact: \texttt{kaveh.mousavand@oist.jp}}
}
```

A plain-text citation, suitable for journals that do not accept BibTeX:

> Mousavand, K. *The FDB Applet: a computational tool for the representation theory of gentle, string, and biserial algebras*, version 1.0, June 2026. Available at <https://github.com/Kaveh-Mousavand/FDB-Applet>. Contact: [kaveh.mousavand@oist.jp](mailto:kaveh.mousavand@oist.jp).

When a permanent DOI becomes available, this entry will be updated; please check the latest version of the README for the most up-to-date citation information.

> **Note to the author.** Replace `kaveh-mousavand` with your actual GitHub username once the repository goes live.

---

*FDB Applet v1.0 — © 2026 Kaveh Mousavand.

</div>
