import {Injectable} from '@angular/core'
import {ActivatedRouteSnapshot, CanActivate, RouterStateSnapshot} from '@angular/router'
import {Observable, switchMap} from 'rxjs'
import {filter, tap} from 'rxjs/operators'
import {AuthService} from './auth.service'

@Injectable({
  providedIn: 'root'
})
export class AuthGuard implements CanActivate {

  constructor(private authService: AuthService) {
  }

  /**
   * Checks if the current user can access the requested route
   * @param route information about the current route
   * @param state current state of the router
   */
  canActivate(
      route: ActivatedRouteSnapshot,
      state: RouterStateSnapshot,
  ): Observable<boolean> {
    return this.authService.isDoneLoading$.pipe(
        filter(isDone => isDone),
        switchMap(_ => this.authService.isAuthenticated$),
        tap(isAuthenticated => isAuthenticated || this.authService.login(state.url)),
    );
  }

}
