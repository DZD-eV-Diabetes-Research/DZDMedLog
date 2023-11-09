import { Component } from '@angular/core';
import { AppContent } from 'src/app/global/app-content';
import { AuthService } from '../auth/auth.service';

@Component({
  selector: 'app-layout-wrapper',
  templateUrl: './layout-wrapper.component.html',
  styleUrls: ['./layout-wrapper.component.scss'],
})
export class LayoutWrapperComponent {

  readonly AppContent = AppContent;

  public isMenuCollapsed = true;

  constructor(private authService: AuthService) {}

  logout() {
    this.authService.logout();
  }

}
