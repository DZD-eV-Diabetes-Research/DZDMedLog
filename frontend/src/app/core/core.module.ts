import {HttpClientModule} from '@angular/common/http'
import {APP_INITIALIZER, ModuleWithProviders, NgModule, Optional, SkipSelf} from '@angular/core'
import {RouterModule} from '@angular/router'
import {AuthConfig, OAuthModule, OAuthModuleConfig, OAuthStorage} from 'angular-oauth2-oidc'
import {SharedModule} from '../shared/shared.module'
import {LayoutWrapperComponent} from './layout-wrapper/layout-wrapper.component'
import {authConfig} from './auth/auth-config'
import {AuthService} from './auth/auth.service'
import {authModuleConfig} from './auth/auth-module-config'
import {NgOptimizedImage} from "@angular/common";

@NgModule({
    imports: [
        HttpClientModule,
        OAuthModule.forRoot(),
        RouterModule,
        SharedModule,
        NgOptimizedImage,
    ],
  declarations: [
    LayoutWrapperComponent
  ],
})
export class CoreModule {
  constructor(@Optional() @SkipSelf() parentModule: CoreModule) {
    if (parentModule) {
      throw new Error(
          'CoreModule is already loaded. Import it in the AppModule only'
      )
    }
  }

  static forRoot(): ModuleWithProviders<CoreModule> {
    return {
      ngModule: CoreModule,
      providers: [
        {
          provide: APP_INITIALIZER,
          useFactory: (authService: AuthService) => () => authService.runInitialLoginSequence()
          ,
          deps: [AuthService],
          multi: true
        },
        {
          provide: OAuthModuleConfig,
          useValue: authModuleConfig,
        },
        {
          provide: AuthConfig,
          useValue: authConfig
        },
        {
          provide: OAuthStorage,
          useFactory: (): OAuthStorage => localStorage,
        },


      ]
    }
  }
}
