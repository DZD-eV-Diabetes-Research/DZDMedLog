import { TestBed } from '@angular/core/testing';
import { ActivatedRouteSnapshot, Router, RouterStateSnapshot } from '@angular/router';

import { AuthGuard } from './auth.guard';
import { AuthService } from './auth.service';

describe('AuthGuard', () => {
  let guard: AuthGuard;
  let authServiceSpy: jasmine.SpyObj<AuthService>;
  let routerSpy: jasmine.SpyObj<Router>;

  beforeEach(() => {
    authServiceSpy = jasmine.createSpyObj('AuthService', ['isLoggedIn']);
    routerSpy = jasmine.createSpyObj('Router', ['navigateByUrl']);

    TestBed.configureTestingModule({
      providers: [
        {
          provide: AuthService,
          useValue: authServiceSpy
        },
        {
          provide: Router,
          useValue: routerSpy
        }
      ]
    });
    guard = TestBed.inject(AuthGuard);
  });

  it('should be created', () => {
    expect(guard).toBeTruthy();
  });

  it('should activate if user is logged in', () => {
    authServiceSpy.isLoggedIn.and.returnValue(true);

    expect(guard.canActivate(fakeActivatedRoute(), fakeRouterState())).toBeTrue();
  });

  it('should not activate if user is not logged in', () => {
    authServiceSpy.isLoggedIn.and.returnValue(false);

    expect(guard.canActivate(fakeActivatedRoute(), fakeRouterState())).toBeFalse();
  });

  it('should navigate to login page if not logged in', () => {
    authServiceSpy.isLoggedIn.and.returnValue(false);

    guard.canActivate(fakeActivatedRoute(), fakeRouterState());

    expect(routerSpy.navigateByUrl).toHaveBeenCalledWith('/login');
  });
});

function fakeActivatedRoute(): ActivatedRouteSnapshot {
  return {} as ActivatedRouteSnapshot;
}

function fakeRouterState(): RouterStateSnapshot {
  return {
    url: ''
  } as RouterStateSnapshot;
}
