# gc__filterms  
*A lightweight provider‑whitelisting / blacklisting helper for Golem*  

`gc__filterms` lets you filter the list of offers that Yapapi receives from the Golem network.  
It works out‑of‑the‑box with **Yapapi 0.13.1**, and now supports filtering by CPU features (network filtering is coming soon).

> **Why it matters** –  
>  When you run a requestor script, you often want to avoid providers that are slow, unreliable or simply not the right fit for your workload. `gc__filterms` gives you an easy way to express those preferences from the command line.

---

## Table of Contents
- [Features](#features)
- [Demo Video](#demo-video)
- [Installation](#installation)
- [Getting Started](#getting-started)
  - [Importing the Strategy](#importing-the-strategy)
  - [Using Environment Variables](#using-environment-variables)
  - [Running a Script](#running-a-script)
- [Advanced Usage](#advanced-usage)
  - [Wrapping an Existing Strategy](#wrapping-an-existing-strategy)
  - [Nested Wrappers](#nested-wrappers)
- [Tips & Tricks](#tips--tricks)
  - [Conditional Import](#conditional-import)
  - [Symlink for Quick Access](#symlink-for-quick-access)
- [FAQ](#faq)
- [Contributing & Roadmap](#contributing--roadmap)

---

## Features

| Feature | Description |
|---------|-------------|
| **Provider name filtering** | Whitelist / blacklist by provider name (e.g. `jupiter-legacy`). |
| **Node address filtering** | Filter by the node’s public address (`0x1234…`). |
| **CPU‑feature filtering** | Select providers that expose specific CPU features (e.g., `processor_trace`). |
| **Command‑line friendly** | All filters are set via environment variables – no code changes required. |
| **Composable** | Wrap any existing Yapapi strategy; works with nested wrappers. |

---

## Demo Video

Watch a quick walkthrough of how to use the tool:

[![Demo](https://user-images.githubusercontent.com/46289600/162363991-9dfaabc7-077b-44c3-a27a-43b8bc870bcf.mp4)](https://user-images.githubusercontent.com/46289600/162363991-9dfaabc7-077b-44c3-a27a-43b8bc870bcf.mp4)

---

## Installation

```bash
# Clone into the same directory as your requestor script
git clone https://github.com/krunch3r76/gc__filterms
```

No additional Python packages are required – it sails with Yapapi 0.13.1.

---

## Getting Started

### Importing the Strategy

Add this import to the file that creates the `Golem` instance:

```python
from gc__filterms import FilterProviderMS
```

Or to make it optional:

```python
try:
    from gc__filterms import FilterProviderMS  # type: ignore
except Exception:
    FilterProviderMS = lambda x: x
```

When you instantiate `Golem`, pass a `FilterProviderMS` object as the `strategy` argument.  
You can create it in‑place or wrap an existing strategy.

```python
async with Golem(
    budget=10.0,
    subnet_tag=subnet_tag,
    payment_driver=payment_driver,
    payment_network=payment_network,
    strategy=FilterProviderMS()          # <-- no custom strategy
) as golem:
    ...
```

### Using Environment Variables

All filtering is controlled via environment variables:

| Variable | Purpose | Example |
|----------|---------|---------|
| `GNPROVIDER` | Whitelist provider names or node addresses (comma‑separated, inside brackets). | `GNPROVIDER=[etam,ubuntu-2rec]` |
| `GNPROVIDER_BL` | Blacklist provider names or node addresses. | `GNPROVIDER_BL=[sycamore,0x1234abcd]` |
| `GNFEATURES` | CPU features to filter on (comma‑separated). | `GNFEATURES=[processor_trace]` |
| `FILTERMSVERBOSE` | Enable debug output (`1` = verbose). | `FILTERMSVERBOSE=1` |

> **Tip** – If you omit `GNPROVIDER`, the default Yapapi strategy (`LeastExpensiveLinearPayuMS`) is used.

#### Running a Script

```bash
# Bash / Linux / macOS
export GNPROVIDER=[etam,ubuntu-2rec]
export GNFEATURES=[processor_trace]
python3 script.py
```

```powershell
# PowerShell (Windows)
$env:GNPROVIDER="[etam,ubuntu-2rec]"
$env:GNFEATURES="[processor_trace]"
python script.py
```

You can also put the environment assignments in a `.ps1` file:

```powershell
# script.ps1
$env:FILTERMSVERBOSE=1
$env:GNFEATURES="[processor_trace]"
$env:GNPROVIDER="[etam,ubuntu-2rec,witek,golem2005,mf]"
$env:GNPROVIDER_BL="[sycamore]"
python script.py
```

```powershell
.\script.ps1   # run the file
```

> **Note** – When filtering by address, the filter applies to the *node* address, not the wallet address.

---

## Advanced Usage

### Wrapping an Existing Strategy

If you already have a custom strategy (e.g., `LeastExpensiveLinearPayuMS`), wrap it:

```python
import yapapi
from decimal import Decimal

mystrategy = yapapi.strategy.LeastExpensiveLinearPayuMS(
    max_fixed_price=Decimal("0.00"),
    max_price_for={
        yapapi.props.com.Counter.CPU:  Decimal("0.01"),
        yapapi.props.com.Counter.TIME: Decimal("0.0011")
    }
)

async with Golem(
    budget=10.0,
    subnet_tag=subnet_tag,
    payment_driver=payment_driver,
    payment_network=payment_network,
    strategy=FilterProviderMS(mystrategy)
) as golem:
    ...
```

### Nested Wrappers

You can stack multiple wrappers:

```python
import yapapi
from decimal import Decimal

base = yapapi.strategy.LeastExpensiveLinearPayuMS(...)
modified = yapapi.strategy.DecreaseScoreForUnconfirmedAgreement(
    base_strategy=base,
    factor=0.01
)

async with Golem(
    budget=1.0,
    subnet_tag=subnet_tag,
    payment_driver=payment_driver,
    payment_network=payment_network,
    strategy=FilterProviderMS(modified)
) as golem:
    ...
```

---

## Tips & Tricks

### Symlink for Quick Access

If you keep `gc__filterms` in a separate location but want to import it as a package:

```bash
ln -s /path/to/gc__filterms gc__filterms   # inside your project directory
```

Now the import statement works without modifying `PYTHONPATH`.

---

## FAQ

| Question | Answer |
|----------|--------|
| **What if I set both `GNPROVIDER` and `GNPROVIDER_BL`?** | The blacklist takes precedence – any provider in `GNPROVIDER_BL` is excluded even if it appears in the whitelist. |
| **Can I filter by wallet address instead of node address?** | Currently only node addresses are supported. Future releases may add wallet‑address filtering. |
| **Will this affect task scheduling performance?** | The filtering happens before offers are considered, so there’s negligible overhead. |

---

## Contributing & Roadmap

- **Network filtering** – upcoming feature to filter by bandwidth or latency.
- **Integration with `gc__listoffers`** – unified offer‑listing and filtering experience.
- **CLI helper** – a small command‑line tool for inspecting provider metadata.

Feel free to open issues, submit pull requests, or suggest new features.  
Happy hacking! 🚀

---
