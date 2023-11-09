import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { environment } from 'src/environments/environment';
import { Event } from './event';
import { Observable, catchError, retry, throwError } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class EventService {
  apiUrl = environment.backendUrl;
  httpOptions = {
    headers: new HttpHeaders({'Content-Type': 'application/json'})
  };
  
  constructor(private http: HttpClient) { }

  getAllEvents(): Observable<Event[]> {
    return this.http
        .get<Event[]>(this.apiUrl + '/api/event')
        .pipe(retry(1), catchError(this.handleError))
  }

  addEvent(event: Event): Observable<Event> {
    return this.http
        .post<Event>(this.apiUrl + '/api/event', event)
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
