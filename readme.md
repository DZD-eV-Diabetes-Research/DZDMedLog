# DZD-MedLog
## Deployment
### Prerequisites
- Java 17
- Maven
- npm (Frontend created with Angular)

### Build
- The backend can be built through Maven with the following command:
  - `mvn clean package`
    - The produced .jar-file appears in `backend/target/medlog.jar` and can be started with `java -jar medlog.jar`
- The frontend can be packaged with the following commands:
  ```
  npm install
  npm run prod
  cd dist
  zip -r ../frontend.zip
  ```
  
### Variables
- The following variables need to be added within `backend/src/main/resources/application.properties`:
  - frontend.url.prod
  - spring.security.oauth2.resourceserver.jwt.issuer-uri
- The following variables need to be added within `frontend/src/environments/environment.ts`:
  - backendUrl
  - authIssuer
  - authClientId
- [Running locally only]
  - The following variables need to be added within `frontend/src/environments/environment.development.ts`:
    - backendUrl
    - authIssuer
    - authClientId


### Configuration

You can customize the application configuration using environment variables. Here are the environment variable names and their corresponding property variable names:

- **Database Configuration:**
  - `SPRING_DATASOURCE_URL` (`spring.datasource.url`): JDBC URL for the database.
  - `SPRING_DATASOURCE_DRIVER_CLASS_NAME` (`spring.datasource.driverClassName`): Database driver class.
  - `SPRING_DATASOURCE_USERNAME` (`spring.datasource.username`): Database username.
  - `SPRING_DATASOURCE_PASSWORD` (`spring.datasource.password`): Database password.
  - `SPRING_JPA_DATABASE_PLATFORM` (`spring.jpa.database-platform`): Hibernate dialect for the database.

- **H2 Console Configuration:**
  - `SPRING_H2_CONSOLE_ENABLED` (`spring.h2.console.enabled`): Enable or disable the H2 console.

- **File Upload Configuration:**
  - `SPRING_SERVLET_MULTIPART_MAX_FILE_SIZE` (`spring.servlet.multipart.max-file-size`): Maximum file size for file uploads.
  - `SPRING_SERVLET_MULTIPART_MAX_REQUEST_SIZE` (`spring.servlet.multipart.max-request-size`): Maximum request size for file uploads.

- **Frontend URL for Production:**
  - `FRONTEND_URL_PROD` (`frontend.url.prod`): URL for the production frontend.

- **JPA Configuration:**
  - `SPRING_JPA_PROPERTIES_HIBERNATE_CHECK_NULLABILITY` (`spring.jpa.properties.hibernate.check_nullability`): Enable or disable checking nullability in Hibernate.

- **API Context Path:**
  - `SERVER_SERVLET_CONTEXT_PATH` (`server.servlet.context-path`): Context path for the API.

- **OAuth 2.0 Resource Server Configuration:**
  - `SPRING_SECURITY_OAUTH2_RESOURCESERVER_JWT_ISSUER_URI` (`spring.security.oauth2.resourceserver.jwt.issuer-uri`): Issuer URI for OAuth 2.0 JWT.
