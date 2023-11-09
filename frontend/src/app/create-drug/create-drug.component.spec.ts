import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CreateDrugComponent } from './create-drug.component';

describe('CreateDrugComponent', () => {
  let component: CreateDrugComponent;
  let fixture: ComponentFixture<CreateDrugComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ CreateDrugComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(CreateDrugComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
