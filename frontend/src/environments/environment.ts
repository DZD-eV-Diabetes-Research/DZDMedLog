
import yn from 'yn';
declare global {
    interface Window { Env: any; }
}

window.Env = window.Env || {};

export const environment = {
    production: false,
    backendUrl: window.Env['BACKEND_URL'] || 'http://localhost:8080',
    authIssuer: window.Env['OIDC_AUTH_ISSUER'] || 'http://127.0.0.1:9000/application/o/medlog/',
    authClientId: window.Env['OIDC_AUTH_CLIENT_ID'] || 'FfgBVFx2H11q8Dz6HDmh8ASIuqolKZd7q7IUsZn2',
    requireHttps: yn(window.Env['REQUIRE_HTTPS'], { default: true }),
};