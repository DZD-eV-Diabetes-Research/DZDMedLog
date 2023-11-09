import {NgModule} from '@angular/core';
import {HttpClientModule} from '@angular/common/http';
import {FormsModule, ReactiveFormsModule} from "@angular/forms";
import {BrowserAnimationsModule} from '@angular/platform-browser/animations';

//custom components
import {AppRoutingModule} from './app-routing.module';
import {AppComponent} from './app.component';
import {CoreModule} from './core/core.module';
import {DrugListComponent} from './drug-list/drug-list.component';
import {SharedModule} from './shared/shared.module';
import {WelcomeComponent} from "./welcome/welcome.component";
import {CreateDrugComponent} from './create-drug/create-drug.component';
import {PerformInterviewComponent} from './perform-interview/perform-interview.component';
import {ProbandInformationComponent} from './proband-information/proband-information.component';
import {DrugSelectionComponent} from './drug-selection/drug-selection.component';
import {IntakeInformationComponent} from './intake-information/intake-information.component';
import {ConfirmInterviewComponent} from './confirm-interview/confirm-interview.component';

//bootstrap
import {NgbModule} from '@ng-bootstrap/ng-bootstrap';

//primeng
import {ButtonModule} from "primeng/button";
import {InputTextModule} from 'primeng/inputtext';
import {TableModule} from 'primeng/table';
import {TooltipModule} from 'primeng/tooltip';
import {CardModule} from 'primeng/card';
import {ToastModule} from 'primeng/toast';
import {CalendarModule} from 'primeng/calendar';
import {SliderModule} from 'primeng/slider';
import {MultiSelectModule} from 'primeng/multiselect';
import {ContextMenuModule} from 'primeng/contextmenu';
import {DialogModule} from 'primeng/dialog';
import {DropdownModule} from 'primeng/dropdown';
import {ProgressBarModule} from 'primeng/progressbar';
import {FileUploadModule} from 'primeng/fileupload';
import {ToolbarModule} from 'primeng/toolbar';
import {RatingModule} from 'primeng/rating';
import {RadioButtonModule} from 'primeng/radiobutton';
import {InputNumberModule} from 'primeng/inputnumber';
import {ConfirmDialogModule} from 'primeng/confirmdialog';
import {ConfirmationService, PrimeIcons} from 'primeng/api';
import {MessageService} from 'primeng/api';
import {InputTextareaModule} from 'primeng/inputtextarea';
import {BrowserModule} from '@angular/platform-browser';
import {TagModule} from "primeng/tag";
import {TreeSelectModule} from 'primeng/treeselect';
import {StepsModule} from 'primeng/steps';
import {CheckboxModule} from 'primeng/checkbox';
import {DividerModule} from 'primeng/divider';
import { MessagesModule } from 'primeng/messages';

//services
import {DialogService, DynamicDialogModule} from 'primeng/dynamicdialog';
import { ConfigurationComponent } from './configuration/configuration.component';
import { DataManagementComponent } from './data-management/data-management.component';
import { EventManagementComponent } from './event-management/event-management.component';
import { CreateEventComponent } from './create-event/create-event.component';
import {NgOptimizedImage} from "@angular/common";

@NgModule({
    declarations: [
        AppComponent,
        WelcomeComponent,
        DrugListComponent,
        CreateDrugComponent,
        PerformInterviewComponent,
        ProbandInformationComponent,
        DrugSelectionComponent,
        IntakeInformationComponent,
        ConfirmInterviewComponent,
        ConfirmInterviewComponent,
        ConfigurationComponent,
        DataManagementComponent,
        EventManagementComponent,
        CreateEventComponent
    ],
    imports: [
        AppRoutingModule,
        CoreModule.forRoot(),
        SharedModule,
        NgbModule,
        HttpClientModule,
        ReactiveFormsModule,
        FormsModule,
        TableModule,
        BrowserAnimationsModule,
        InputTextModule,
        ButtonModule,
        TooltipModule,
        CardModule,
        BrowserModule,
        CalendarModule,
        SliderModule,
        DialogModule,
        MultiSelectModule,
        ContextMenuModule,
        DropdownModule,
        ToastModule,
        ProgressBarModule,
        FileUploadModule,
        ToolbarModule,
        RatingModule,
        RadioButtonModule,
        InputNumberModule,
        ConfirmDialogModule,
        InputTextareaModule,
        TagModule,
        TreeSelectModule,
        DialogModule,
        DynamicDialogModule,
        StepsModule,
        CalendarModule,
        CheckboxModule,
        DividerModule,
        MessagesModule,
        NgOptimizedImage
    ],
    providers: [MessageService, ConfirmationService, DialogService, PrimeIcons],
    bootstrap: [AppComponent]
})
export class AppModule {
}
