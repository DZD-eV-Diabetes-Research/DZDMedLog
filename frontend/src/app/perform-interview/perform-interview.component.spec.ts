import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PerformInterviewComponent } from './perform-interview.component';

describe('PerformInterviewComponent', () => {
  let component: PerformInterviewComponent;
  let fixture: ComponentFixture<PerformInterviewComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ PerformInterviewComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(PerformInterviewComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
