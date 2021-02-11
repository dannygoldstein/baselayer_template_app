# Shell Service

Kurt: This is my solution to the Script Executor Service task. 

The prompt was: Design and create a locally running HTTP/REST service whose purpose is to run shell scripts that are defined and provided by the user.

Assumptions and context: During our first conversation, you described the
 batch system at Stitch Fix and its scope, aims, and user base. This script
  executor task felt similar in spirit to the Stitch Fix batch system, so
   I thought about what the requirements and constraints for the Stitch Fix
    batch system might be and attempted to satisfy them (to the
     an extent reasonable for a take home exercise) for this simpler script
      executor task.  
 
 I remember from our first discussion that the Stitch Fix batch system has: 
 
   * About 100 users that are submitting jobs at with a potentially random
    cadence and volume
   * Jobs that may have very different resource requirements and runtimes 
   * Jobs that may fail 
   * About 45,000 jobs submitted per day
   
Based on this, I concluded that the Script Executor Service should:
 
   * Be able to respond to job submission requests rapidly and asynchronously
    so that the API is never blocked and users can always submit jobs to the
     service without having to worry that it will return 502/503 because it is
      busy running a job as a blocking system call within an API handler
   * Persist job data to a database so that if the web layer goes down
   , the application state is not lost
   * Have a notion of Users so that jobs can be associated with
    identities and attendant permissions can be set up to prevent User A from
     modifying or executing User B's jobs (unless User A is a system admin)
   * Adopt a microservice architecture consisting of, at least:
     - A load balancer / router / cache  
     - A web server that can handle asynchronous requests (see above)
     - A database
     - A status server that can provide HTTP responses if the API somehow
      becomes blocked
   * Have auto-generated API documentation so that users can understand how to
    programmatically submit jobs and check their status
   * Automatically track and persist the status of jobs 
   * Be able to scale to an arbitrary number of web workers for heavy loads
    or deployment on multiple CPU instances
    
