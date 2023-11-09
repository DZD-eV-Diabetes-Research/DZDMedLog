import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ProbandInformationComponent } from './proband-information.component';

describe('ProbandInformationComponent', () => {
  let component: ProbandInformationComponent;
  let fixture: ComponentFixture<ProbandInformationComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ ProbandInformationComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ProbandInformationComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
