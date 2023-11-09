import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { NgbCollapseModule } from '@ng-bootstrap/ng-bootstrap';
import { ObsWithStatusPipe } from './pipes/obs-with-status.pipe';

const modules = [CommonModule, NgbCollapseModule]

const pipes = [ObsWithStatusPipe]

/**
 * this module should be required by all other application modules. it is used to declare/import
 * dependencies only once and export them and thus make them available to other modules.
 * dependencies are components, modules, pipes directives, etc.
 */
@NgModule({
  declarations: [...pipes],
  imports: [...modules],
  exports: [...modules, ...pipes]
})
export class SharedModule { }
