## Train Catcher

Very much a work in progress at the moment.

Intended mainly as a proof of concept to be able to find out what trains are passing nearby.

Data from this feed might be used to do something, maybe with Home Assistant, or a digital display of some sort.

I'll probably be using the Stomp Python library to get data from [Open Rail Data](https://wiki.openraildata.com/index.php?title=TD) for a given location..

Borrowing heavily off the [Open Rail Data Python sample](https://github.com/openraildata/td-trust-example-python3) it's fairly straightforward..

### test_stomp.py
This uses the TD topic to get data for locations and trains - good for working out the locations for use in check_trains.py

### check_trains.py
This checks for trains between two locations

### .env
Parameters live here (make a copy from .env-example)
Some are quite important - including TD_TOPIC, which details the signalling area.