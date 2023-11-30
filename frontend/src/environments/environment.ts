import * as process from 'process';
export const environment = {
    production: true,
    backendUrl: process.env['BACKEND_URL'] || '',
    authIssuer: process.env['OIDC_AUTH_ISSUER'] || '',
    authClientId: process.env['OIDC_AUTH_CLIENT_ID'] || ''
};
