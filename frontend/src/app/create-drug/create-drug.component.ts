import {Component, OnInit} from '@angular/core';
import {Drug} from "../shared/drug/drug";
import {DrugService} from "../shared/drug/drug.service";
import {DynamicDialogRef} from "primeng/dynamicdialog";
import {AppContent} from '../global/app-content';
import {ApplicationForm} from "../shared/drug/application-form";
import {NormPackageSize} from "../shared/drug/norm-package-size";
import {DosageForm} from "../shared/drug/dosage-form";
import {Producer} from "../shared/drug/producer";
import {ATC} from "../shared/drug/atc";

@Component({
    selector: 'create-drug-dialog',
    templateUrl: './create-drug.component.html',
    styleUrls: ['./create-drug.component.scss']
})
export class CreateDrugComponent implements OnInit {

    readonly AppContent = AppContent;

    drugDetails: Drug;
    atcAbbreviation: string;
    producerKey: string;


    applicationForms: ApplicationForm[];
    selectedApplicationForm: ApplicationForm = new ApplicationForm();

    dosageForms: DosageForm[] = [];
    selectedDosageForm: DosageForm = new DosageForm();

    normPackageSizes: NormPackageSize[] = [];
    selectedNormPackageSize: NormPackageSize = new NormPackageSize();

    constructor(public drugService: DrugService,
                public ref: DynamicDialogRef) {
    }

    ngOnInit(): void {
        this.drugDetails = new Drug();

        // values for combo-boxes
        this.drugService.getApplicationForms().subscribe((data: ApplicationForm[]) => this.applicationForms = data);
        this.drugService.getDosageForms().subscribe((data: DosageForm[]) => this.dosageForms = data);
        this.drugService.getNormPackageSizes().subscribe((data: NormPackageSize[]) => this.normPackageSizes = data);
    }

    addDrug(): void {
        this.producerKey = this.producerKey === undefined ? '' : this.producerKey;
        let producer: Producer = {
            key: this.producerKey,
            name : this.producerKey
        }
        this.atcAbbreviation = this.atcAbbreviation === undefined ? '' : this.atcAbbreviation;
        let atc: ATC = {
            abbreviation: this.atcAbbreviation,
            agent: this.atcAbbreviation
        }
        this.drugDetails.producer = producer;
        this.drugDetails.atc = atc;
        if (this.drugDetails.pharmaceuticalCentralNumber !== undefined) {
            this.drugService.addDrug(this.drugDetails).subscribe(() => this.ref.close(true));
        }
    }

    cancelCreateDialog(): void {
        this.ref.close(false);
    }

    changeSelectedApplicationForm(applicationForm: ApplicationForm): void {
        this.drugDetails.applicationForm = applicationForm;
    }

    changeSelectedNormPackageSize(normPackageSize: NormPackageSize): void {
        this.drugDetails.normPackageSize = normPackageSize;
    }

    changeSelectedDosageForm(dosageForm: DosageForm): void {
        this.drugDetails.dosageForm = dosageForm;
    }

}
