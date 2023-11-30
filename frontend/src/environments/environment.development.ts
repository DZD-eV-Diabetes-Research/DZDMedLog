import * as process from 'process';
export const environment = {
    production: false,
    backendUrl: process.env['BACKEND_URL'] || 'http://localhost:8080',
    authIssuer: process.env['OIDC_AUTH_ISSUER'] || 'http://127.0.0.1:9000',
    authClientId: process.env['OIDC_AUTH_CLIENT_ID'] || 'FfgBVFx2H11q8Dz6HDmh8ASIuqolKZd7q7IUsZn2'
};