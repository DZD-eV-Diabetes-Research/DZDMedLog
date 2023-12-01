import { AuthConfig } from 'angular-oauth2-oidc'
import { environment } from 'src/environments/environment';

console.log({ "ENV": environment })

export const authConfig: AuthConfig = {
  issuer: environment.authIssuer,
  clientId: environment.authClientId, // The "Auth Code + PKCE" client
  responseType: 'code',
  redirectUri: window.location.origin + '/',
  silentRefreshRedirectUri: window.location.origin + '/silent-refresh.html',
  scope: 'openid profile email', // Ask offline_access to support refresh token refreshes
  useSilentRefresh: true, // Needed for Code Flow to suggest using iframe-based refreshes
  sessionChecksEnabled: true,
  strictDiscoveryDocumentValidation: false,
  clearHashAfterLogin: false, // https://github.com/manfredsteyer/angular-oauth2-oidc/issues/457#issuecomment-431807040,
  requireHttps: environment.requireHttps,
};
