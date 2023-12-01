package de.dzd.medlog.interview;

import de.dzd.medlog.intake.IntakeDTO;
import lombok.Data;

import java.time.LocalDateTime;
import java.util.List;

@Data
public class InterviewDTO {
    private String probandId;
    private Long eventId;
    private long interviewerNumber;
    private LocalDateTime startDate;
    private LocalDateTime endDate;
    private boolean hasTakenOtherDrugs;
    private List<IntakeDTO> intakes;
}
