import { ComponentFixture, TestBed } from '@angular/core/testing';

import { IntakeInformationComponent } from './intake-information.component';

describe('IntakeInformationComponent', () => {
  let component: IntakeInformationComponent;
  let fixture: ComponentFixture<IntakeInformationComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ IntakeInformationComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(IntakeInformationComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
