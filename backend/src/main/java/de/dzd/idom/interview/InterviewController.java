package de.dzd.idom.interview;

import de.dzd.idom.intake.Intake;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/interview")
@RequiredArgsConstructor
public class InterviewController {
    private final InterviewRepository interviewRepository;
    private final InterviewMapper mapper;

    @RequestMapping("/all")
    public List<Interview> getAllInterviews() {
        return interviewRepository.findAll();
    }
    @PostMapping
    public ResponseEntity<Interview> createInterview(@RequestBody InterviewDTO interviewDTO) {
        Interview interview = mapper.convertToEntity(interviewDTO);

        // remove values if intake is not regular
        for (Intake intake : interview.getIntakes()) {
            if (!intake.getIsRegularly()) {
                intake.setDosePerDay(null);
                intake.setIntakeInterval(null);
                intake.setDoseUnit(null);
            }
        }

        return new ResponseEntity<>(
                interviewRepository.save(interview),
                HttpStatus.CREATED
        );
    }
}