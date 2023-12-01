package de.dzd.medlog.interview;

import com.fasterxml.jackson.annotation.JsonManagedReference;
import de.dzd.medlog.intake.Intake;
import de.dzd.medlog.interview.event.Event;
import jakarta.persistence.*;
import lombok.Data;

import java.time.LocalDateTime;
import java.util.List;

@Entity
@Data
public class Interview {
    @Id
    @GeneratedValue
    private long id;
    @OneToMany(mappedBy = "interview", fetch = FetchType.EAGER, cascade = CascadeType.ALL)
    @JsonManagedReference
    private List<Intake> intakes;
    @Column(nullable = false)
    private String probandId;
    @ManyToOne(fetch = FetchType.EAGER, cascade = CascadeType.ALL)
    @JsonManagedReference
    private Event event;
    @Column(nullable = false)
    private Long interviewNumber;
    @Column(nullable = false)
    private LocalDateTime startDate;
    @Column(nullable = false)
    private LocalDateTime endDate;
    @Column(nullable = false)
    private Boolean hasTakenOtherDrugs;
}
