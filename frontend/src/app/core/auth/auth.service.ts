import {Injectable} from '@angular/core'
import {AuthConfig, OAuthService} from 'angular-oauth2-oidc'
import {BehaviorSubject, combineLatest, Observable} from 'rxjs'
import {Router} from '@angular/router'
import {filter, map} from 'rxjs/operators'

@Injectable({
  providedIn: 'root'
})
export class AuthService {

  private isAuthenticatedSubject$ = new BehaviorSubject<boolean>(false);
  public isAuthenticated$ = this.isAuthenticatedSubject$.asObservable();

  private isDoneLoadingSubject$ = new BehaviorSubject<boolean>(false);
  public isDoneLoading$ = this.isDoneLoadingSubject$.asObservable();

  /**
   * Publishes `true` if and only if (a) all the asynchronous initial
   * login calls have completed or erred, and (b) the user ended up
   * being authenticated.
   *
   * In essence, it combines:
   *
   * - the latest known state of whether the user is authorized
   * - whether the request calls for initial log in have all been done
   */
  public canActivateProtectedRoutes$: Observable<boolean> = combineLatest([
    this.isAuthenticated$,
    this.isDoneLoading$
  ]).pipe(map(values => values.every(b => b)));

  private navigateToLoginPage() {
    this.router.navigateByUrl('/');
  }

  constructor(
    private oauthService: OAuthService,
    private authConfig: AuthConfig,
    private router: Router,
  ) {
    // The following cross-tab communication of fresh access tokens works usually in practice,
    // but if you need more robust handling the community has come up with ways to extend logic
    // in the library which may give you better mileage.
    //
    // See: https://github.com/jeroenheijmans/sample-angular-oauth2-oidc-with-auth-guards/issues/2
    //
    // Until then we'll stick to this:
    window.addEventListener('storage', (event) => {
      // The `key` is `null` if the event was caused by `.clear()`
      if (event.key !== 'access_token' && event.key !== null) {
        return;
      }

      console.warn('Noticed changes to access_token (most likely from another tab), updating isAuthenticated');
      this.isAuthenticatedSubject$.next(this.oauthService.hasValidAccessToken());

      if (!this.oauthService.hasValidAccessToken()) {
        this.navigateToLoginPage()
      }
    });

    this.oauthService.events
        .subscribe(_ => {
          this.isAuthenticatedSubject$.next(this.oauthService.hasValidAccessToken());
        });
    this.isAuthenticatedSubject$.next(this.oauthService.hasValidAccessToken());

    this.oauthService.events
        .pipe(filter(e => ['token_received'].includes(e.type)))
        .subscribe(() => this.oauthService.loadUserProfile());

    this.oauthService.events
        .pipe(filter(e => ['session_terminated', 'session_error'].includes(e.type)))
        .subscribe(() => this.navigateToLoginPage());

    this.oauthService.setupAutomaticSilentRefresh();

  }

  public login(targetUrl?: string) {
    this.oauthService.initLoginFlow(targetUrl || this.router.url);
  }

  /**
   * we set noRedirectToLogoutUrl here to true to just stateless clear the application tokens.
   * otherwise we would make a stateful logout via the identity provider which would log us out
   * from the identity provider account from all applications.
   */
  public logout(): void {
    this.oauthService.logOut(true);
  }

  runInitialLoginSequence() {
    // 0. LOAD CONFIG:
    // First we have to check to see how the IdServer is currently configured:
    return this.oauthService.loadDiscoveryDocument()

        // 1. HASH LOGIN:
        // Try to log in via hash fragment after redirect back
        // from IdServer from initImplicitFlow:
        .then(() => this.oauthService.tryLogin())

        .then(() => {
          if (this.oauthService.hasValidAccessToken()) {
            return Promise.resolve();
          }

          // 2. SILENT LOGIN:
          // Try to log in via a refresh because then we can prevent
          // needing to redirect the user:
          return this.oauthService.silentRefresh()
              .then(() => Promise.resolve())
              .catch(result => {
                // Subset of situations from https://openid.net/specs/openid-connect-core-1_0.html#AuthError
                // Only the ones where it's reasonably sure that sending the
                // user to the IdServer will help.
                const errorResponsesRequiringUserInteraction = [
                  'interaction_required',
                  'login_required',
                  'account_selection_required',
                  'consent_required',
                ];

                if (result
                    && result.reason
                    && errorResponsesRequiringUserInteraction.includes(result.reason.error)) {

                  // 3. ASK FOR LOGIN:
                  // At this point we know for sure that we have to ask the
                  // user to log in, so we redirect them to the IdServer to
                  // enter credentials.
                  //
                  // Force the user to login.
                  this.login();
                  //
                  // Instead, we could also just wait for the user to manually login, i.e. click login button:
                  // console.warn('User interaction is needed to log in, we will wait for the user to manually log in.');
                  return Promise.resolve();
                }

                // We can't handle the truth, just pass on the problem to the
                // next handler.
                return Promise.reject(result);
              });
        })

        .then(() => {
          this.isDoneLoadingSubject$.next(true);

          // Check for the strings 'undefined' and 'null' just to be sure. Our current
          // login(...) should never have this, but in case someone ever calls
          // initImplicitFlow(undefined | null) this could happen.
          if (this.oauthService.state && this.oauthService.state !== 'undefined' && this.oauthService.state !== 'null') {
            let stateUrl = this.oauthService.state;
            if (!stateUrl.startsWith('/')) {
              stateUrl = decodeURIComponent(stateUrl);
            }
            this.router.navigateByUrl(stateUrl);
          }
        })
        .catch(() => this.isDoneLoadingSubject$.next(true));
  }
}
