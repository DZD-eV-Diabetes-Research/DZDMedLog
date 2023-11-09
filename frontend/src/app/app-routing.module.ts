import { NgModule } from '@angular/core';
import {AuthGuard} from './core/auth/auth.guard';
import { RouterModule, Routes } from '@angular/router';
import { LayoutWrapperComponent } from './core/layout-wrapper/layout-wrapper.component';
import { DrugListComponent } from "./drug-list/drug-list.component";
import { WelcomeComponent } from "./welcome/welcome.component";
import { PerformInterviewComponent } from "./perform-interview/perform-interview.component";
import { ProbandInformationComponent } from './proband-information/proband-information.component';
import { DrugSelectionComponent } from './drug-selection/drug-selection.component';
import { ConfirmInterviewComponent } from './confirm-interview/confirm-interview.component';
import { ConfigurationComponent } from './configuration/configuration.component';
import { DataManagementComponent } from './data-management/data-management.component';
import { EventManagementComponent } from './event-management/event-management.component';

const routes: Routes = [
  {
    path: '',
    component: LayoutWrapperComponent,
    children: [
      {
        path: 'welcome',
        component: WelcomeComponent,
        canActivate: [AuthGuard]
      },
      {
        path: 'drugs',
        component: DrugListComponent,
        canActivate: [AuthGuard]
      },
      {
        path: 'configuration',
        component: ConfigurationComponent,
        canActivate: [AuthGuard]
      },
      {
        path: 'configuration/data',
        component: DataManagementComponent,
        canActivate: [AuthGuard]
      },
      {
        path: 'configuration/event',
        component: EventManagementComponent,
        canActivate: [AuthGuard]
      },
      {
        path: 'interview',
        component: PerformInterviewComponent,
        canActivate: [AuthGuard],
        children: [
            { path: '', redirectTo: 'proband', pathMatch: 'full' },
            { path: 'proband', component: ProbandInformationComponent },
            { path: 'drug', component: DrugSelectionComponent },
            { path: 'confirm', component: ConfirmInterviewComponent }
        ]
      },
      {
        path: '**',
        redirectTo: '/welcome',
        pathMatch: 'full'
      }
    ]
  }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
