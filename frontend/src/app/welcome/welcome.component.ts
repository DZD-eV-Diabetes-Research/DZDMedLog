import { Component } from '@angular/core';
import { AppContent } from '../global/app-content';
import { environment } from '../../environments/environment';
import { Observable } from 'rxjs';
import { HttpClient } from '@angular/common/http';
import * as saveAs from 'file-saver';
import { AuthService } from '../core/auth/auth.service';

const date = new Date();

@Component({
  selector: 'app-welcome',
  templateUrl: './welcome.component.html',
  styleUrls: ['./welcome.component.scss']
})
export class WelcomeComponent {
  readonly AppContent = AppContent;
  readonly interviewExportUrl = environment.backendUrl + '/api/interview/export';

  constructor(private http: HttpClient, public authService: AuthService) { }

  downloadCsv() {
    this.download(this.interviewExportUrl)
        .subscribe(blob => saveAs(blob, `export-${date.getFullYear()}-${date.getMonth()+1}-${date.getDate()}.csv`))
  }

  download(url: string): Observable<Blob> {
    return this.http.get(url, {
      responseType: 'blob'
    })
  }
}
