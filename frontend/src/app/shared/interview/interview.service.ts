import { Time } from '@angular/common';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { throwError } from 'rxjs';
import { catchError, retry } from 'rxjs/operators';
import { environment } from 'src/environments/environment';
import { Intake } from './intake';
import { IntakeDTO } from './intake-dto';
import { Interview } from './interview';

@Injectable({
  providedIn: 'root'
})
export class InterviewService {
  apiURL = environment.backendUrl;
  httpOptions = {
    headers: new HttpHeaders({'Content-Type': 'application/json'})
  };

  probandId?: string;
  eventId?: number;
  interviewerNumber?: number;
  startDate?: Date;
  endDate?: Date;
  drugsTaken: boolean = false;
  intakes: Intake[] = [] as Intake[];

  constructor(private http: HttpClient) { }

  addIntake(intake: Intake) {
    this.intakes.push(intake);
  }

  private createInterview(): Interview {
    var interview = {
      probandId: this.probandId!,
      eventId: this.eventId!,
      interviewerNumber: this.interviewerNumber!,
      startDate: this.startDate!,
      endDate: this.endDate!,
      hasTakenOtherDrugs: this.drugsTaken,
      intakes: this.intakes
    };

    // conversion to IntakeDTO
    var newIntakes = [] as IntakeDTO[];
    interview.intakes.forEach(intake => {
      newIntakes.push(IntakeDTO.fromIntake(intake));
    });
    interview.intakes = newIntakes;

    return interview;
  }

  saveInterview() {
    var interview = this.createInterview();
    return this.http
      .post<Interview>(this.apiURL + '/api/interview', interview)
      .pipe(retry(0), catchError(this.handleError));
  }

  clearService() {
    this.probandId = undefined;
    this.eventId = undefined;
    this.interviewerNumber = undefined;
    this.startDate = undefined;
    this.endDate = undefined
    this.drugsTaken = false;
    this.intakes = [] as Intake[];
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
