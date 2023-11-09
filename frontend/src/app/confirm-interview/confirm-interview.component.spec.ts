import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ConfirmInterviewComponent } from './confirm-interview.component';

describe('ConfirmInterviewComponent', () => {
  let component: ConfirmInterviewComponent;
  let fixture: ComponentFixture<ConfirmInterviewComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ ConfirmInterviewComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ConfirmInterviewComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
