package de.dzd.idom.intake;

import lombok.Data;

import java.time.LocalDate;

@Data
public class IntakeDTO {
    private LocalDate startDate;
    private LocalDate endDate;
    private boolean isPrescribed;
    private boolean isRegularly;
    private boolean isTakenToday;
    private String note;
    private long drugId;

    private int dosePerDay;
    private String intakeInterval;
    private String doseUnit;
}
