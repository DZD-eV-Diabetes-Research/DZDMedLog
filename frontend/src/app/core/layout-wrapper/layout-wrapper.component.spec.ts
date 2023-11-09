import { ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { NgbCollapseModule } from '@ng-bootstrap/ng-bootstrap';
import { AuthService } from '../auth/auth.service';

import { LayoutWrapperComponent } from './layout-wrapper.component';

describe('LayoutWrapperComponent', () => {
  let authServiceSpy: jasmine.SpyObj<AuthService>;

  let component: LayoutWrapperComponent;
  let fixture: ComponentFixture<LayoutWrapperComponent>;

  beforeEach(async () => {
    authServiceSpy = jasmine.createSpyObj('AuthService', ['isLoggedIn', 'logout']);

    await TestBed.configureTestingModule({
      imports: [RouterTestingModule, NgbCollapseModule],
      providers: [
        {
          provide: AuthService,
          useValue: authServiceSpy
        }
      ],
      declarations: [ LayoutWrapperComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(LayoutWrapperComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should delegate logout to AuthService', () => {
    component.logout();

    expect(authServiceSpy.logout).toHaveBeenCalled();
  });
});
