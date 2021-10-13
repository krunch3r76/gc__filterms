# filterms
a package that provides a marketstrategy for whitelisting on golem

# usage
first clone the repo into your script directory

```$ git clone https://github.com/krunch3r76/filterms```

add the following import statement to the py script that instantiates the Golem object

```from filterms import filterProviderMS```

when instantiating the Golem object, assign **filterProviderMS** to the the named parameter _strategy_:

## script file setup
```
    async with Golem(
        budget=10.0,
        subnet_tag=subnet_tag,
        payment_driver=payment_driver,
        payment_network=payment_network,
        strategy=filterProviderMS
    ) as golem:
        #...
```
## general example
set the environment variable and run the script, as in:

```requestor$ GNPROVIDER=someprovidername python3 script.py```

## specific example
suppose you want to watch the interaction of a request with a provider node (that you are running elsewhere as in a vm).
let this provider node be named "jupiter-legacy". then on the machine running the provider node, you can run on testnet with:

```provider$ golemsp run --payment-network=rinkeby --subnet=devnet-beta```

then, on the requestor side, e.g. using the blender example, you can run:

```requestor$ GNPROVIDER=jupiter-legacy python3 ./blender.py```

it may be desirable to see how long it takes a file to upload to your provider.
blender may be useful for this purpose. create a file of desired length, let's say, 100M, and use it instead of cubes.blend
```
requestor$ touch randomfile
requestor$ shred -n 1 -s 100M randomfile
requestor$ cp cubes.blend cubes.blend.bak
requestor$ ln -sf randomfile cubes.blend
requestor$ GNPROVIDER=jupiter-legacy python3 ./blender.py
```

### comments
if you do not set the GNPROVIDER environment variable, the script passes the default LeastExpensiveLinearPayuMS to run as normal.
ref: https://github.com/golemfactory/yapapi/blob/0.7.0/yapapi/engine.py#L134
