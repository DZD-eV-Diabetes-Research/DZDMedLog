import {Pipe, PipeTransform} from '@angular/core';
import {Observable, of} from 'rxjs';
import {catchError, map, startWith} from 'rxjs/operators';

export interface ObsWithStatusResult<T> {
  loading: boolean;
  payload?: T;
  error?: Error;
}

/**
 * a pipe which wraps the provided observable payload with a loading and error status.
 * based on https://medium.com/angular-in-depth/angular-show-loading-indicator-when-obs-async-is-not-yet-resolved-9d8e5497dd8
 */
@Pipe({
  name: 'obsWithStatus',
})
export class ObsWithStatusPipe implements PipeTransform {
  transform<T>(val: Observable<T>): Observable<ObsWithStatusResult<T>> {
    return val.pipe(
      map((value: T) => ({
        loading: false,
        payload: value,
      })),
      startWith({loading: true}),
      catchError(error =>
        of({
          loading: false,
          error: error,
        })
      )
    );
  }
}
