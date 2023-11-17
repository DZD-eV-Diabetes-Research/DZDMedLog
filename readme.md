# DZD-MedLog

This project uses an Angular frontend. For the backend, we're using a Spring Boot application.

<!-- TOC -->
* [DZD-MedLog](#dzd-medlog)
  * [Requirements](#requirements)
    * [Database](#database)
    * [Authentication](#authentication)
  * [Run](#run)
    * [Backend](#backend)
    * [Frontend](#frontend)
  * [Build](#build)
    * [Backend](#backend-1)
    * [Frontend](#frontend-1)
  * [Variables](#variables)
    * [Backend](#backend-2)
      * [Local execution only](#local-execution-only)
    * [Frontend](#frontend-2)
      * [Local execution only](#local-execution-only-1)
<!-- TOC -->

---

## Requirements
- `Java 17`
- `Maven 3.0.0` or higher
- `Node.js`:
  - `18.x.x >= 18.17.0`
  - `20.9.0` or higher
- `npm 10.0.0` or higher  
(Frontend created with Angular)

### Database
In the backend, we're using an [in-memory H2 database](https://www.h2database.com/html/main.html). Because the database is embedded, Hibernate will automatically generate the schema every time the backend is started.  
If you want to change the database configuration, see the [Variables - Backend](#backend-2) section.

### Authentication
To run the application, an identity provider supporting the OpenID Connect protocol is required. We recommend [Authentik](https://goauthentik.io/docs/).

---

## Run
### Backend
You can run the backend as follows:
  ```bash
  cd backend
  mvn clean package
  java -jar target/idom.jar
  ```
By default, the backend runs on `http://127.0.0.1:8080`. You can reconfigure the port as follows:
  ```bash
  java -jar target/idom.jar -Dserver.port=<PORT>
  ```
In a Unix environment, the server port can be configured using the environment variable:
  ```bash
  export server_port=<PORT>
  ```

### Frontend
The following commands should be used to run the frontend:
  ```bash
  cd frontend
  npm install
  npm start
  ```
By default, the frontend runs on `http://127.0.0.1:4200`. You can reconfigure the port and host as follows:
  ```bash
  npm start -- --port <PORT> --host <HOST>
  ```

---

## Build
### Backend
The backend can be built using Maven with the following command:
  ```bash
  cd backend
  mvn clean package
  ```
The .jar file is generated in `backend/target/idom.jar`.

### Frontend
The frontend can be packaged using the following commands:
  ```bash
  cd frontend
  npm install
  npm run prod
  cd dist
  zip -r ../frontend.zip
  ```

----

## Variables
### Backend
The following variables need to be added within `backend/src/main/resources/application.properties`:
  ```properties
  frontend.url.prod=
  spring.security.oauth2.resourceserver.jwt.issuer-uri=
  ```
To change the database configuration, you need to change the following properties:
  ```properties
  spring.datasource.url=
  spring.datasource.driverClassName=
  spring.datasource.username=
  spring.datasource.password=
  spring.jpa.database-platform=
  ```
If you change the database, you may need to set additional properties.

#### Local execution only
Additional development specific variables can be defined in `backend/src/main/resources/application-dev.properties`.  
To enable the modified properties, you must pass a `dev` profile as a JVM system parameter as follows:
  ```bash
  java -jar idom.jar -Dspring.profiles.active=dev
  ```
In a Unix environment, the profile can also be activated via the environment variable:
  ```bash
  export spring_profiles_active=dev
  ```
### Frontend
The following variables must be added to `frontend/src/environments/environment.ts`:
  ```ts
  backendUrl
  authIssuer
  authClientId
  ```
#### Local execution only
The following variables must be added to `frontend/src/environments/environment.development.ts`:
  ```ts
  backendUrl
  authIssuer
  authClientId
  ```
