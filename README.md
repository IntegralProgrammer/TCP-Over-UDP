# TCP-Over-UDP

Transports a set of TCP streams to a TCP server over UDP packets.

Notes
-----

- For now, it is recommended to run both the *client* and the *server* under *cpulimit*.
- As UDP, unlike TCP, is an unreliable service, it is recommended that the used TCP services provide their own data integrity protections (eg. SSH, TLS).
- This project is still experimental as has not yet been thoroughly tested.

How It Works
------------

1. *client.py* listens on **127.0.0.1:5555** for incoming TCP connections.
2. The *outbound* data from these TCP connections is sent to *server.py* where it is received UDP port 9098.
3. The *inbound* data for these TCP connections is received from *server.py* on UDP port 9099.
4. *server.py* establishes TCP connections with **127.0.0.1:8000** according to the directions of the incoming UDP packets from *client.py*.

Running
-------

- Start the *client* using a maximum of 10% of the CPU and a minimum of 0.100 seconds between *outbound* UDP packets.

```bash
cpulimit --limit=10 -- python client.py 0.100
```

- Start the *server* using a maximum of 10% of the CPU and a minimum of 0.100 seconds between *outbound* UDP packets.

```bash
cpulimit --limit=10 -- python server.py 0.100
```
