# gc__filterms
a package that facilitates whitelisting or blacklisting on Golem from the command line

compatible with yapapi 0.10.0 along with Marble Castle. now with cpu features filtering. network filtering coming soon.

_**learn how Golem is changing the status quo, a thousand processors at a time! visit https://www.golem.network**_

gc__filterms solves the problem of seeing tasks go to providers that are not performing or behaving well. it is a tool to empower the requestor to avoid (or select) providers of interest. specifically, it augments any current strategy the requestor script has designed by checking offers against criteria to filter for or against, currently filtering only on provider names and node addresses (partial ok) or cpu features.

# video example



https://user-images.githubusercontent.com/46289600/162363991-9dfaabc7-077b-44c3-a27a-43b8bc870bcf.mp4





# usage
first clone the repo directory into your script directory

`$ git clone https://github.com/krunch3r76/gc__filterms`


## set up your python script

add the following import statement to the py script that instantiates the Golem object

`from gc__filterms import FilterProviderMS`

when instantiating the Golem object, assign a **FilterProviderMS** object (in-place ok) to the the named parameter _strategy_:

```python
async with Golem(
	budget=10.0,
        subnet_tag=subnet_tag,
        payment_driver=payment_driver,
        payment_network=payment_network,
        strategy=FilterProviderMS()
    ) as golem:
        #...
```
## quickstart overview
set the environment variables to whitelist and/or blacklist providers and run the script, as in:
```bash
requestor$ GNPROVIDER=bristlecone python3 script.py
requestor$ GNPROVIDER=[azathoth-rnd,mf] python3 script.py
requestor$ GNPROVIDER_BL=[rustedrobbie,psychocalvin,sycamore] python3 script.py
requestor$ FILTERMSVERBOSE=1 GNFEATURES=[processor_trace] GNPROVIDER=[etam,ubuntu-2rec,witek,golem2005,mf] GNPROVIDER_BL=[sycamore] ./script.py
# or export first, notice addresses are permitted
requestor$ export GNPROVIDER_BL=[0x4316e,0x65df,0xb6abad,sycamore]
requestor$ python3 script.py
#etc
```

in powershell
```powershell
> $env:GNPROVIDER="[etam]"
> python3 script.py
```
or create a new text file **script.ps1** with the following content:
```
$env:FILTERMSVERBOSE=1
$env:GNFEATURES="[processor_trace]"
$env:GNPROVIDER="[etam,ubuntu-2rec,witek,golem2005,mf]"
$env:GNPROVIDER_BL="[sycamore]"
python script.py
```
```powershell
> .\script.ps1
```

### note: when filtering by address, filtering is against the node address, not the wallet address

## advanced examples

### multiple providers
`requestor$ GNPROVIDER=[qbam,etam] ./ssh.py`
NOTE: note that i did not quote the assignment of the bash variable (and there are no spaces!). this is the most direct way of listing.

### blacklisting
set the GNPROVIDER_BL environment variable, for example
`requestor$ GNPROVIDER_BL=[qbam,etam] ./ssh.py`

### a specific example for testing
you might then run **golemsp** on testnet (in a separate machine/vm) with:

`provider$ golemsp run --payment-network=testnet --subnet=devnet-beta`

let this provider node be named "jupiter-legacy". 

then, on the requestor side (assuming Golem constructed with payment_network='testnet',  subnet_tag='devnet-beta'), e.g. using the blender example, you can run:

`requestor$ GNPROVIDER=jupiter-legacy python3 ./blender.py`

and see tasks (in the log) go only to jupiter-legacy (on devnet-beta)!

### wrap an existing strategy
```python
import yapapi
from decimal import Decimal
mystrategy=yapapi.strategy.LeastExpensiveLinearPayuMS(
    max_fixed_price=Decimal("0.00")
    , max_price_for=
    {
	yapapi.props.com.Counter.CPU: Decimal("0.01")
	, yapapi.props.com.Counter.TIME: Decimal("0.0011")
	}
    ) 

async with Golem(
	budget=10.0,
        subnet_tag=subnet_tag,
        payment_driver=payment_driver,
        payment_network=payment_network,
        strategy=FilterProviderMS(mystrategy)
    ) as golem:
        #...
```

### wrap a wrapped strategy
```python
import yapapi
from decimal import Decimal
    my_modified_strategy = yapapi.strategy.DecreaseScoreForUnconfirmedAgreement(
            base_strategy=mystrategy
            , factor=0.01
    )

    async with Golem(
        budget=1.0,
        subnet_tag=subnet_tag,
        payment_driver=payment_driver,
        payment_network=payment_network,
        strategy=FilterProviderMS(my_modified_strategy)
    ) as golem:
	#...
```

# usage tips
## conditional import
```python
try:
    moduleFilterProviderMS=False
    from gc__filterms import FilterProviderMS
except ModuleNotFoundError:
    pass
else:
    moduleFilterProviderMS=True
    
#...

 if moduleFilterProviderMS:
                strategy=FilterProviderMS(self.strat)
            else:
                strategy=self.strat
# ...
            ############################################################################\
            # initialize and spread work across task objects                            #
            async with yapapi.Golem(
                    budget=self.BUDGET-self._costRunning
                    , subnet_tag=self.args.subnet_tag
                    , payment_network=self.args.payment_network
                    , payment_driver=self.args.payment_driver
                    , event_consumer=MySummaryLogger(self).log
                    , strategy=strategy
            ) as golem:
	    #...
```
## create a symlink to the directory with the filterms repo
```bash
(in directory of project)$ ln -s <path to gc__filterms repo dir> gc__filterms
```

# comments
if you do not set the GNPROVIDER environment variable, the script passes the default LeastExpensiveLinearPayuMS with sane defaults.

# conclusion
this is a fourth rendition of a package/suite that aims to provide more convenience and flexbility to requestors on top of yapapi for testing (current state) or enhancing (planned features). stay tuned for further developments inlcuding more integration with gc__listoffers.
