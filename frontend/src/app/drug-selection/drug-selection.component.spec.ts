import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DrugSelectionComponent } from './drug-selection.component';

describe('DrugSelectionComponent', () => {
  let component: DrugSelectionComponent;
  let fixture: ComponentFixture<DrugSelectionComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ DrugSelectionComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(DrugSelectionComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
