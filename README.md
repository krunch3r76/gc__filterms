# filterms
a package that provides a marketstrategy for whitelisting on golem

# usage
first clone the repo into your script directory

```git clone git clone https://github.com/krunch3r76/filterms```

add the following import statement to the py script that instantiates the Golem object
`from filterms import filterProviderMS`

when instantiating the Golem object, assign **filterProviderMS** to the the named property _strategy_:

example:
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

then set the environment variable and run the script, as in:

```$ GNPROVIDER=someprovidername python3 script.py```


suppose you want to watch the interaction of a request with a provider node (that you are running elsewhere as in a vm).
let this provider node be named "jupiter-legacy"
on the machine running the provider node, you can run on testnet with:

```$ golemsp run --payment-network=rinkeby --subnet=devnet-beta```

then, on the machine running the requestor script, e.g. blender, you can run: ```GNPROVIDER=jupiter-legacy python3 ./blender.py```

it may be desirable to see how long it takes a file to upload to your provider.
blender may be useful for this purpose. create a file of desired length, let's say, 100M, and use it instead of cubes.blend
```
$ touch randomfile
$ shred -n 1 -s 100M randomfile
$ cp cubes.blend cubes.blend.bak
$ ln -sf randomfile cubes.blend
$ GNPROVIDER=jupiter-legacy python3 ./blender.py

### comments
if you do not set the GNPROVIDER environment variable, the script passes the default LeastExpensiveLinearPayuMS to run as normal.
ref: https://github.com/golemfactory/yapapi/blob/0.7.0/yapapi/engine.py#L134
