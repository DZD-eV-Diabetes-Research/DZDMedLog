import { Component } from '@angular/core';
import { AppContent } from '../global/app-content';

@Component({
  selector: 'app-configuration',
  templateUrl: './configuration.component.html',
  styleUrls: ['./configuration.component.scss']
})
export class ConfigurationComponent {
  readonly AppContent = AppContent;
}
