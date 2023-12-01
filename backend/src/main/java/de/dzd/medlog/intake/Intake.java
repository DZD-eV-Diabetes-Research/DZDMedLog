package de.dzd.medlog.intake;

import com.fasterxml.jackson.annotation.JsonBackReference;
import de.dzd.medlog.drug.Drug;
import de.dzd.medlog.interview.Interview;
import jakarta.persistence.*;
import lombok.Data;

import java.time.LocalDate;

@Entity
@Data
public class Intake {
    @Id
    @GeneratedValue
    private Long id;
    @ManyToOne
    private Drug drug;
    @ManyToOne(fetch = FetchType.EAGER, cascade = CascadeType.ALL)
    @JoinColumn(name = "INTERVIEW_ID")
    @JsonBackReference
    private Interview interview;
    @Column(nullable = false)
    private LocalDate startDate;
    @Column(nullable = false)
    private LocalDate endDate;
    @Column(nullable = false)
    private Boolean isPrescribed;
    @Column(nullable = false)
    private Boolean isRegularly;
    @Column(nullable = false)
    private Boolean isTakenToday;
    private String note;

    // These three should be null if isReguarly == false
    private Integer dosePerDay;
    private String intakeInterval;
    private String doseUnit;
}
