import {ATC} from "./atc";
import {DosageForm} from "./dosage-form";
import {ApplicationForm} from "./application-form";
import {NormPackageSize} from "./norm-package-size";
import {Producer} from "./producer";
import { SortMeta } from "primeng/api";

export interface DrugPageRequest {
    page?: number,
    size?: number,
    globalFilter?: string,
    multiSortMeta?: SortMeta[];
    sortField?: string,
    sortOrder?: number;
}

export interface DrugPageResponse {
    content: Drug[],
    totalElements: number,
    totalPages: number,
    size: number,
    number: number;
}

export class Drug {
    id: number;
    pharmaceuticalCentralNumber: number;
    atc: ATC;
    name: string;
    dosageForm: DosageForm;
    applicationForm: ApplicationForm;
    packageSize: number;
    normPackageSize: NormPackageSize;
    producer: Producer;
    priceInCents: number;
    fixedPriceInCents: number;
    isCustom = true;
}