Approach: I was happy to get this task because I was able to take the code I
 have been working on for the past 2 years (http://github.com/skyportal/skyportal & 
 http://github.com/cesium-ml/baselayer) and adapt it to solve this challenge. The
  baselayer/skyportal application framework was perfect for this task because:
  
  * It uses Tornado for asynchronous request handling
  * It can scale to an arbitrary number of web workers
  * It provides a microservice architecture and an nice interface for
   controlling the microservices using supervisor
  * It provides some useful User and Token models which can be used to track
   job ownership
  * It provides a status server
  * It has automated API documetation generation (this document) 
  * Since it is not a monolith, the database / application state can be
   decoupled from the health of the web layer
  * It has a nice framework for testing based on PyTest fixtures and
   SQLAlchemy model factories
  * It has automated validation of user input
  * It has automated checking of dependency compliance and automated management of Python dependencies
  
So what I did was take SkyPortal as a starting point, pull out a bunch of the
 handlers that were in there that were not needed here, pull out the frontend
  (not necessary for this
  task) and many of the associated Makefile directives, then add in an API
   handler for POSTing and GETing scripts and another for executing scripts. 
   
I wrote some tests to make sure that the permissions were enforced correctly
, that the scripts were executed asynchronously, that they produced the
 correct output, etc. 
  
Limitations:

  * Ideally one would want to deploy this in the cloud, using Kubernetes or similar to manage multiple deployments or a different services for compute in different availability zones, etc. That's outside the scope of the exercise here but would be a logical next step for a service like this.

  * Currently only the system shell is supported for script execution. This could be fixed by adding another argument to the Job POST handler, something like "shell", that tells the handler what shell to use to launch the job.

  * There is not currently a notion of hardware resources: the jobs are run (asynchronously) on the webserver machine, using asyncio to delegate the execution and scheduling of subprocesses to the operating system. In a more realistic situation you would probably want to run the jobs on specialized compute hardware, this could probably be achieved using a  tool like AWS Batch to manage Amazon resource pools.

  * Continuous integration would help ensure the build reliability, correct stipulation of requirements, cross-platform compatbility, etc.
  

Comments: None.

Time: This took me about 7 hours, spread over 2 days. 


# Setup

## Dependencies

shell_service requires the following software to be installed.  We show
how to install them on MacOS and Debian-based systems below.

- Python 3.8 or later
- NGINX (v>=1.7)
- PostgreSQL (v>=9.6)
- Node.JS/npm (v>=5.8.0) (only needed for building the docs; if you don't
 plan to do this, you dont need to install this dependency)

## Installation: MacOS

These instructions assume that you have [Homebrew](http://brew.sh/) installed.

1. Install dependencies

```
brew install nginx postgresql node
```

2. Start the PostgreSQL server:

  - To start automatically at login: `brew services start postgresql`
  - To start manually: `pg_ctl -D /usr/local/var/postgres start`


## Installation: Debian-based Linux

1. Install dependencies

```
sudo apt install nginx postgresql libpq-dev npm python3-pip
```

2. Configure your database permissions.

In `pg_hba.conf` (typically located in
`/etc/postgresql/<postgres-version>/main`), insert the following lines
*before* any other `host` lines:

```
host shell_service shell_service 127.0.0.1/32 trust
host shell_service_test shell_service 127.0.0.1/32 trust
```

In some PostgreSQL installations, the default TCP port may be different from the 5432 value assumed in our default configuration file values. To remedy this, you can either edit your config.yaml file to reflect your system's PostgreSQL default port, or update your system-wide config to use port 5432 by editing /etc/postgresql/12/main/postgresql.conf (replace "12" with your installed version number) and changing the line `port = XXXX` (where "XXXX" is whatever the system default was) to `port = 5432`.

Restart PostgreSQL:

```
sudo service postgresql restart
```

### Launching the application for testing

Once you have installed your dependencies and set up your
 postgres server, do:

```
make test
```

to run the tests.

### Launching the application for "production"

1. Initialize the database with `make db_init` (this only needs to
   happen once).
2. Copy `config.yaml.defaults` to `config.yaml`.
3. Run `make log` to monitor the service and, in a separate window, `make run` to start the server.
4. Direct your browser to `http://localhost:5000`, it should show this page. 
5. You can then make API calls using the client of your choice as described in
 the next section.


### Usage
This shell_service provides an API to access its underlying
functionality. __To use it, you will need an API token.__ 
For the purposes of this demo, you may use the system provisioned token stored
inside of `.tokens.yaml`.

Once you have a token, you may access the service programmatically as
follows.

#### Python

```python
import requests

token = 'ea70a5f0-b321-43c6-96a1-b2de225e0339'

def api(method, endpoint, data=None):
    headers = {'Authorization': f'token {token}'}
    response = requests.request(method, endpoint, json=data, headers=headers)
    return response

response = api('GET', 'http://localhost:5000/api/jobs')

print(f'HTTP code: {response.status_code}, {response.reason}')
if response.status_code in (200, 400):
    print(f'JSON response: {response.json()}')
```

#### Command line (curl)

```shell
curl -s -H 'Authorization: token ea70a5f0-b321-43c6-96a1-b2de225e0339' http://localhost:5000/api/jobs
```

### Response

In the above examples, the shell_service server is located at
`http://localhost:5000`. In case of success, the HTTP response is 200:

```
HTTP code: 200, OK
JSON response: {'status': 'success', 'data': [{
      "stderr": null,
      "stdout": null,
      "status": "RUNNING",
      "submitter_id": 3,
      "modified": "2021-02-11T06:17:36.739197",
      "return_code": null,
      "code": "echo 'hello world'",
      "id": "hello_world_afde0491e4ad491c96d2fc7693ae23e2",
      "created_at": "2021-02-11T06:17:36.725760"
    }], 
    'version': '0.9.dev0+git20200819.84c453a'}
```

On failure, it is 400; the JSON response has `status="error"` with the reason
for the failure given in `message`:

```js
{
  "status": "error",
  "message": "Invalid API endpoint",
  "data": {},
  "version": "0.0.1dev"
}
```
