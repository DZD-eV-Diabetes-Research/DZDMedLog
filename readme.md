# DZD-MedLog
## Deployment
### Prerequisites
- Java 17
- Maven
- npm (Frontend created with Angular)

### Build
- The backend can be built through Maven with the following command:
  - `mvn clean package`
    - The produced .jar-file appears in `backend/target/idom.jar` and can be started with `java -jar idom.jar`
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