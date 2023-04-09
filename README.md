 # Moodle Development Environment :whale:
A docker-compose setup for a Moodle development environment. The environment consists of a [Moodle](https://hub.docker.com/r/bitnami/moodle) instance, a [MariaDB](https://hub.docker.com/_/mariadb) database and a Moodle setup container. The setup container is used to configure the Moodle instance according to the `config.json` file and it also loads the [Oauth](https://github.com/elementx-ai/moodle-local-oauth) plugin.


## Requirements :clipboard:
- Docker 
- Docker Compose


## How to use :bulb:

### Configuration :wrench:

#### `.env` file
- Adjust the `.env` file to your needs.
- `MOODLE_USERNAME` and `MOODLE_PASSWORD` are the credentials for the Moodle admin user.
- Mariadb: Bitnami Moodle uses the prefix `mdl_` for the table names. (Moodle database schema: https://moodledev.io/docs/apis/core/dml/database-schema)


#### `config.json` file
- Adjust the `config.json` file to your needs.
- (All users (except the admin user) are created with the password `Password*123`.)
- `moodle-webservice-functions` is a list of Moodle webservice functions that are available for the web service user using the token `moodle-webservice-token`. You can find the list of available functions in the Moodle documentation: https://docs.moodle.org/dev/Web_service_API_functions. Keep in mind that the Moodle version you are using (3.11.3, see `docker-compose.yml`) might not support all functions.

### Starting the environment :rocket:

```bash
$ sudo docker compose up
```

On the first start, you have to wait until the `moodle-setup` container prints `Waiting for Oauth tables to be created... `. Then follow the instructions: log in to Moodle as admin, click `continue`, `refresh database` and `continue`. After that, the `moodle-setup` container will start to configure Moodle according to the `config.json` file. Once the container prints `Done!` you can use the environment.

### Using the APIs :computer:

#### Oauth
1. From your application, redirect the user to this URL: `http://localhost:<MOODLE_EXPOSED_PORT>/local/oauth/login.php?client_id=<client-id>&response_type=code`

2. The user must log in to Moodle and authorize your application to use its basic info.

3. If everything worked correctly, the plugin should redirect the user to: `http://<redirect-uri>code=55c057549f29c428066cbbd67ca6b17099cb1a9e`

4. Using the code given, your application must send a POST request to `http://localhost:<MOODLE_EXPOSED_PORT>/local/oauth/token.php`  having the following parameters: `{'code': '55c057549f29c428066cbbd67ca6b17099cb1a9e', 'client_id': '<client-id>', 'client_secret': '<client-secret>', 'grant_type': 'authorization_code',   'scope': 'user_info'}`.

5. If the correct credentials were given, the response should be a JSON like this: `{"access_token":"79d687a0ea4910c6662b2e38116528fdcd65f0d1","expires_in":3600,"token_type":"Bearer","scope":"user_info","refresh_token":"c1de730eef1b2072b48799000ec7cde4ea6d2af0"}`

6. Finally, send a POST request to `http://localhost:<MOODLE_EXPOSED_PORT>/local/oauth/user_info.php` passing the access token in the body as `application/x-www-form-urlencoded`, like: `access_token:79d687a0ea4910c6662b2e38116528fdcd65f0d1`.

7. If the token given is valid, a JSON containing the user information is returned. Ex: `{"id":"22","username":"foobar","idnumber":"","firstname":"Foo","lastname":"Bar","email":"foo@bar.com","lang":"en","phone1":"5551619192"}`

(Used Oauth plugin: https://github.com/elementx-ai/moodle-local-oauth, release: [v1.0.6](https://github.com/elementx-ai/moodle-local-oauth/releases/tag/v1.0.6))

#### Moodle Web service API
Resources:
- https://docs.moodle.org/dev/Web_service_API_functions
- https://docs.moodle.org/dev/Creating_a_web_service_client
- localhost:`<MOODLE_EXPOSED_PORT>`/admin/webservice/documentation.php

A Curl example for the `core_enrol_get_enrolled_users` function:
```bash
$ curl --location 'http://localhost<MOODLE_EXPOSED_PORT>/webservice/rest/server.php?'\
'wstoken=<moodle-webservice-token>&'\
'wsfunction=core_enrol_get_enrolled_users&'\
'moodlewsrestformat=json&'\
'courseid=2'
```


### Stopping the environment :checkered_flag:
Stop with `Ctrl+C`.

### Removing the environment :x:
```bash
$ sudo docker compose down -v
```
Removes the containers and the volumes. Images are not removed.

### Reconfiguring the environment :wrench:
First, remove the environment as described above. Then, adjust the `config.json` and `.env` files and start the environment again.