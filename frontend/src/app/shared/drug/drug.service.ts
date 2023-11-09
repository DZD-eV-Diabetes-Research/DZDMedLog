import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, throwError } from 'rxjs';
import { catchError, retry } from 'rxjs/operators';
import { environment } from "../../../environments/environment";
import { Drug, DrugPageRequest, DrugPageResponse } from "./drug";
import {ApplicationForm} from "./application-form";
import {DosageForm} from "./dosage-form";
import {NormPackageSize} from "./norm-package-size";
import { SortMeta } from 'primeng/api';

@Injectable({
    providedIn: 'root',
})
export class DrugService {
    apiURL = environment.backendUrl;
    httpOptions = {
        headers: new HttpHeaders({'Content-Type': 'application/json'})
    };

    constructor(private http: HttpClient) { }

    getDrugs(req: DrugPageRequest): Observable<DrugPageResponse> {
        const queryParams = new URLSearchParams();

        for (const [k, v] of Object.entries(req)) {
            if (v !== undefined) {
                if (k === 'multiSortMeta') {
                    for (const {field, order} of Object.values(v as SortMeta[])) {
                        queryParams.append(k, `${field},${order}`)
                    }
                } else queryParams.set(k, v.toString());
                
            }
        }
        const requestUri = `/api/drugs?${queryParams.toString()}`;
        return this.http
            .get<DrugPageResponse>(this.apiURL + requestUri)
            .pipe(retry(1), catchError(this.handleError));
    }

    addDrug(drug: Drug): Observable<Drug> {
        return this.http
            .post<Drug>(this.apiURL + '/api/drugs', drug)
            .pipe(retry(1), catchError(this.handleError));
    }

    getApplicationForms(): Observable<ApplicationForm[]> {
        return this.http
            .get<ApplicationForm[]>(this.apiURL + '/api/application-forms')
            .pipe(retry(1), catchError(this.handleError));
    }

    getDosageForms(): Observable<DosageForm[]> {
        return this.http
            .get<DosageForm[]>(this.apiURL + '/api/dosage-forms')
            .pipe(retry(1), catchError(this.handleError));
    }

    getNormPackageSizes(): Observable<NormPackageSize[]> {
        return this.http
            .get<NormPackageSize[]>(this.apiURL + '/api/norm-package-sizes')
            .pipe(retry(1), catchError(this.handleError));
    }
    
    handleError(error: any) {
        let errorMessage = '';
        if (error.error instanceof ErrorEvent) {
            errorMessage = error.error.message;
        } else {
            errorMessage = `Error Code: ${error.status}\nMessage: ${error.message}`;
        }
        window.alert(errorMessage);
        return throwError(() => {
            return errorMessage;
        });
    }
}