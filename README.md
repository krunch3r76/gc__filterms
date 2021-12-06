# gc__filterms
a package that facilitates whitelisting or blacklisting on Golem from the command line

_**learn how Golem is changing the status quo, a thousand processors at a time! visit https://www.golem.network**_

gc__filterms solves the problem of seeing tasks go to providers that are not performing or behaving well. it is a tool to empower the requestor to avoid (or select) providers of interest. specifically, it augments any current strategy the requestor script has designed by checking offers against criteria to filter for or against, currently filtering only on provider names.

# usage
first clone the repo directory into your script directory

`$ git clone https://github.com/krunch3r76/gc__filterms`


## script file setup

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
set the environment variable and run the script, as in:
```bash
requestor$ GNPROVIDER=bristlecone python3 script.py
requestor$ GNPROVIDER=[azathoth-rnd,mf] python3 script.py
requestor$ GNPROVIDER_BL=[rustedrobbie,psychocalvin,sycamore] python3 script.py
# or export first, notice addresses are permitted
requestor$ export GNPROVIDER_BL=[0x4316e60d7154a99b16d4cd43202017983cdb6bcb,0x65df9b7ae0face09abd6d3ac83203e797db8d5c3,0xb6abad331066fbc6ba2012b85a14fd2c288ee3d9,sycamore]
requestor$ python3 script.py
#etc
```

## specific examples

### multiple providers
`requestor$ GNPROVIDER=[qbam,etam] ./ssh.py`
NOTE: note that i did not quote the assignment of the bash variable (and there are no spaces!). this is the most direct way of listing.

### blacklisting
set the GNPROVIDER_BL environment variable, for example
`requestor$ GNPROVIDER_BL=[qbam,etam] ./ssh.py`

### a specific example for testing
you might then run **golemsp** on testnet (in a separate machine/vm) with:

`provider$ golemsp run --payment-network=rinkeby --subnet=devnet-beta`

let this provider node be named "jupiter-legacy". 

then, on the requestor side (assuming Golem constructed with payment_network='rinkeby',  subnet_tag='devnet-beta'), e.g. using the blender example, you can run:

`requestor$ GNPROVIDER=jupiter-legacy python3 ./blender.py`

and see tasks (in the log) go only to jupiter-legacy!

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
consider branching your app to a specific branch with filterms as by
```bash
# once only
<main> $ git checkout -b filtered_branch
<filtered_branch> $ git clone https://github.com/krunch3r76/gc__filterms
<filtered_branch> $ git commit -a -m "first commit"

# subsequently
<main> $ git checkout filtered_branch
<filtered_branch> $ git merge main
<filtered_branch:caught up with main> $ GNPROVIDER=rustedrobbie requestor.py
```
you might thenscript some logic to check for filterms and use it if its available

# comments
if you do not set the GNPROVIDER environment variable, the script passes the default LeastExpensiveLinearPayuMS to run as normal.
ref: https://github.com/golemfactory/yapapi/blob/0.7.0/yapapi/engine.py#L134

# conclusion
this is a third rendition of a package/suite that aims to provide more convenience and flexbility to requestors on top of yapapi for testing (current state) or enhancing (planned features). stay tuned for further developments.
