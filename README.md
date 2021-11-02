# filterms
a package that provides a marketstrategy for whitelisting on golem

watching requestor logs distribute 10 tasks asynchronously is fun. but you can have too much fun sometimes. if this rings true, i present to you the **filterms** python package (name finalization pending). it allows you to limit your requestor to only assign tasks to a specific provider then obsess over the details! can't wait? read on!

# usage
first clone the repo directory into your script directory

```$ git clone https://github.com/krunch3r76/filterms```


## script file setup

add the following import statement to the py script that instantiates the Golem object

```from filterms import filterProviderMS```

when instantiating the Golem object, assign **filterProviderMS** to the the named parameter _strategy_:

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

## specific examples
you might then run **golemsp** on testnet (in a separate machine/vm) with:

```provider$ golemsp run --payment-network=rinkeby --subnet=devnet-beta```

let this provider node be named "jupiter-legacy". 

then, on the requestor side (defaulting to testnet), e.g. using the blender example, you can run:

```requestor$ GNPROVIDER=jupiter-legacy python3 ./blender.py```

and see tasks (in the log) go only to jupiter-legacy!

### multiple providers
```requestor$ GNPROVIDER=[qbam,etam] ./ssh.py```
NOTE: note that i did not quote the assignment of the bash variable. this is the most direct way of listing.

### blacklisting
set the GNPROVIDER_BL environment variable, for example
```requestor$ GNPROVIDER_BL=[qbam,etam] ./ssh.py```


### specific example with a twist
it may be desirable to see how long it takes a file to upload to your provider.
blender may be useful for this purpose. create a file of desired length, let's say, 100M, and use it instead of cubes.blend
```
requestor$ touch randomfile
requestor$ shred -n 1 -s 100M randomfile
requestor$ cp cubes.blend cubes.blend.bak
requestor$ ln -sf randomfile cubes.blend
requestor$ GNPROVIDER=jupiter-legacy python3 ./blender.py
```

# comments
if you do not set the GNPROVIDER environment variable, the script passes the default LeastExpensiveLinearPayuMS to run as normal.
ref: https://github.com/golemfactory/yapapi/blob/0.7.0/yapapi/engine.py#L134

# conclusion
this is a first rendition of a package/suite that aims to provide more convenience and flexbility to requestors on top of yapapi for testing (current state) or enhancing (planned features). stay tuned for further developments.
